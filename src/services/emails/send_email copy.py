import os
import asyncio
import logging
import re
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from tenacity import retry, stop_after_attempt, wait_exponential

import aiosmtplib
from dotenv import load_dotenv
from pathlib import Path

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class EmailConfig:
    """Configuração do servidor de email - Domain Model"""
    smtp_server: str
    smtp_port: int
    username: str
    password: str
    sender_email: str
    use_tls: bool = True
    timeout: int = 30

@dataclass
class EmailMessage:
    """Modelo de domínio para mensagem de email"""
    subject: str
    recipients: List[str]
    body_text: Optional[str] = None
    body_html: Optional[str] = None
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None
    attachments: Optional[List[Path]] = None

    def __post_init__(self):
        if not self.body_text and not self.body_html:
            raise ValueError(
                "Email deve ter pelo menos body_text ou body_html")
        print("Debug  -> Entrou em EmailMessage")

class EmailValidationError(Exception):
    """Exceção customizada para erros de validação de email"""

    def __init__(self, message: str, field: Optional[str] = None):
        self.field = field
        super().__init__(message)
        print("Debug  -> Entrou em EmailValidationError")

class EmailSendError(Exception):
    """Exceção customizada para erros de envio de email"""

    def __init__(self, message: str, error_type: str = "UNKNOWN", original_error: Optional[Exception] = None):
        self.error_type = error_type
        self.original_error = original_error
        super().__init__(message)
        print("Debug  -> Entrou em EmailSendError")
        logger.error(f"error_type: {error_type}, original_error: {original_error}")

class EmailConnectionError(EmailSendError):
    """Erro de conexão com servidor SMTP"""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message, "CONNECTION_ERROR", original_error)
        print("Debug  -> Entrou em EmailConnectionError")
        logger.error(f"messessage: {message}, original_error: {original_error}")

class EmailAuthenticationError(EmailSendError):
    """Erro de autenticação no servidor SMTP"""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message, "AUTH_ERROR", original_error)
        print("Debug  -> Entrou em EmailAuthenticationError")
        logger.error(f"message: {message}, original_error: {original_error}")

class EmailRecipientError(EmailSendError):
    """Erro relacionado aos destinatários"""

    def __init__(self, message: str, invalid_emails: List[str], original_error: Optional[Exception] = None):
        self.invalid_emails = invalid_emails
        super().__init__(message, "RECIPIENT_ERROR", original_error)
        print("Debug  -> Entrou em EmailRecipientError")
        logger.error(f"message: {message}, invalid_emails: {invalid_emails}, original_error: {original_error}")

class ModernEmailSender:
    """
    Sistema moderno de envio de emails com suporte assíncrono

    Analogia: Como um sistema de correio inteligente que processa
    múltiplas cartas simultaneamente e com diferentes formatos
    """

    def __init__(self, config: EmailConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._validate_config()
        print("Debug  -> Entrou em ModernEmailSender")

    def _validate_config(self) -> None:
        """Valida a configuração do email"""
        required_fields = ['smtp_server', 'smtp_port',
                           'username', 'password', 'sender_email']
        for field in required_fields:
            if not getattr(self.config, field):
                raise EmailValidationError(
                    f"Campo obrigatório '{field}' não fornecido")

    def _validate_email_format(self, email: str) -> bool:
        """
        Valida formato de email usando regex

        Analogia: Como um inspetor que verifica se o endereço
        na carta está no formato correto
        """
        print("Debug  -> Entrou em _validate_email_format")
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        match_result = re.match(pattern, email.strip())
        return match_result is not None

    def _validate_message_size(self, message: EmailMessage) -> None:
        """Valida se o email não excede limites de tamanho"""
        total_size = len(message.subject.encode('utf-8'))
        if message.body_text:
            total_size += len(message.body_text.encode('utf-8'))
        if message.body_html:
            total_size += len(message.body_html.encode('utf-8'))

        # Limite típico de 25MB para email completo
        if total_size > 25 * 1024 * 1024:
            raise EmailValidationError("Email excede tamanho máximo permitido")


    def _create_mime_message(self, message: EmailMessage) -> MIMEMultipart:
        """Cria objeto MIME da mensagem"""
        # Usando MIMEMultipart para suportar texto, HTML e anexos
        msg = MIMEMultipart('alternative')

        # Headers básicos
        msg['Subject'] = self._normalize_text(message.subject)
        msg['From'] = self.config.sender_email
        msg['To'] = ', '.join(message.recipients)

        if message.cc:
            msg['Cc'] = ', '.join(message.cc)

        # Corpo da mensagem
        if message.body_text:
            message.body_text = self._normalize_text(message.body_text)
            msg.attach(MIMEText(message.body_text, 'plain', 'utf-8'))

        if message.body_html:
            message.body_html = self._normalize_text(message.body_html)
            msg.attach(MIMEText(message.body_html, 'html', 'utf-8'))

        # Anexos
        if message.attachments:
            self._add_attachments(msg, message.attachments)

        return msg

    def _add_attachments(self, msg: MIMEMultipart, attachments: List[Path]) -> None:
        """Adiciona anexos à mensagem"""
        for file_path in attachments:
            if not file_path.exists():
                self.logger.warning(f"Arquivo anexo não encontrado: {file_path}")
                continue

            try:
                with open(file_path, 'rb') as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())

                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {file_path.name}'
                )
                msg.attach(part)

            except Exception as e:
                self.logger.error(f"Erro ao anexar arquivo {file_path}: {e}")

    def _get_all_recipients(self, message: EmailMessage) -> List[str]:
        """Retorna todos os destinatários (to, cc, bcc)"""
        all_recipients = message.recipients.copy()

        if message.cc:
            all_recipients.extend(message.cc)

        if message.bcc:
            all_recipients.extend(message.bcc)

        return all_recipients

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def send_email_async(self, message: EmailMessage) -> Dict[str, Any]:
        """
        Envia email de forma assíncrona com tratamento robusto de erros

        Returns:
            Dict com status do envio e informações
        """
        print("Debug  -> Entrou em send_email_async")

        try:
            # Validação prévia
            print("Debug -> Antes de _validate_email_message")
            self._validate_email_message(message)
            print("Debug -> Depois de _validate_email_message, antes de _create_mime_message")

            # Cria mensagem MIME
            mime_msg = self._create_mime_message(message)
            print("Debug -> Depois de _create_mime_message, antes de _get_all_recipients")
            all_recipients = self._get_all_recipients(message)

            # Tentativa de conexão e envio
            async with aiosmtplib.SMTP(
                hostname=self.config.smtp_server,
                port=self.config.smtp_port,
                timeout=self.config.timeout
            ) as smtp_client:
                print("Debug -> Dentro do bloco async with aiosmtplib.SMTP")

                try:
                    # Conectar ao servidor
                    print("Debug -> Antes de smtp_client.connect()")
                    await smtp_client.connect()

                    if self.config.use_tls:
                        await smtp_client.starttls()

                    # Autenticar
                    await smtp_client.login(
                        self.config.username,
                        self.config.password
                    )

                    # Enviar o email
                    await smtp_client.send_message(
                        mime_msg,
                        sender=self.config.sender_email,
                        recipients=all_recipients
                    )

                    await smtp_client.quit()

                except aiosmtplib.SMTPConnectError as e:
                    raise EmailConnectionError(
                        f"Não foi possível conectar ao servidor SMTP {self.config.smtp_server}:{self.config.smtp_port}",
                        original_error=e
                    )

                except aiosmtplib.SMTPAuthenticationError as e:
                    raise EmailAuthenticationError(
                        "Falha na autenticação. Verifique usuário e senha",
                        original_error=e
                    )

                except aiosmtplib.SMTPRecipientsRefused as e:
                    # Extrair emails que foram rejeitados
                    rejected_emails = list(e.recipients.keys()) if hasattr(  # type: ignore [Stubs de tipo incompletos ou desatualizados]
                        e, 'recipients') else []
                    raise EmailRecipientError(
                        f"Destinatários rejeitados pelo servidor: {', '.join(rejected_emails)}",
                        invalid_emails=rejected_emails,
                        original_error=e
                    )

                except aiosmtplib.SMTPDataError as e:
                    error_msg = str(e)
                    if "quota" in error_msg.lower():
                        raise EmailSendError(
                            "Cota de email excedida. Tente novamente mais tarde",
                            error_type="QUOTA_EXCEEDED",
                            original_error=e
                        )
                    elif "spam" in error_msg.lower():
                        raise EmailSendError(
                            "Email rejeitado por filtro anti-spam",
                            error_type="SPAM_REJECTED",
                            original_error=e
                        )
                    else:
                        raise EmailSendError(
                            f"Erro no conteúdo do email: {error_msg}",
                            error_type="DATA_ERROR",
                            original_error=e
                        )

                except aiosmtplib.SMTPServerDisconnected as e:
                    raise EmailConnectionError(
                        "Conexão com servidor perdida durante o envio",
                        original_error=e
                    )

                except asyncio.TimeoutError as e:
                    raise EmailConnectionError(
                        f"Timeout na conexão ({self.config.timeout}s). Servidor pode estar sobrecarregado",
                        original_error=e
                    )

                except Exception as e:
                    # Captura outros erros não específicos
                    raise EmailSendError(
                        f"Erro inesperado no envio: {str(e)}",
                        error_type="UNEXPECTED_ERROR",
                        original_error=e
                    )

                self.logger.info(
                    f"Email enviado com sucesso para {len(all_recipients)} destinatários")

                return {
                    'success': True,
                    'message': 'Email enviado com sucesso',
                    'recipients_count': len(all_recipients),
                    'subject': message.subject
                }

        except EmailValidationError as e:
            self.logger.error(f"Erro de validação: {e}")
            raise

        except (EmailConnectionError, EmailAuthenticationError, EmailRecipientError, EmailSendError) as e:
            self.logger.error(f"Erro no envio de email: {e}")
            raise

        except Exception as e:
            self.logger.error(f"Erro inesperado: {e}")
            raise EmailSendError(
                f"Erro inesperado no sistema de email: {str(e)}",
                error_type="SYSTEM_ERROR",
                original_error=e
            )

    def send_email_sync(self, message: EmailMessage) -> Dict[str, Any]:
        """
        Wrapper síncrono para envio de email

        Útil quando você não está em contexto assíncrono
        """
        print("Debug  -> Entrou em send_email_sync")
        return asyncio.run(self.send_email_async(message))

    async def send_bulk_emails_async(self, messages: List[EmailMessage]) -> List[Dict[str, Any]]:
        """
        Envia múltiplos emails simultaneamente

        Analogia: Como uma máquina de franquear cartas que processa
        várias correspondências ao mesmo tempo
        """
        tasks = [self.send_email_async(msg) for msg in messages]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    'success': False,
                    'error': str(result),
                    'message_index': i
                })
            else:
                processed_results.append(result)

        return processed_results

    def _validate_email_message(self, message: EmailMessage) -> None:
        """Valida a mensagem de email com tratamento específico de erros"""
        # Validar destinatários
        if not message.recipients:
            raise EmailValidationError(
                "Lista de destinatários não pode estar vazia", field="recipients")

        # Validar formato dos emails
        invalid_emails = []
        all_emails = message.recipients.copy()
        print(f"Debug -> Validando emails: {all_emails} (recipients: {message.recipients})")

        if message.cc:
            all_emails.extend(message.cc)
        if message.bcc:
            all_emails.extend(message.bcc)

        for email in all_emails:

            print(f"Debug -> Validando email: '{email}' (tipo: {type(email)})")
            if not isinstance(email, str):
                print(f"Debug -> ERRO: Email não é string: {email}")
                # Adicionando log explícito aqui também, caso o print da exceção não apareça
                self.logger.error(f"Email com tipo inválido encontrado: {type(email)}, valor: {email}")
                raise EmailValidationError(
                    f"Endereço de email inválido (não é string): {email}",
                    field="email_format"
                )

            if not self._validate_email_format(email.strip()):
                invalid_emails.append(email)
                print(f"Debug -> Email '{email}' validado.")

        if invalid_emails:
            raise EmailValidationError(
                f"Emails com formato inválido: {', '.join(invalid_emails)}",
                field="email_format"
            )
        print("Debug -> Validação de formato de email concluída.")

        # Validar assunto
        if not message.subject or not message.subject.strip():
            raise EmailValidationError(
                "Assunto não pode estar vazio", field="subject")
        print("Debug -> Validação de assunto concluída.")
        # Validar tamanho do assunto (muitos servidores limitam)
        if len(message.subject) > 200:
            raise EmailValidationError(
                "Assunto muito longo (máximo 200 caracteres)", field="subject")
        print("Debug -> Validação de tamanho do assunto concluída.")

        # Validar corpo da mensagem
        if not message.body_text and not message.body_html:
            raise EmailValidationError(
                "Email deve ter pelo menos body_text ou body_html", field="body")

        # Validar anexos
        if message.attachments:
            total_size = 0
            for attachment in message.attachments:
                if not attachment.exists():
                    raise EmailValidationError(
                        f"Arquivo anexo não existe: {attachment}", field="attachments")

                file_size = attachment.stat().st_size
                total_size += file_size

                # Limite de 25MB por arquivo (padrão da maioria dos servidores)
                if file_size > 25 * 1024 * 1024:
                    raise EmailValidationError(
                        f"Arquivo muito grande: {attachment.name} ({file_size // (1024*1024)}MB). Máximo: 25MB",
                        field="attachments"
                    )

            # Limite total de 25MB para todos os anexos
            if total_size > 25 * 1024 * 1024:
                raise EmailValidationError(
                    f"Tamanho total dos anexos muito grande ({total_size // (1024*1024)}MB). Máximo: 25MB",
                    field="attachments"
                )
            print("Debug -> _validate_email_message concluída com sucesso.")
    def _normalize_text(self, text: str) -> str:
        return text.encode('utf-8', errors='replace').decode('utf-8')


def create_email_config_from_env() -> EmailConfig:
    """
    Factory method para criar configuração a partir do .env

    Analogia: Como um assistente que lê suas anotações (arquivo .env)
    e prepara tudo para você usar
    """
    load_dotenv()

    return EmailConfig(
        smtp_server=os.getenv('SMTP_SERVER', 'smtplw.com.br'),
        smtp_port=int(os.getenv('SMTP_PORT', '587')),
        username=os.getenv('EMAIL_USERNAME', ''),
        password=os.getenv('EMAIL_PASSWORD', '').removeprefix(
            '"').removesuffix('"'),
        sender_email=os.getenv('EMAIL_FROM', ''),
        use_tls=os.getenv('EMAIL_USE_TLS', 'true').lower() == 'true',
        timeout=int(os.getenv('EMAIL_TIMEOUT', '30'))
    )

# ---------------------------------------------------------------------------------
# Exemplo de uso
# ---------------------------------------------------------------------------------
# async def exemplo_uso():
#     """Exemplo de como usar o sistema de email moderno"""

#     # 1. Criar configuração
#     config = create_email_config_from_env()

#     # 2. Criar instância do sender
#     email_sender = ModernEmailSender(config)

#     # 3. Criar mensagem simples
#     mensagem_simples = EmailMessage(
#         subject="Teste de Email Moderno",
#         recipients=["destinatario@exemplo.com"],
#         body_text="Olá! Este é um email de teste em texto simples.",
#         body_html="""
#         <html>
#             <body>
#                 <h2>Email de Teste</h2>
#                 <p>Este é um <strong>email de teste</strong> com formatação HTML.</p>
#                 <p>Sistema moderno de envio de emails! 🚀</p>
#             </body>
#         </html>
#         """
#     )

#     # 4. Enviar email
#     try:
#         resultado = await email_sender.send_email_async(mensagem_simples)
#         print(f"Sucesso: {resultado}")
#     except EmailSendError as e:
#         print(f"Erro no envio: {e}")

# # Exemplo de uso com tratamento de erros específicos


# def exemplo_uso_com_tratamento_erros():
#     """Exemplo completo de tratamento de erros para o Estoque Rápido"""

#     config = create_email_config_from_env()
#     email_sender = ModernEmailSender(config)

#     mensagem = EmailMessage(
#         subject="🔑 Senha Temporária - Estoque Rápido",
#         recipients=["usuario@exemplo.com"],
#         body_html="""
#         <h2>Bem-vindo ao Estoque Rápido!</h2>
#         <p>Sua senha temporária é: <strong>Temp123!</strong></p>
#         <p>⚠️ Troque sua senha no primeiro login!</p>
#         """
#     )

#     try:
#         resultado = email_sender.send_email_sync(mensagem)
#         print(f"✅ Sucesso: {resultado['message']}")
#         return {"success": True, "data": resultado}

#     except EmailValidationError as e:
#         # Erros de validação - dados incorretos
#         print(f"❌ Erro de validação: {e}")
#         if e.field == "email_format":
#             return {"success": False, "error": "Email inválido", "user_message": "Verifique o email digitado"}
#         elif e.field == "subject":
#             return {"success": False, "error": "Assunto inválido", "user_message": "Erro interno, tente novamente"}
#         else:
#             return {"success": False, "error": str(e), "user_message": "Dados inválidos"}

#     except EmailAuthenticationError as e:
#         # Problema de configuração do servidor
#         print(f"🔐 Erro de autenticação: {e}")
#         return {"success": False, "error": "Erro de configuração", "user_message": "Falha temporária, tente novamente"}

#     except EmailConnectionError as e:
#         # Problema de rede/servidor
#         print(f"🌐 Erro de conexão: {e}")
#         return {"success": False, "error": "Erro de conexão", "user_message": "Servidor indisponível, tente novamente"}

#     except EmailRecipientError as e:
#         # Email do destinatário rejeitado
#         print(f"📧 Erro de destinatário: {e}")
#         return {"success": False, "error": "Email rejeitado", "user_message": f"Email inválido: {', '.join(e.invalid_emails)}"}

#     except EmailSendError as e:
#         # Outros erros de envio
#         print(f"📤 Erro de envio: {e}")

#         if e.error_type == "QUOTA_EXCEEDED":
#             return {"success": False, "error": "Cota excedida", "user_message": "Limite de emails atingido, tente mais tarde"}
#         elif e.error_type == "SPAM_REJECTED":
#             return {"success": False, "error": "Spam detectado", "user_message": "Email rejeitado, entre em contato conosco"}
#         else:
#             return {"success": False, "error": str(e), "user_message": "Falha no envio, tente novamente"}

#     except Exception as e:
#         # Qualquer outro erro não previsto
#         print(f"💥 Erro inesperado: {e}")
#         return {"success": False, "error": "Erro inesperado", "user_message": "Erro interno, entre em contato com suporte"}

# # Exemplo de uso no contexto do Estoque Rápido


# def enviar_senha_temporaria_usuario(email_usuario: str, senha_temp: str):
#     """
#     Função específica para enviar senha temporária no Estoque Rápido

#     Analogia: Como um segurança que entrega as chaves e confirma
#     que a pessoa certa recebeu
#     """

#     config = create_email_config_from_env()
#     email_sender = ModernEmailSender(config)

#     mensagem = EmailMessage(
#         subject="🔑 Sua senha temporária - Estoque Rápido",
#         recipients=[email_usuario],
#         body_html=f"""
#         <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
#             <h2 style="color: #2c3e50;">Bem-vindo ao Estoque Rápido!</h2>

#             <p>Sua conta foi criada com sucesso. Use os dados abaixo para fazer seu primeiro login:</p>

#             <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
#                 <p><strong>Email:</strong> {email_usuario}</p>
#                 <p><strong>Senha temporária:</strong> <code style="background-color: #e9ecef; padding: 4px 8px; border-radius: 4px;">{senha_temp}</code></p>
#             </div>

#             <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 8px; margin: 20px 0;">
#                 <p style="margin: 0; color: #856404;"><strong>⚠️ IMPORTANTE:</strong> Por segurança, troque sua senha no primeiro login!</p>
#             </div>

#             <p><a href="https://estoque-rapido.com/login" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Fazer Login Agora</a></p>

#             <hr style="margin: 30px 0; border: none; border-top: 1px solid #dee2e6;">
#             <p style="font-size: 12px; color: #6c757d;">Este é um email automático do sistema Estoque Rápido. Não responda este email.</p>
#         </div>
#         """
#     )

#     try:
#         resultado = email_sender.send_email_sync(mensagem)

#         # Log de sucesso para auditoria
#         print(f"Senha temporária enviada para {email_usuario}")

#         return {
#             "success": True,
#             "message": "Email enviado com sucesso",
#             "user_message": "Verifique seu email para obter a senha temporária"
#         }

#     except EmailValidationError as e:
#         if e.field == "email_format":
#             return {
#                 "success": False,
#                 "error": "invalid_email",
#                 "user_message": "Email inválido. Verifique o endereço digitado."
#             }
#         else:
#             return {
#                 "success": False,
#                 "error": "validation_error",
#                 "user_message": "Dados inválidos. Tente novamente."
#             }

#     except EmailAuthenticationError:
#         # Log do erro para administrador
#         print("Erro de autenticação no servidor de email")
#         return {
#             "success": False,
#             "error": "email_config_error",
#             "user_message": "Falha temporária no sistema. Tente novamente em alguns minutos."
#         }

#     except EmailConnectionError:
#         return {
#             "success": False,
#             "error": "connection_error",
#             "user_message": "Servidor de email indisponível. Tente novamente mais tarde."
#         }

#     except EmailRecipientError as e:
#         return {
#             "success": False,
#             "error": "recipient_rejected",
#             "user_message": f"Email rejeitado pelo servidor. Verifique se o endereço {email_usuario} está correto."
#         }

#     except EmailSendError as e:
#         if e.error_type == "QUOTA_EXCEEDED":
#             return {
#                 "success": False,
#                 "error": "quota_exceeded",
#                 "user_message": "Limite de emails atingido. Tente novamente em 1 hora."
#             }
#         elif e.error_type == "SPAM_REJECTED":
#             return {
#                 "success": False,
#                 "error": "spam_detected",
#                 "user_message": "Email rejeitado por filtro de spam. Entre em contato com suporte."
#             }
#         else:
#             return {
#                 "success": False,
#                 "error": "send_error",
#                 "user_message": "Falha no envio. Tente novamente."
#             }

#     except Exception as e:
#         # Log do erro completo para debugging
#         print(f"Erro inesperado no envio de senha temporária: {e}")
#         return {
#             "success": False,
#             "error": "unexpected_error",
#             "user_message": "Erro interno do sistema. Entre em contato com suporte."
#         }


# # Exemplo de uso síncrono (sem async/await)
# def exemplo_uso_sincrono():
#     """Exemplo para usar sem contexto assíncrono"""
#     config = create_email_config_from_env()
#     email_sender = ModernEmailSender(config)

#     mensagem = EmailMessage(
#         subject="Email Síncrono",
#         recipients=["teste@exemplo.com"],
#         body_html="<p>Email enviado de forma síncrona!</p>"
#     )

#     try:
#         resultado = email_sender.send_email_sync(mensagem)
#         print(f"Email enviado: {resultado}")
#     except EmailSendError as e:
#         print(f"Erro: {e}")


# if __name__ == "__main__":
#     # Para testar de forma assíncrona
#     asyncio.run(exemplo_uso())

#     # Ou de forma síncrona
#     # exemplo_uso_sincrono()
