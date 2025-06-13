from src.domains.app_config.models.app_config_model import AppConfig
from src.domains.app_config.repositories.contracts.app_config_repository import AppConfigRepository
from src.shared.utils import get_uuid



"""
Essa estrutura garante uma separação clara de responsabilidades, onde a AppConfigService atua como intermediária,
organizando e validando os dados antes de delegar a execução das operações ao repositório de dados.
Isso promove uma arquitetura mais limpa e modular, facilitando manutenção e escalabilidade do sistema.
"""


class AppConfigServices:
    """Seriço de gerenciamento de Configuração de Sistema.

    A classe AppConfigService é um serviço dedicado ao gerenciamento de app config,
    facilitando a interação entre a aplicação e o banco de dados.
    Ela possui métodos específicos para criação, atualização e busca de configurações,
    delegando essas operações ao repositório de dados.

    Args: repository (AppConfigRepository): Repositório app_config do database selecionado em app_config_controller.

    Attributes:
        repository (AppConfigRepository): Repositório app_config.

    Example:
        Exemplo de como instanciar e usar a classe:
        >>> repository = FirebaseAppConfigRepository()
        >>> config_service = AppConfigService(repository)
    """

    def __init__(self, repository: AppConfigRepository):
        self.repository = repository

    # def create_config(self, config: AppConfig):
    #     """Envia os dados da nova configuração para o repositório criar.

    #     Este método é responsável por enviar os dados da nova configuração para o repositório,
    #     que, por sua vez, cria uma nova entrada na entidade app_config do banco de dados.

    #     Args:
    #         config (AppConfig): Instância da Configuração do sistema a ser criada.

    #     Returns:
    #         ID do documento da Configuração do sistema criada

    #     Raises:
    #         ValueError: Descrição da exceção que pode ser lançada, se aplicável.

    #     Exemplo:
    #         >>> repository = FirebaseAppConfigRepository()
    #         >>> config_service = AppConfigService(repository)
    #         >>> config_id = config_service.create_config(config)
    #     """

    #     existing_config = self.repository.find_by_id(config.id)

    #     if existing_config:
    #         raise ValueError("Já existe uma configuração com este ID")

    #     # Envia para o repositório selecionado em config_controllrer salvar
    #     return self.repository.save(config)


    def create(self, config: AppConfig) -> str:
        # Gera por padrão um uuid raw (sem os hífens) com prefixo 'app_'
        config.id = 'app_' + get_uuid()
       # Envia para o repositório selecionado em app_config_controllrer salvar
        return self.repository.save(config)


    def update(self, config: AppConfig) -> str:
        """Atualiza os dados de uma configuração existente.

        Este método atualiza os dados de uma configuração existente. Ele envia as informações
        atualizadas para o repositório, que localiza a configuração pelo ID na entidade app_config e
        realiza as modificações necessárias.

        Args:
            config (AppConfig): Instância da AppConfig a ser criada.

        Returns:
            ID do documento da AppConfig alterada

        Raises:
            ValueError: Descrição da exceção que pode ser lançada, se aplicável.

        Exemplo:
            >>> repository = FirebaseAppConfigRepository()
            >>> config_service = AppConfigService(repository)
            >>> config_id = config_service.update_config(config)
        """

        if not config.id:
            raise ValueError(
                "ID da configuração é necessário para atualização")
        return self.repository.save(config)

    def find_config_by_id(self, id: str) -> AppConfig|None:
        """Busca uma configuração no banco de dados utilizando o ID.

        Este método busca uma configuração no banco de dados utilizando o ID fornecido.
        Ele solicita ao repositório que encontre a configuração correspondente na entidade app_config.

        Args:
            id (str): ID da configuração a ser encontrada

        Returns:
            Optional[AppConfig]: Configuração encontrada ou None se não existir
        """
        return self.repository.get(id)
