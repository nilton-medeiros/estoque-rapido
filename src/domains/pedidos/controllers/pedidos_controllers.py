from src.domains.pedidos.models.pedidos_model import Pedido
from src.domains.pedidos.repositories.implementations.firebase_pedidos_repository import FirebasePedidosRepository
from src.domains.pedidos.services.pedidos_services import PedidosServices
from src.domains.shared.models.registration_status import RegistrationStatus
from src.domains.usuarios.models.usuarios_model import Usuario


def handle_save_pedido(pedido: Pedido, current_user: Usuario) -> dict:
    """Cria ou atualiza um pedido."""
    response = {}
    operation = "atualizado"  # Inicializa a variável fora do try
    try:
        repository = FirebasePedidosRepository()
        services = PedidosServices(repository)

        if not pedido:
            raise ValueError("Pedido é necessário para salvar.")
        if not current_user:
            raise ValueError("Usuário logado é necessário para salvar pedido.")

        if pedido.id:
            pedido_obj = services.update_pedido(pedido, current_user)
        else:
            pedido_obj = services.create_pedido(pedido, current_user)
            operation = "criado"

        response["status"] = "success"
        response["data"] = pedido_obj
        response["message"] = f"Pedido {operation} com sucesso."
    except ValueError as e:
        response["status"] = "error"
        response["message"] = str(e)
    except Exception as e:
        response["status"] = "error"
        response[
            "message"] = f"Erro ao {'criar' if operation == 'criado' else 'atualizar'} pedido: {str(e)}"

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


def handle_get_pedidos_by_empresa_id(empresa_id: str, status: RegistrationStatus | None = None) -> dict:
    """Busca todos os pedidos de uma empresa."""
    response = {}
    try:
        if not empresa_id:
            raise ValueError("ID da empresa é necessário para busca.")

        repository = FirebasePedidosRepository()
        services = PedidosServices(repository)

        pedidos, quantidade_deletados = services.get_pedidos_by_empresa_id(empresa_id, status)

        response["status"] = "success"
        response["data"] = {
            "pedidos": pedidos,
            "quantidade_deletados": quantidade_deletados
        }
    except ValueError as e:
        response["status"] = "error"
        response["message"] = f"Erro de validação: {str(e)}"
    except Exception as e:
        response["status"] = "error"
        response["message"] = f"Erro ao buscar pedidos: {str(e)}"

    return response


def handle_delete_pedido(pedido: Pedido, current_user: Usuario) -> dict:
    """Realiza um soft delete em um pedido, definindo deleted_at."""
    response = {}
    try:
        if not pedido.id:
            raise ValueError("ID do pedido é necessário para deleção.")
        if not current_user:
            raise ValueError("Usuário logado é necessário para deleção.")

        repository = FirebasePedidosRepository()
        services = PedidosServices(repository)

        is_deleted = services.delete_pedido(pedido, current_user)

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

def handle_restore_pedido_from_trash(pedido: Pedido, current_user: Usuario) -> dict:
    """Restaura um pedido da lixeira."""
    response = {}
    try:
        if not pedido.id:
            raise ValueError("ID do pedido é necessário para restauração.")
        if not current_user:
            raise ValueError("Usuário logado é necessário para restauração.")

        repository = FirebasePedidosRepository()
        services = PedidosServices(repository)

        is_restored = services.restore_pedido(pedido, current_user)

        if is_restored:
            response["status"] = "success"
            response["message"] = "Pedido restaurado com sucesso."
        else:
            response["status"] = "error"
            response["message"] = "Erro ao restaurar pedido."
    except ValueError as e:
        response["status"] = "error"
        response["message"] = str(e)
    except Exception as e:
        response["status"] = "error"
        response["message"] = f"Erro ao restaurar pedido: {str(e)}"

    return response
