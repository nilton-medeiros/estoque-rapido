from src.domains.pedidos.models.pedidos_model import Pedido
from src.domains.pedidos.models.pedidos_subclass import OrderStatus
from src.domains.pedidos.repositories.implementations.firebase_pedidos_repository import FirebasePedidosRepository
from src.domains.pedidos.services.pedidos_services import PedidosServices


def handle_save_pedido(pedido: Pedido, usuario_logado: dict) -> dict:
    """Cria ou atualiza um pedido."""
    response = {}
    try:
        repository = FirebasePedidosRepository()
        services = PedidosServices(repository)

        if not pedido:
            raise ValueError("Pedido é necessário para salvar.")
        if not usuario_logado:
            raise ValueError("Usuário logado é necessário para salvar pedido.")

        operation = "atualizado"

        if pedido.id:
            pedido_id = services.update_pedido(pedido, usuario_logado)
        else:
            pedido_id = services.create_pedido(pedido, usuario_logado)
            operation = "criado"

        response["status"] = "success"
        response["data"] = pedido_id
        response["message"] = f"Pedido {operation} com sucesso."
    except ValueError as e:
        response["status"] = "error"
        response["message"] = str(e)
    except Exception as e:
        response["status"] = "error"
        response[
            "message"] = f"Erro ao {"criar" if operation == "criado" else "atualizar"} pedido: {str(e)}"

    return response


def handle_get_pedido_by_id(pedido_id: str) -> dict:
    """Busca um pedido pelo seu ID."""
    response = {}
    try:
        if not pedido_id:
            raise ValueError("ID do pedido é necessário para busca.")

        repository = FirebasePedidosRepository()
        services = PedidosServices(repository)

        pedido = services.get_pedido_by_id(pedido_id)

        if pedido:
            response["status"] = "success"
            response["data"] = pedido
        else:
            response["status"] = "error"
            response["message"] = "Pedido não encontrado."
    except ValueError as e:
        response["status"] = "error"
        response["message"] = str(e)
    except Exception as e:
        response["status"] = "error"
        response["message"] = f"Erro ao buscar pedido: {str(e)}"

    return response


def handle_get_pedidos_by_empresa_id(empresa_id: str, status: OrderStatus | None = None) -> dict:
    """Busca todos os pedidos de uma empresa."""
    response = {}
    try:
        if not empresa_id:
            raise ValueError("ID da empresa é necessário para busca.")

        repository = FirebasePedidosRepository()
        services = PedidosServices(repository)

        pedidos = services.get_pedidos_by_empresa_id(empresa_id, status)

        response["status"] = "success"
        response["data"] = pedidos
    except ValueError as e:
        response["status"] = "error"
        response["message"] = str(e)
    except Exception as e:
        response["status"] = "error"
        response["message"] = f"Erro ao buscar pedido: {str(e)}"

    return response


def handle_delete_pedido(pedido: Pedido, usuario_logado: dict) -> dict:
    """Realiza um soft delete em um pedido, definindo deleted_at."""
    response = {}
    try:
        if not pedido.id:
            raise ValueError("ID do pedido é necessário para deleção.")
        if not usuario_logado:
            raise ValueError("Usuário logado é necessário para deleção.")

        repository = FirebasePedidosRepository()
        services = PedidosServices(repository)

        is_deleted = services.delete_pedido(pedido, usuario_logado)

        if is_deleted:
            response["status"] = "success"
            response["message"] = "Pedido deletado com sucesso."
        else:
            response["status"] = "error"
            response["message"] = "Erro ao deletar pedido."
    except ValueError as e:
        response["status"] = "error"
        response["message"] = str(e)
    except Exception as e:
        response["status"] = "error"
        response["message"] = f"Erro ao buscar pedido: {str(e)}"

    return response
