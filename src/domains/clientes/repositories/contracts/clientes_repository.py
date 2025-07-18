from abc import ABC, abstractmethod

from src.domains.clientes.models.clientes_model import Cliente


class ClientesRepository(ABC):
    """Classe base (abstrata) que define o contrato para operações de repositório de Clientes."""
    @abstractmethod
    def get_all(self, status_deleted: bool = False) -> tuple[list[Cliente], int]:
        """Obtém todos os clientes da empresa logada pelo ID self.empresa_id."""
        raise NotImplementedError(
            "Este método deve ser implementado pela subclasse")

    @abstractmethod
    def get_by_id(self, cliente_id: str) -> Cliente | None:
        """Encontra um cliente pelo seu ID no banco de dados."""
        raise NotImplementedError(
            "Este método deve ser implementado pela subclasse")

    @abstractmethod
    def save(self, cliente: Cliente) -> str | None:
        """Cria ou atualiza um cliente no banco de dados."""
        raise NotImplementedError(
            "Este método deve ser implementado pela subclasse")

    @abstractmethod
    def get_by_name_cpf_or_phone(self, empresa_id: str, research_data: str) -> list[Cliente]:
        """
        Obtém uma lista de clientes ativos pelo nome, CPF ou telefone.

        Args:
            empresa_id (str): ID da empresa logada.
            research_data (str): Dados de pesquisa (nome, CPF ou telefone).

        Returns:
            Lista de clientes encontrados.
        """
        raise NotImplementedError(
            "Este método deve ser implementado pela subclasse")
