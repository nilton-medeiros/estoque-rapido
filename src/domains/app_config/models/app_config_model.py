from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class AppConfig:
    """
    Representa as configurações da aplicação.

    Esta classe encapsula as configurações principais da aplicação,
    incluindo dados de conexão com chaves de API e URLs.

    Attributes:
        dfe_api_token (str): Chave de API para acesso a serviços externos.
        dfe_api_token_expires_in (str): datestamp de expiração da chave de API.
        debug (bool): Indica se o modo de depuração está ativado.
        timeout (int): Tempo limite para chamadas de API.

    Example:
        Exemplo de como instanciar e usar a classe:
        >>> app_config = AppConfig(dfe_api_token="abc123", dfe_api_token_expires_in="AbC123Key", debug=True, timeout=30)
        >>> print(app_config)
    """

    dfe_api_token: str
    dfe_api_token_expires_in: datetime
    debug: bool = False
    timeout: int = 30
    id: str | None = field(default=None)

    def __post_init__(self):
        """
        Método chamado automaticamente após a inicialização da instância da classe.

        Realiza validações adicionais dos campos 'dfe_api_token' e 'dfe_api_token_expires_in'.
        """
        # Validação do campo 'dfe_api_token'
        if not self.dfe_api_token:
            raise ValueError("O campo 'dfe_api_token' é obrigatório.")

        # Validação do campo 'dfe_api_token_expires_in'
        if not self.dfe_api_token_expires_in:
            raise ValueError("O campo 'dfe_api_token_expires_in' é obrigatório.")

        # Validação do campo 'debug'
        if not isinstance(self.debug, bool):
            raise ValueError("O campo 'debug' deve ser um valor booleano.")

        # Validação do campo 'timeout'
        if self.timeout <= 0:
            raise ValueError("O campo 'timeout' deve ser maior que zero.")
