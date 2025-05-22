import logging

from typing import Any
from src.domains.produtos.models import ProdutoCategorias, ProdutoStatus
from src.domains.produtos.repositories import FirebaseCategoriasRepository
from src.domains.produtos.services import CategoriasServices

logger = logging.getLogger(__name__)


async def handle_save(categoria: ProdutoCategorias, usuario: dict[str,Any]) -> dict[str, Any]:
    """Salva ou atualiza uma categoria de produto."""
    response = {}

    try:
        repository = FirebaseCategoriasRepository()
        categorias_services = CategoriasServices(repository)

        operation = "atualizada"

        if categoria.id:
            id = await categorias_services.update(categoria, usuario)
        else:
            id = await categorias_services.create(categoria, usuario)
            operation = "criada"

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


async def handle_update_status(categoria: ProdutoCategorias, usuario: dict, status: ProdutoStatus) -> dict[str, Any]:
    """Manipula o status para ativo, inativo ou deletada de uma categoria de produto."""
    response = {}

    try:
        if not categoria.id:
            raise ValueError("ID da categoria não pode ser nulo ou vazio")
        if not isinstance(categoria, ProdutoCategorias):
            raise ValueError("Categoria não é do tipo ProdutoCategorias")
        if not usuario:
            raise ValueError("Usuário não pode ser nulo ou vazio")
        if not isinstance(usuario, dict):
            raise ValueError("Usuário não é do tipo dict")
        if not status:
            raise ValueError("Status não pode ser nulo ou vazio")
        if not isinstance(status, ProdutoStatus):
            raise ValueError("Status não é do tipo ProdutoStatus")

        repository = FirebaseCategoriasRepository()
        categorias_services = CategoriasServices(repository)

        is_updated = await categorias_services.update_status(categoria, usuario, status)

        if is_updated:
            response["status"] = "success"
            response["data"] = status
        else:
            response["status"] = "error"
            response["message"] = f"Não foi possível atualizar o status da categoria para {status.value}"

    except ValueError as e:
        response["status"] = "error"
        response["message"] = f"Erro de validação: {str(e)}"
        logger.error("cat_controllers.handle_update_status(ValueError). " + response["message"])
    except Exception as e:
        response["status"] = "error"
        response["message"] = str(e)
        logger.error(response["message"])

    return response


async def handle_get_all(empresa_id: str, status_deleted: bool = False) -> dict[str, Any]:
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
        >>> response = await handle_get_empresas(['abc123', 'def456'])
        >>> print(response)
    """

    response = {}

    try:
        # Usa o repositório do Firebase para buscar as categorias
        repository = FirebaseCategoriasRepository()
        categorias_services = CategoriasServices(repository)

        if not empresa_id:
            raise ValueError("ID da empresa logada não pode ser nulo ou vazio")
        categorias_list, quantify = await categorias_services.get_all(empresa_id=empresa_id, status_deleted=status_deleted)

        if categorias_list:
            response["status"] = "success"
            response["data"] = {
                "categorias": categorias_list,
                "deleted": quantify if quantify else 0,
            }
        else:
            response["status"] = "error"
            response["message"] = "Nenhuma categoria de produto encontrada!"
    except ValueError as e:
        response["status"] = "error"
        response["message"] = f"categorias_controllers.handle_get_all ValueError: Erro de validação: {str(e)}"
    except Exception as e:
        response["status"] = "error"
        response["message"] = str(e)

    return response