from abc import ABC, abstractmethod

from src.domains.pedidos.models.pedidos_model import Pedido
from src.domains.shared.models.registration_status import RegistrationStatus


class PedidosRepository(ABC):
    """Classe base abstrata que define o contrato para operações de repositório de pedidos."""

    @abstractmethod
    def get_next_pedido_number(self, empresa_id: str) -> str:
        """
        Obtém o próximo número sequencial para um pedido da empresa e o incrementa.
        Usa uma transação do Firestore para garantir a atomicidade.
        """
        raise NotImplementedError(
        "Este método deve ser implementado pela subclasse")


    @abstractmethod
    def save_pedido(self, pedido: Pedido) -> Pedido | None:
        """Adiciona um novo pedido ao Firestore."""
        raise NotImplementedError(
        "Este método deve ser implementado pela subclasse")


    @abstractmethod
    def get_pedido_by_id(self, pedido_id: str) -> Pedido | None:
        """Busca um pedido pelo seu ID."""
        raise NotImplementedError(
        "Este método deve ser implementado pela subclasse")


    @abstractmethod
    def get_pedidos_by_empresa_id(self, empresa_id: str, status: RegistrationStatus | None = None) -> tuple[list[Pedido], int]:
        """Busca todos os pedidos de uma empresa, opcionalmente filtrando por status."""
        raise NotImplementedError(
        "Este método deve ser implementado pela subclasse")


    # @abstractmethod
    # def update_pedido(self, pedido: Pedido) -> Pedido:
    #     """Atualiza um pedido existente no Firestore."""
    #     raise NotImplementedError(
    #     "Este método deve ser implementado pela subclasse")


    @abstractmethod
    def delete_pedido(self, pedido: Pedido) -> bool:
        """Realiza um soft delete em um pedido, definindo deleted_at."""
        raise NotImplementedError(
        "Este método deve ser implementado pela subclasse")


    @abstractmethod
    def hard_delete_pedido(self, pedido_id: str) -> bool:
        """Remove um pedido completamente do Firestore (uso cauteloso)."""
        raise NotImplementedError(
        "Este método deve ser implementado pela subclasse")


    @abstractmethod
    def restore_pedido(self, pedido: Pedido) -> bool:
        """Restaura um pedido da lixeira."""
        raise NotImplementedError(
        "Este método deve ser implementado pela subclasse")
