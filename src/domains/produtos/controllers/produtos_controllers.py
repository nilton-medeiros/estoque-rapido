import logging

from typing import Any
from src.domains.produtos.models import Produto
from src.domains.shared import RegistrationStatus
from src.domains.produtos.repositories import FirebaseProdutosRepository
from src.domains.produtos.services import ProdutosServices
from src.domains.usuarios.models.usuarios_model import Usuario


logger = logging.getLogger(__name__)


def handle_save(produto: Produto, current_user: Usuario) -> dict[str, Any]:
    """Salva ou atualiza um produto."""
    response = {}

    try:
        repository = FirebaseProdutosRepository(company_id=produto.empresa_id)
        produtos_services = ProdutosServices(repository)

        operation = "atualizado"

        if produto.id:
            id = produtos_services.update(produto, current_user)
        else:
            id = produtos_services.create(produto, current_user)
            operation = "criado"

        response["status"] = "success"
        response["data"] = id

    except ValueError as e:
        response["status"] = "error"
        response["message"] = f"handle_save ValueError: Erro de validação: {str(e)}"
        logger.error(response["message"])
    except Exception as e:
        response["status"] = "error"
        response["message"] = str(e)
        logger.error(response["message"])

    return response


def handle_update_status(produto: Produto, current_user: Usuario, status: RegistrationStatus) -> dict[str, Any]:
    """Manipula o status para ativo, inativo ou deletado de um produto."""
    response = {}

    try:
        if not produto.id:
            raise ValueError("ID da produto não pode ser nulo ou vazio")
        if not isinstance(produto, Produto):
            raise ValueError("Produto não é do tipo Produto")
        if not current_user:
            raise ValueError("Usuário não pode ser nulo ou vazio")
        if not isinstance(current_user, Usuario):
            raise ValueError("O argumento current_user não é do tipo 'Usuario'")
        if not isinstance(current_user.id, str):
            raise ValueError("O Usuário não tem um ID válido")
        if not status:
            raise ValueError("Status não pode ser nulo ou vazio")
        if not isinstance(status, RegistrationStatus):
            raise ValueError("Status não é do tipo RegistrationStatus")

        repository = FirebaseProdutosRepository(company_id=produto.empresa_id)
        produtos_services = ProdutosServices(repository)

        is_updated = produtos_services.update_status(produto, current_user, status)

        if is_updated:
            response["status"] = "success"
            response["data"] = status
        else:
            response["status"] = "error"
            response["message"] = f"Não foi possível atualizar o status da produto para {status.produto_label}"

    except ValueError as e:
        response["status"] = "error"
        response["message"] = f"Erro de validação: {str(e)}"
        logger.error("produtos_controllers.handle_update_status(ValueError). " + response["message"])
    except Exception as e:
        response["status"] = "error"
        response["message"] = str(e)
        logger.error(response["message"])

    return response


def handle_get_by_id(empresa_id: str, produto_id: str) -> dict | None:
    """Busca uma produto de produto pelo seu ID."""
    response = {}

    try:
        if not empresa_id:
            raise ValueError("ID da empresa não pode ser nulo ou vazio")
        if not produto_id:
            raise ValueError("ID do produto não pode ser nulo ou vazio")

        repository = FirebaseProdutosRepository(company_id=empresa_id)
        produtos_services = ProdutosServices(repository)

        produto = produtos_services.get_by_id(produto_id)

        if produto:
            response["status"] = "success"
            response["data"] = produto
        else:
            response["status"] = "error"
            response["message"] = "Produto não encontrado"

    except ValueError as e:
        response["status"] = "error"
        response["message"] = f"handle_get_by_id ValueError: Erro de validação: {str(e)}"
        logger.error(response["message"])
    except Exception as e:
        response["status"] = "error"
        response["message"] = str(e)

    return response


def handle_get_all(empresa_id: str, status_deleted: bool = False) -> dict[str, Any]:
    """
    Busca todos os produtos da empresa logada que sejam ativa ou não, dependendo do status_active desejado.

    Esta função retorna todos os produtos da empresa logada, se não houver produtos, retorna uma lista vazia.
    Ela utiliza um repositório específico para realizar a busca e retorna a lista de produtos, se encontrada.

    Args:
        empresa_id (str): O ID da empresa para buscar os produtos.
        status_deleted (bool): True para produtos deletados, False para produtos ativos.

    Returns (dict):
        status (str): "success" ou "error"
        message (str): Uma mensagem de erro.
        data (dict):
            "produtos": Lista de produtos encontrados.
            "deleted": Quantidade de produtos deletados. (para o tooltip da lixeira).

    Raises:
        ValueError: Se houver um erro de validação ao buscar produtos.
        Exception: Se ocorrer um erro inesperado durante a operação.

    Exemplo:
        >>> response = handle_get_all(['abc123', 'def456'])
        >>> print(response)
    """

    response = {}

    try:
        # Usa o repositório do Firebase para buscar os produtos
        repository = FirebaseProdutosRepository(company_id=empresa_id)
        produtos_services = ProdutosServices(repository)

        if not empresa_id:
            raise ValueError("ID da empresa logada não pode ser nulo ou vazio")
        produtos_list, quantity = produtos_services.get_all(status_deleted=status_deleted)

        response["status"] = "success"
        response["data"] = {
            "produtos": produtos_list if produtos_list else [],
            "deleted": quantity if quantity else 0,
        }
    except ValueError as e:
        response["status"] = "error"
        response["message"] = f"produtos_controllers.handle_get_all ValueError: Erro de validação: {str(e)}"
    except Exception as e:
        response["status"] = "error"
        response["message"] = str(e)

    return response


def handle_get_low_stock_count(empresa_id: str) -> dict[str, Any]:
    """
    Obtém a quantidade de produtos ativos que necessitam de reposição no estoque.
    Um produto necessita de reposição se 'quantity_on_hand' < 'minimum_stock_level'.
    """
    response = {}

    try:
        # Usa o repositório do Firebase para buscar os produtos
        repository = FirebaseProdutosRepository(company_id=empresa_id)
        produtos_services = ProdutosServices(repository)

        if not empresa_id:
            raise ValueError("ID da empresa logada não pode ser nulo ou vazio")

        quantity = produtos_services.get_low_stock_count()

        response["status"] = "success"
        response["data"] = {
            "products_low_stock": quantity if quantity else 0,
        }
    except ValueError as e:
        response["status"] = "error"
        response["message"] = f"produtos_controllers.handle_get_low_stock_count ValueError: Erro de validação: {str(e)}"
    except Exception as e:
        response["status"] = "error"
        response["message"] = str(e)

    return response
