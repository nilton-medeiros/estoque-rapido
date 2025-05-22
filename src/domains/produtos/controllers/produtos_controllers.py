import logging

from typing import Any
from src.domains.produtos.models import Produto, ProdutoStatus
from src.domains.produtos.repositories import FirebaseProdutosRepository
from src.domains.produtos.services import ProdutosServices


logger = logging.getLogger(__name__)


def handle_save(produto: Produto, usuario: dict[str,Any]) -> dict[str, Any]:
    """Salva ou atualiza uma produto de produto."""
    response = {}

    try:
        repository = FirebaseProdutosRepository(company_id=produto.empresa_id)
        produtos_services = ProdutosServices(repository)

        operation = "atualizado"

        if produto.id:
            id = produtos_services.update(produto, usuario)
        else:
            id = produtos_services.create(produto, usuario)
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


def handle_update_status(produto: Produto, usuario: dict, status: ProdutoStatus) -> dict[str, Any]:
    """Manipula o status para ativo, inativo ou deletada de uma produto de produto."""
    response = {}

    try:
        if not produto.id:
            raise ValueError("ID da produto não pode ser nulo ou vazio")
        if not isinstance(produto, Produto):
            raise ValueError("Categoria não é do tipo Produto")
        if not usuario:
            raise ValueError("Usuário não pode ser nulo ou vazio")
        if not isinstance(usuario, dict):
            raise ValueError("Usuário não é do tipo dict")
        if not status:
            raise ValueError("Status não pode ser nulo ou vazio")
        if not isinstance(status, ProdutoStatus):
            raise ValueError("Status não é do tipo ProdutoStatus")

        repository = FirebaseProdutosRepository(company_id=produto.empresa_id)
        produtos_services = ProdutosServices(repository)

        is_updated = produtos_services.update_status(produto, usuario, status)

        if is_updated:
            response["status"] = "success"
            response["data"] = status
        else:
            response["status"] = "error"
            response["message"] = f"Não foi possível atualizar o status da produto para {status.value}"

    except ValueError as e:
        response["status"] = "error"
        response["message"] = f"Erro de validação: {str(e)}"
        logger.error("cat_controllers.handle_update_status(ValueError). " + response["message"])
    except Exception as e:
        response["status"] = "error"
        response["message"] = str(e)
        logger.error(response["message"])

    return response

def get_by_id(self, empresa_id: str, produto_id: str) -> dict | None:
    """Busca uma produto de produto pelo seu ID."""
    response = {}

    try:
        if not empresa_id:
            raise ValueError("ID da empresa não pode ser nulo ou vazio")
        if not produto_id:
            raise ValueError("ID da produto não pode ser nulo ou vazio")

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
        response["message"] = f"get__by_id ValueError: Erro de validação: {str(e)}"
        logger.error(response["message"])
    except Exception as e:
        response["status"] = "error"
        response["message"] = str(e)

    return response


def handle_get_all(empresa_id: str, status_deleted: bool = False) -> dict[str, Any]:
    """
    Busca todas as categorias do usuário logado que sejam ativa ou não, dependendo do status_active desejado.

    Esta função retorna todas as categorias do usuário logado, se não houver categorias, retorna uma lista vazia.
    Ela utiliza um repositório específico para realizar a busca e retorna a lista de categorias, se encontrada.

    Args:
        empresa_id (str): O ID da empresa para buscar as categorias.

    Returns (dict):
        is_error (bool): True se houve erro na operação, False caso contrário.
        message (str): Uma mensagem de sucesso ou erro.
        data_list (list): Uma lista de categorias da empresa logada ou [].
        deleted (int): Quantidade de categorias deletadas (para o tooltip da lixeira).

    Raises:
        ValueError: Se houver um erro de validação ao buscar categorias.
        Exception: Se ocorrer um erro inesperado durante a operação.

    Exemplo:
        >>> response = handle_get_allhandle_update_status_empresas(['abc123', 'def456'])
        >>> print(response)
    """

    response = {}

    try:
        # Usa o repositório do Firebase para buscar as categorias
        repository = FirebaseProdutosRepository(company_id=empresa_id)
        produtos_services = ProdutosServices(repository)

        if not empresa_id:
            raise ValueError("ID da empresa logada não pode ser nulo ou vazio")
        categorias_list, quantify = produtos_services.get_all(empresa_id=empresa_id, status_deleted=status_deleted)

        if categorias_list:
            response["status"] = "success"
            response["data"] = {
                "categorias": categorias_list,
                "deleted": quantify if quantify else 0,
            }
        else:
            response["status"] = "error"
            response["message"] = "Nenhuma produto de produto encontrada!"
    except ValueError as e:
        response["status"] = "error"
        response["message"] = f"categorias_controllers.handle_get_all ValueError: Erro de validação: {str(e)}"
    except Exception as e:
        response["status"] = "error"
        response["message"] = str(e)

    return response