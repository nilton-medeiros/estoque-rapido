# logging_config.py
import logging
from src.shared.logging.s3_logging_handler import setup_estoque_rapido_logging


# Inicializa o sistema de logging globalmente quando este módulo é importado.
# A função setup_estoque_rapido_logging() configura o logger raiz e outros.
# Módulos subsequentes podem obter loggers usando logging.getLogger(__name__).
setup_estoque_rapido_logging()

# Opcionalmente, logar que a configuração foi feita:
config_logger = logging.getLogger(__name__) # ou logging.getLogger("logging_config")
config_logger.info("Sistema de logging EstoqueRápido inicializado a partir de logging_config.py.")


"""
# Exemplo de uso (pode ser removido daqui e colocado em outro arquivo)
import logging
logger = logging.getLogger(__name__)
console_logger = logging.getLogger("console")

logger.debug("Esta mensagem é de debug e vai para o arquivo.")
logger.info("Esta mensagem é de info e vai para o arquivo.")
logger.warning("Esta mensagem é de warning e vai para o arquivo.")
logger.error("Esta mensagem é de erro e vai para o arquivo.")
logger.critical("Esta mensagem é crítica e vai para o arquivo.")

console_logger.critical("Esta mensagem não vai para o arquivo, pois é do console_logger")
>>> print("Esta mensagem é um print e vai para o console.")
"""
