# s3_logging_handler.py - VERSÃO CORRIGIDA
import logging
import boto3
import json
from datetime import datetime, timezone
from threading import Lock, Timer
from collections import deque
from botocore.client import Config
import os

class S3BufferedHandler(logging.Handler):
    """
    Handler otimizado que acumula logs em buffer e envia para S3 em lotes

    Analogia: Como um caminhão de lixo inteligente que:
    - Coleta resíduos de várias casas (buffer)
    - Vai ao aterro quando está cheio OU no horário programado
    - Tem GPS para não se perder (retry logic)
    - Tem backup se o aterro estiver fechado (fallback local)
    """

    def __init__(self,
                 bucket_name: str,
                 app_name: str,
                 s3_key_prefix: str = "logs",
                 aws_access_key_id: str | None = None,
                 aws_secret_access_key: str | None = None,
                 aws_region: str = "us-east-1",
                 buffer_size: int = 100,
                 flush_interval: int = 300,  # 5 minutos
                 max_retry_attempts: int = 3,
                 level=logging.NOTSET):

        super().__init__(level)

        self.bucket_name = bucket_name
        self.app_name = app_name
        self.s3_key_prefix = s3_key_prefix
        self.buffer_size = buffer_size
        self.flush_interval = flush_interval
        self.max_retry_attempts = max_retry_attempts

        # Buffer thread-safe para armazenar logs
        self.buffer = deque()
        self.buffer_lock = Lock()
        self.sending_threads = [] # Para rastrear threads de envio e aguardar sua conclusão

        # Estatísticas para monitoramento
        self.stats = {
            'logs_buffered': 0,
            'logs_sent': 0,
            'batches_sent': 0,
            'errors': 0,
            'last_flush': None
        }

        # Cliente S3 com configuração otimizada
        session = boto3.Session(
            aws_access_key_id=aws_access_key_id or os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=aws_secret_access_key or os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_DEFAULT_REGION') or aws_region
        )

        self.s3_client = session.client(
            's3',
            config=Config(
                retries={'max_attempts': 2, 'mode': 'adaptive'},
                max_pool_connections=10
            )
        )

        # Informações da sessão
        self.session_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        self.instance_id = os.getenv('RENDER_INSTANCE_ID', 'local')[:8]

        # Timer para flush automático
        self.timer = None
        self._setup_auto_flush()

        # Flag para indicar se está sendo fechado
        self._closing = False

    def emit(self, record):
        """Adiciona log ao buffer de forma thread-safe"""
        if self._closing:
            return

        try:
            # Formata a mensagem com informações extras para Estoque Rápido
            log_entry = {
                'timestamp': datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
                'level': record.levelname,
                'logger': record.name,
                'message': self.format(record),
                'module': getattr(record, 'module', ''),
                'function': getattr(record, 'funcName', ''),
                'line': getattr(record, 'lineno', 0),
                'thread_name': getattr(record, 'threadName', ''),
                'process_id': os.getpid(),
                'session_id': self.session_id,
                'instance_id': self.instance_id,
                # Informações extras se disponíveis
                'pathname': getattr(record, 'pathname', ''),
                'exc_info': self.format(record) if record.exc_info else None
            }

            with self.buffer_lock:
                self.buffer.append(log_entry)
                self.stats['logs_buffered'] += 1

                # Flush automático se buffer estiver cheio
                if len(self.buffer) >= self.buffer_size:
                    self._flush_buffer_internal()

        except Exception as e:
            self.stats['errors'] += 1
            self.handleError(record)

    def _flush_buffer_internal(self):
        """Flush interno (já dentro do lock)"""
        if not self.buffer or self._closing:
            return

        try:
            # Prepara o lote para envio
            logs_to_send = list(self.buffer)
            self.buffer.clear()

            # Envia em thread separada para não bloquear
            from threading import Thread # Importa aqui para evitar dependência circular se Thread for usado em outras partes
            thread = Thread(target=self._send_to_s3, args=(logs_to_send,))
            thread.daemon = True
            self.sending_threads.append(thread) # Adiciona à lista antes de iniciar
            thread.start()

        except Exception as e:
            self.stats['errors'] += 1
            print(f"Erro no flush interno: {e}")

    def _send_to_s3(self, logs_to_send):
        """Envia logs para S3 com retry logic"""
        if not logs_to_send:
            return

        for attempt in range(self.max_retry_attempts):
            try:
                # Cria o nome do arquivo com informações detalhadas
                timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")[:-3]

                # O log será salvo na estrutura: estoquerapido/ > logs/ > 202506/
                # Para logs > YYYY > MM > DD/ Use: f"{datetime.now(timezone.utc).strftime('%Y/%m/%d')}/" para separar Ano, mês e dia em pastas diferentes
                s3_key = (f"{self.s3_key_prefix}/"
                         f"{datetime.now(timezone.utc).strftime('%Y%m')}/"
                         f"estoque_rapido_{self.instance_id}_{timestamp}.jsonl")

                # Prepara o conteúdo (JSON Lines format para eficiência)
                log_lines = []
                for log_entry in logs_to_send:
                    log_lines.append(json.dumps(log_entry, ensure_ascii=False, separators=(',', ':')))

                content = '\n'.join(log_lines)

                # Metadados do arquivo
                metadata = {
                    'session_id': self.session_id,
                    'instance_id': self.instance_id,
                    'log_count': str(len(logs_to_send)),
                    'app_name': self.app_name,
                    'environment': 'production' if os.getenv('RENDER') else 'development'
                }

                # Upload para S3
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=s3_key,
                    Body=content.encode('utf-8'),
                    ContentType='application/x-jsonlines',
                    Metadata=metadata
                )

                # Atualiza estatísticas
                self.stats['logs_sent'] += len(logs_to_send)
                self.stats['batches_sent'] += 1
                self.stats['last_flush'] = datetime.now(timezone.utc).isoformat()

                print(f"📤 Logs enviados para S3: {len(logs_to_send)} entradas -> {s3_key}")
                return  # Sucesso, sai do loop de retry

            except Exception as e:
                self.stats['errors'] += 1
                if attempt < self.max_retry_attempts - 1:
                    wait_time = (2 ** attempt) * 1  # Backoff exponencial: 1s, 2s, 4s
                    print(f"❌ Erro ao enviar logs (tentativa {attempt + 1}): {e}")
                    print(f"   Tentando novamente em {wait_time}s...")
                    import time
                    time.sleep(wait_time)
                else:
                    print(f"❌ Falha definitiva ao enviar logs após {self.max_retry_attempts} tentativas: {e}")
                    # TODO: Implementar fallback local se necessário

    def _setup_auto_flush(self):
        """Configura o timer para flush automático"""
        def auto_flush():
            if not self._closing and self.buffer:
                with self.buffer_lock:
                    self._flush_buffer_internal()

            # Reagenda o próximo flush
            if not self._closing:
                self.timer = Timer(self.flush_interval, auto_flush)
                self.timer.daemon = True
                self.timer.start()

        self.timer = Timer(self.flush_interval, auto_flush)
        self.timer.daemon = True
        self.timer.start()

    def flush(self):
        """Força o envio de todos os logs do buffer"""
        with self.buffer_lock:
            self._flush_buffer_internal()

        # Aguarda um pouco para permitir que a thread termine
        import time
        time.sleep(1)

    def close(self):
        """Finaliza o handler enviando logs restantes"""
        self._closing = True

        if self.timer:
            self.timer.cancel()

        # Flush final
        self.flush()

        # Aguarda todas as threads de envio concluírem
        for thread in list(self.sending_threads): # Itera sobre uma cópia, pois a lista pode ser modificada
            if thread.is_alive():
                try:
                    thread.join(timeout=5) # Espera até 5 segundos para cada thread
                except RuntimeError: # A thread pode já ter terminado
                    pass
            with self.buffer_lock: # Adquire o lock para remover com segurança da lista compartilhada
                if thread in self.sending_threads:
                    self.sending_threads.remove(thread)

        final_logger = logging.getLogger(__name__)
        # Log das estatísticas finais
        final_logger.info("📊 Estatísticas do S3Handler:")
        final_logger.info(f"   Logs processados: {self.stats['logs_buffered']}")
        final_logger.info(f"   Logs enviados: {self.stats['logs_sent']}")
        final_logger.info(f"   Lotes enviados: {self.stats['batches_sent']}")
        final_logger.info(f"   Erros: {self.stats['errors']}")
        super().close()

    def get_stats(self):
        """Retorna estatísticas do handler"""
        return self.stats.copy()


class EstoqueRapidoLogConfig:
    """
    Configuração de logging híbrida otimizada para Estoque Rápido

    Analogia: Como ter um caderno de rascunho (local) e um arquivo definitivo (S3)
    - Desenvolvimento: arquivo local para debug rápido
    - Produção: S3 com buffer inteligente para eficiência
    """

    def __init__(self,
                 log_level=None,  # Auto-detecta baseado no ambiente
                 use_s3=None,     # Auto-detecta baseado no ambiente
                 bucket_name=None,
                 app_name=None):

        # Auto-detecção do ambiente
        self.is_production = os.getenv('RENDER', '').lower() == 'true'

        # Configurações inteligentes baseadas no ambiente
        if log_level is None:
            log_level = logging.INFO if self.is_production else logging.DEBUG

        if use_s3 is None:
            use_s3 = self.is_production

        if bucket_name is None:
            bucket_name = os.getenv('AWS_S3_BUCKET_NAME')

        if app_name is None:
            app_name = os.getenv('AWS_S3_APP_NAME')

        self.use_s3 = use_s3 and bucket_name
        self.s3_handler = None

        # Formatter otimizado para Estoque Rápido
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - [%(levelname)s] - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Limpa handlers existentes para evitar duplicação
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        root_logger.setLevel(logging.DEBUG)

        # Handler para arquivo local (desenvolvimento)
        if not self.is_production:
            self._setup_local_handler(root_logger, formatter, log_level)

        # Handler para S3 (produção)
        if self.use_s3:
            self._setup_s3_handler(root_logger, formatter, bucket_name, app_name, log_level)

        # Handler para console (sempre presente)
        self._setup_console_handler(root_logger, formatter)

        # Configurações específicas para bibliotecas externas
        self._setup_third_party_loggers()

        # Configurar graceful shutdown
        self._setup_graceful_shutdown()

        # Log de inicialização
        logger = logging.getLogger(__name__)
        environment = "PRODUÇÃO (Render)" if self.is_production else "DESENVOLVIMENTO"
        logger.info(f"Sistema de logging inicializado - Ambiente: {environment}")
        if self.use_s3:
            logger.info(f"Logs sendo enviados para S3: {bucket_name}")

    def _setup_local_handler(self, root_logger, formatter, log_level):
        """Configura handler para arquivo local (desenvolvimento)"""
        from logging.handlers import RotatingFileHandler

        try:
            # CORREÇÃO: Import seguro do find_project_root
            try:
                from src.shared.utils.find_project_path import find_project_root
                project_root = find_project_root(__file__)
            except ImportError:
                # Fallback se não encontrar o módulo
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

            log_dir = os.path.join(project_root, 'logs')
            os.makedirs(log_dir, exist_ok=True)

            log_file = os.path.join(log_dir, "estoque_rapido.log")

            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=10485760,  # 10MB
                backupCount=10,     # Manter 10 arquivos de backup
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            file_handler.setLevel(log_level)
            root_logger.addHandler(file_handler)

            print(f"✓ Log local configurado: {log_file}")

        except Exception as e:
            print(f"✗ Erro ao configurar handler local: {e}")

    def _setup_s3_handler(self, root_logger, formatter, bucket_name, app_name, log_level):
        """Configura handler para S3 com buffer otimizado"""
        try:
            # Torna o buffer e o intervalo configuráveis via variáveis de ambiente
            buffer_size = int(os.getenv('AWS_S3_LOG_BUFFER_SIZE', '200'))
            flush_interval = int(os.getenv('AWS_S3_LOG_FLUSH_INTERVAL', '600')) # 10 minutos

            self.s3_handler = S3BufferedHandler(
                bucket_name=bucket_name,
                app_name=app_name,
                s3_key_prefix=f"{app_name}/logs",
                # buffer_size=100,     # Buffer maior para produção
                # flush_interval=300,  # 5 minutos
                buffer_size=buffer_size,
                flush_interval=flush_interval,
                level=log_level
            )
            self.s3_handler.setFormatter(formatter)
            root_logger.addHandler(self.s3_handler)

            print(f"✓ Log S3 configurado: {bucket_name}/{app_name}/logs/")

        except Exception as e:
            print(f"✗ Erro ao configurar handler S3: {e}")
            self.s3_handler = None

    def _setup_console_handler(self, root_logger, formatter):
        """Configura handler para console"""
        import sys
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)

        # No desenvolvimento: tudo no console
        # Na produção: apenas WARNING e acima
        console_level = logging.DEBUG if not self.is_production else logging.WARNING
        console_handler.setLevel(console_level)

        root_logger.addHandler(console_handler)

    def _setup_third_party_loggers(self):
        """Configura loggers de bibliotecas externas"""
        # Configurações específicas para diferentes bibliotecas
        logger_configs = {
            "uvicorn": logging.INFO,
            "uvicorn.access": logging.WARNING,  # Reduz ruído de acesso
            "uvicorn.error": logging.ERROR,
            "websockets": logging.WARNING,      # Reduz ruído de websockets
            "boto3": logging.WARNING,           # AWS SDK
            "botocore": logging.WARNING,        # AWS Core
            "flet": logging.INFO,               # Flet framework
            "flet_core": logging.WARNING,       # Flet core components
            # Ajuste específico para flet_web.fastapi
            # Em produção, queremos menos verbosidade, focando em warnings/errors.
            # Em desenvolvimento, INFO pode ser útil para entender o fluxo.
            "flet_web.fastapi": logging.WARNING if self.is_production else logging.INFO,
        }

        for logger_name, level in logger_configs.items():
            logger = logging.getLogger(logger_name)
            logger.setLevel(level)
            # Garante que os handlers configurados no root logger sejam utilizados,
            # a menos que um handler específico seja adicionado a este logger.
            # No seu caso, como você limpa e adiciona handlers ao root, True é o ideal.
            logger.propagate = True

    def _setup_graceful_shutdown(self):
        """Configura shutdown gracioso para garantir envio dos logs"""
        import atexit
        import signal
        import sys

        def cleanup():
            if self.s3_handler:
                print("Enviando logs finais para S3...")
                self.s3_handler.flush()
                self.s3_handler.close()

        # Registra cleanup para diferentes cenários de shutdown
        atexit.register(cleanup)

        def signal_handler(signum, frame):
            print(f"Recebido sinal {signum}, fazendo cleanup...")
            cleanup()
            sys.exit(0)

        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)


# ===== FUNÇÃO PRINCIPAL PARA USAR NO SEU PROJETO =====
def setup_estoque_rapido_logging():
    """
    Função para inicializar o sistema de logging do Estoque Rápido

    Uso:
    - Desenvolvimento: arquivo local + console detalhado
    - Produção: S3 com buffer + console resumido

    Returns:
        logging.Logger: Logger configurado e pronto para uso
    """

    # Verifica se as variáveis necessárias estão configuradas
    if os.getenv('RENDER') and not os.getenv('AWS_S3_BUCKET_NAME'):
        print("⚠️  AVISO: Rodando no Render mas AWS_S3_BUCKET_NAME não configurado!")
        print("   Configure as variáveis de ambiente para logging em S3")

    # Inicializa a configuração
    log_config = EstoqueRapidoLogConfig()

    # Retorna um logger pronto para uso
    return logging.getLogger("estoque_rapido")


# ===== FUNÇÕES AUXILIARES PARA PÁGINA DE ADMINISTRAÇÃO =====
def get_s3_logging_stats():
    """
    Retorna estatísticas do sistema de logging S3

    Returns:
        dict: Estatísticas atuais do handler S3
    """
    root_logger = logging.getLogger()

    for handler in root_logger.handlers:
        if isinstance(handler, S3BufferedHandler):
            stats = handler.get_stats()
            stats['buffer_current_size'] = len(handler.buffer)
            stats['buffer_max_size'] = handler.buffer_size
            stats['flush_interval'] = handler.flush_interval
            return stats

    return {'error': 'S3Handler não encontrado'}


def force_s3_logging_flush():
    """
    Força o flush imediato de todos os logs para S3

    Returns:
        dict: Resultado da operação
    """
    root_logger = logging.getLogger()

    for handler in root_logger.handlers:
        if isinstance(handler, S3BufferedHandler):
            try:
                handler.flush()
                return {'success': True, 'message': 'Flush executado com sucesso'}
            except Exception as e:
                return {'success': False, 'error': str(e)}

    return {'success': False, 'error': 'S3Handler não encontrado'}
