from src.domains.pedidos.models.pedidos_model import Pedido
from src.domains.pedidos.models.pedidos_subclass import OrderStatus
from src.domains.pedidos.repositories.contracts.pedidos_repository import PedidosRepository
from src.shared.utils.gen_uuid import get_uuid


class PedidosServices:
    def __init__(self, repository: PedidosRepository):
        self.repository = repository

    def create_pedido(self, pedido: Pedido, usuario_logado: dict) -> str | None:
        """
        Envia dados do Pedido para o repositorio do database instânciado em pedidos_controllers

        Args:
            pedido (Pedido): Instância de Pedido para criação

        Returns:
            pedido_id (str): ID do pedido criado
        """
        if pedido.order_number:
            raise ValueError(
                "Este pedido já tem um número de pedido atribuído.")

        # Gera por padrão um uuid raw (sem os hífens) com prefixo 'ped_'
        pedido.id = 'ped_' + get_uuid()

        # Atribuição de created_at, updated_at será feita pelo repositório do database om o tipo TIMESTAMP do db
        pedido.created_at = None
        pedido.created_by_id = usuario_logado["id"]
        pedido.created_by_name = usuario_logado["name"].nome_completo

        return self.repository.save_pedido(pedido)

    def update_pedido(self, pedido: Pedido, usuario_logado: dict) -> str | None:
        """
        Envia dados do Pedido para o repositorio do database instânciado em pedidos_controllers

        Args:
            pedido (Pedido): Instância de Pedido para alterar

        Returns:
            pedido_id (str): ID do pedido alterado
        """
        if not pedido.id:
            raise ValueError("ID do pedido é necessário para atualização.")
        if not pedido.order_number:
            raise ValueError("Número do pedido é necessário para atualização.")

        pedido.updated_by_id = usuario_logado["id"]
        pedido.updated_by_name = usuario_logado["name"].nome_completo

        return self.repository.save_pedido(pedido)

    def get_pedido_by_id(self, pedido_id: str) -> Pedido | None:
        """
        Busca um pedido pelo seu ID.

        Args:
            pedido_id (str): ID do pedido a ser buscado

        Returns:
            pedido (Pedido): Instância de Pedido encontrada ou None se não existir
        """
        return self.repository.get_pedido_by_id(pedido_id)

    def get_pedidos_by_empresa_id(self, empresa_id: str, status: OrderStatus | None = None) -> list[Pedido]:
        """
        Busca todos os pedidos de uma empresa.

        Args:
            empresa_id (str): ID da empresa a ser buscada
            status (OrderStatus | None, optional): Se passado, filtra os pedidos pelo seu status

        Returns:
            pedidos (list[Pedido]): Lista de Instâncias de Pedido encontradas ou vazia se não existir
        """
        return self.repository.get_pedidos_by_empresa_id(empresa_id, status)

    def delete_pedido(self, pedido: Pedido, usuario_logado: dict) -> bool:
        """
        Realiza um soft delete em um pedido, definindo deleted_at.

        Args:
            pedido_id (str): ID do pedido a ser deletado.

        Returns:
            bool: True se o pedido for deletado com sucesso, False caso contrário.
        """
        if pedido.status == OrderStatus.DELIVERED:
            raise ValueError("Não é possível deletar um pedido já entregue.")

        pedido.deleted_by_id = usuario_logado["id"]
        pedido.deleted_by_name = usuario_logado["name"].nome_completo

        return self.repository.delete_pedido(pedido)
