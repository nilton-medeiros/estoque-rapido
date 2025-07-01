import logging

from typing import Any
from src.domains.shared import RegistrationStatus
from src.domains.categorias.models import ProdutoCategorias
from src.domains.categorias.repositories import FirebaseCategoriasRepository
from src.domains.categorias.services import CategoriasServices

logger = logging.getLogger(__name__)


def handle_save(categoria: ProdutoCategorias, usuario: dict[str, Any]) -> dict[str, Any]:
    """Salva ou atualiza uma categoria de produto."""
    response = {}

    try:
        repository = FirebaseCategoriasRepository()
        categorias_services = CategoriasServices(repository)

        operation = "atualizada"

        if categoria.id:
            id = categorias_services.update(categoria, usuario)
        else:
            id = categorias_services.create(categoria, usuario)
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


def handle_update_status(categoria: ProdutoCategorias, usuario: dict, status: RegistrationStatus) -> dict[str, Any]:
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
        if not isinstance(status, RegistrationStatus):
            raise ValueError("Status não é do tipo RegistrationStatus")

        repository = FirebaseCategoriasRepository()
        categorias_services = CategoriasServices(repository)

        is_updated = categorias_services.update_status(
            categoria, usuario, status)

        if is_updated:
            response["status"] = "success"
            response["data"] = status
        else:
            response["status"] = "error"
            response[
                "message"] = f"Não foi possível atualizar o status da categoria para {status.produto_label}"

    except ValueError as e:
        response["status"] = "error"
        response["message"] = f"Erro de validação: {str(e)}"
        logger.error(
            "categorias_controllers.handle_update_status(ValueError). " + response["message"])
    except Exception as e:
        response["status"] = "error"
        response["message"] = str(e)
        logger.error(response["message"])

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
        >>> response = handle_get_all(['abc123', 'def456'])
        >>> print(response)
    """

    response = {}

    try:
        # Usa o repositório do Firebase para buscar as categorias
        repository = FirebaseCategoriasRepository()
        categorias_services = CategoriasServices(repository)

        if not empresa_id:
            raise ValueError("ID da empresa logada não pode ser nulo ou vazio")

        categorias_list, quantity = categorias_services.get_all(empresa_id=empresa_id, status_deleted=status_deleted)

        response["status"] = "success"
        response["data"] = {
            "categorias": categorias_list if categorias_list else [],
            "deleted": quantity if quantity else 0,
        }
    except ValueError as e:
        response["status"] = "error"
        response[
            "message"] = f"categorias_controllers.handle_get_all ValueError: Erro de validação: {str(e)}"
    except Exception as e:
        response["status"] = "error"
        response["message"] = str(e)

    return response


def handle_get_active_categorias_summary(empresa_id: str) -> dict[str, Any]:
    """
    Obtém um resumo (ID, nome, descrição) de todas as categorias ativas
        de uma empresa, ordenadas por nome.

    Args:
        empresa_id (str): O ID da empresa para buscar as categorias.

    return (dict): response:
     sucesso: {"status": "success", "data": [summary_list]}
     erro: {"status": "error", "message": "mensagem de erro"}
    """
    response = {}

    try:
        # Usa o repositório do Firebase para buscar as categorias
        repository = FirebaseCategoriasRepository()
        categorias_services = CategoriasServices(repository)

        if not empresa_id:
            raise ValueError("ID da empresa logada não pode ser nulo ou vazio")
        summary_list = categorias_services.get_summary(empresa_id)

        if summary_list:
            response["status"] = "success"
            response["data"] = summary_list
        else:
            response["status"] = "error"
            response["message"] = "Nenhuma categoria de produto encontrada!"
    except ValueError as e:
        response["status"] = "error"
        response[
            "message"] = f"categorias_controllers.handle_get_all ValueError: Erro de validação: {str(e)}"
    except Exception as e:
        response["status"] = "error"
        response["message"] = str(e)

    return response

def handle_get_active_id(empresa_id: str, nome: str) -> str | None:
    """Obtem o ID da categoria pelo nome da categoria"""
    try:
        repository = FirebaseCategoriasRepository()
        categorias_services = CategoriasServices(repository)

        if not nome:
            raise ValueError("Nome da categoria não pode ser nulo ou vazio")
        if not empresa_id:
            raise ValueError("ID da empresa logada não pode ser nulo ou vazio")

        categoria_id = categorias_services.get_active_id(company_id=empresa_id, name=nome)

        return categoria_id
    except ValueError as e:
        raise ValueError(f"categorias_controllers.handle_get_active_id ValueError: Erro de validação: {str(e)}")
    except Exception as e:
        raise Exception(str(e))
