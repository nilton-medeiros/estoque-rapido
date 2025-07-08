from src.domains.clientes.models.clientes_model import Cliente
from src.domains.clientes.repositories.contracts.clientes_repository import ClientesRepository
from src.domains.shared.models.nome_pessoa import NomePessoa
from src.domains.shared.models.registration_status import RegistrationStatus
from src.shared.utils.gen_uuid import get_uuid


class ClientesServices:
    def __init__(self, repository: ClientesRepository) -> None:
        """
        Serviço de gerenciamento de clientes.

        Args:
            repository (ClientesRepository): Repositório de clientes.

        Returns: None
        """
        self.repository = repository


    def create(self, cliente: Cliente, usuario_logado: dict) -> str | None:
        """
        Cria um novo cliente no repositório de clientes.

        Args:
            cliente (Cliente): Objeto Cliente contendo os dados do cliente a ser criado.
            usuario_logado (dict): Dicionário contendo informações do usuário logado.

        Returns:
            (str | None): ID do cliente criado ou None em caso de erro.
        """
        if not usuario_logado.get("id"):
            raise ValueError("ID do usuário é necesário")

        # Gera por padrão um uuid raw (sem os hifens) com prefixo 'cli_'
        cliente.id = "cli_" + get_uuid()

        # Atribuição de created_at, updated_at será feita pelo repositório do banco de dados com o tipo TIMESTAMP do database
        cliente.created_at = None # Garante None para ser atribuido pelo banco um SERVER_TIMESTAMP
        cliente.created_by_id = usuario_logado["id"]
        user_name: NomePessoa = usuario_logado["name"]
        cliente.created_by_name = user_name.nome_completo  # Desnormalização para otimizar indices no banco de dados

        # Envia para o repositório selecionado em clientes_controllrer salvar
        return self.repository.save(cliente)


    def update(self, cliente: Cliente, usuario_logado: dict) -> str | None:
        """
        Atualiza os dados de uma cliente existente.

        Args:
            cliente (Cliente): Objeto Cliente contendo os dados do cliente a ser alterado.
            usuario_logado (dict): Dicionário contendo informações do usuário logado.

        Returns:
            (str | None): ID do cliente alteado ou None em caso de erro.
        """
        if not cliente.id:
            raise ValueError("ID do cliente é necessário")
        if not usuario_logado.get("id"):
            raise ValueError("ID do usuário é necessário")

        # Atribuição de created_at, updated_at será feita pelo repositório do banco de dados com o tipo TIMESTAMP do database
        cliente.updated_by_id = usuario_logado["id"]
        user_name: NomePessoa = usuario_logado["name"]
        cliente.updated_by_name = user_name.nome_completo  # Desnormalização para otimizar indices no banco de dados

        # Envia para o repositório selecionado em clientes_controllrer salvar
        return self.repository.save(cliente)


    def get_by_id(self, cliente_id: str) -> Cliente | None:
        """Obtém um cliente pelo seu ID."""
        return self.repository.get_by_id(cliente_id)


    # def get_all(self, status_deleted: bool = False) -> tuple[list[Cliente], int]:
    #     """
    #     Obtém todos os clientes da empresa logada.

    #     Args:
    #         status_deleted (bool): Se True, retorna apenas clientes deletados.

    #     Returns:
    #         list[Cliente]: Lista de clientes.
    #         int: Número total de clientes marcados como "DELETED".
    #     """
    #     return self.repository.get_all(status_deleted=status_deleted)


    def update_status(self, cliente: Cliente, logged_user: dict, status: RegistrationStatus) -> bool:
        """Atualiza o status de uma cliente existente"""
        user_name: NomePessoa = logged_user["name"]
        previous_status = cliente.status
        cliente.status = status

        match status:
            case RegistrationStatus.ACTIVE:
                cliente.activated_at = None # Remove o datetime, será atribuido pelo SDK do banco TIMESTAMP
                cliente.activated_by_id = logged_user["id"]
                cliente.activated_by_name = user_name.nome_completo  # Desnormalização p/ otimização de índices no db
            case RegistrationStatus.INACTIVE:
                cliente.inactivated_at = None # Remove o datetime, será atribuido pelo SDK do banco TIMESTAMP
                cliente.inactivated_by_id = logged_user["id"]
                cliente.inactivated_by_name = user_name.nome_completo  # Desnormalização p/ otimização de índices no db
            case RegistrationStatus.DELETED:
                cliente.deleted_at = None # Remove o datetime, será atribuido pelo SDK do banco TIMESTAMP
                cliente.deleted_by_id = logged_user["id"]
                cliente.deleted_by_name = user_name.nome_completo  # Desnormalização p/ otimização de índices no db

        id = self.repository.save(cliente)
        if not id:
            # Status não foi alterado, retorna o status anterior ao objeto
            cliente.status = previous_status
        return id is not None
