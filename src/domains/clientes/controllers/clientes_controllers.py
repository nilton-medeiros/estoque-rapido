import logging

from src.domains.clientes.models.cliente_model import Cliente
from src.domains.clientes.repositories.implementations.firebase_clientes_repository import FirebaseClientesRepository
from src.domains.clientes.services.clientes_services import ClientesServices


logger = logging.getLogger(__name__)


def handle_save(cliente: Cliente, usuario_logado: dict) -> dict:
    """Salva ou atualiza um cliente.

    Args:
        cliente (Cliente): Objeto cliente a ser criado ou atualizado.
        usuario_logado (dict): Usuário logado para campos de auditoria.

    Returns:
        response (dict): Resposta da operação.
    """
    response = {}

    try:
        repository = FirebaseClientesRepository(cliente.empresa_id)
        clientes_services = ClientesServices(repository)

        operation = "atualizado"

        if cliente.id:
            id = clientes_services.update(cliente, usuario_logado)
        else:
            id = clientes_services.create(cliente, usuario_logado)
            operation = "criado"

        response["status"] = "success"
        response["data"] = id
        response["message"] = f"Cliente {operation} com sucesso"

    except ValueError as e:
        response["status"] = "error"
        response["message"] = f"handle_save ValueError: Erro de validação: {str(e)}"
        logger.error(response["message"])
    except Exception as e:
        response["status"] = "error"
        response["message"] = str(e)
        logger.error(response["message"])

    return response


def handle_get_by_id(cliente_id: str, empresa_logada: str) -> dict:
    """
    Obtém um cliente pelo seu ID.

    Args:
        cliente_id (str): ID do cliente a ser obtido.
        empresa_logada (str): ID da empresa logada.

    Returns:
        objeto (Cliente | None): Cliente encontrado ou None se não existir.
    """
    response = {}

    try:
        if not cliente_id:
            raise ValueError("ID do cliente é necessário")
        if not empresa_logada:
            raise ValueError("ID da empresa é necessário")

        repository = FirebaseClientesRepository(empresa_logada)
        clientes_services = ClientesServices(repository)

        cliente = clientes_services.get_by_id(cliente_id)

        if cliente:
            response["status"] = "success"
            response["data"] = cliente
        else:
            response["status"] = "error"
            response["message"] = "Cliente não encontrado"

    except ValueError as e:
        response["status"] = "error"
        response["message"] = f"clientes_controllers.handle_get_by_id ValueError: Erro de validação: {str(e)}"
        logger.error(response["message"])
    except Exception as e:
        response["status"] = "error"
        response["message"] = str(e)

    return response


def handle_get_all(empresa_logada: str) -> dict:
    """
    Obtém todos os clientes da empresa logada.

    Args:
        empresa_logada (str): ID da empresa logada.

    Returns:
        response (dict): Resposta da operação.
    """
    response = {}

    try:

        if not empresa_logada:
            raise ValueError("ID da empresa é necessário")

        repository = FirebaseClientesRepository(empresa_logada)
        clientes_services = ClientesServices(repository)

        clientes_list, quantidade_deletados = clientes_services.get_all()

        response["status"] = "success"
        response["data"] = {
            "clientes": clientes_list,
            "quantidade_deletados": quantidade_deletados
        }
    except ValueError as e:
        response["status"] = "error"
        response["message"] = f"clientes_controllers.handle_get_all ValueError: Erro de validação: {str(e)}"
    except Exception as e:
        response["status"] = "error"
        response["message"] = str(e)

    return response
