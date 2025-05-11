import logging

from src.domains.empresas.models.cnpj import CNPJ  # Importar diretamente para evitar cíclo em src/domains/empresa/__init__.py
from src.domains.empresas.models.empresa_model import Empresa
from src.domains.empresas.models.empresa_subclass import Status
from src.domains.empresas.repositories.implementations.firebase_empresas_repository import FirebaseEmpresasRepository
from src.domains.empresas.services.empresas_services import EmpresasServices

logger = logging.getLogger(__name__)

"""
Essa estrutura garante um controle claro de responsabilidades, onde empresas_controller atua organizando
e redirecionando os dados ao repositório de dados.
Isso promove uma arquitetura mais limpa e modular, facilitando manutenção e escalabilidade do sistema.
"""


async def handle_save_empresas(empresa: Empresa, usuario: dict) -> dict:
    """
    Manipula a operação de salvar empresa.

    Esta função manipula a operação de salvar uma empresa no banco de dados, seja criando uma nova
    empresa ou atualizando uma existente. Ela utiliza um repositório específico para realizar as
    operações necessárias.

    Args:
        empresa (Empresa): A instância do empresa a ser salva.
        usuario (Ususario): Usuário logado.

    Returns:
        dict: Um dicionário contendo o status da operação, uma mensagem de sucesso ou erro, e o ID do empresa.

    Raises:
        ValueError: Se houver um erro de validação ao salvar a empresa.
        Exception: Se ocorrer um erro inesperado durante a operação.

    Exemplo:
        >>> empresa = Empresa(corporate_name="Minha Empresa", cnpj=CNPJ("00.000.000/0000-00"))
        >>> response = await handle_save_empresas(empresa, create_new=True)
        >>> print(response)
    """
    response = {
        "is_error": False,
        "message": "",
        "id": None
    }

    try:
        # Usa o repositório do Firebase! Para outro banco, apenas troque o repositório abaixo pelo novo.
        repository = FirebaseEmpresasRepository()
        empresas_services = EmpresasServices(repository)

        operation = "atualizada"
        id = None

        if empresa.id:
            # Alterar empresa existente
            id = await empresas_services.update(empresa, usuario)
        else:
            # Criar novo empresa
            operation = "criada"
            id = await empresas_services.create(empresa, usuario)

        response["message"] = f"Empresa {operation} com sucesso!"
        response["id"] = id

    except ValueError as e:
        response["is_error"] = True
        response["message"] = f"handle_save_empresas ValueError: Erro de validação: {str(e)}"
        logger.error(response["message"])
    except Exception as e:
        response["is_error"] = True
        response["message"] = str(e)
        logger.error(response["message"])

    return response


async def handle_get_empresas_by_id(id: str) -> dict:
    """
    Manipula a operação de buscar empresa.

    Esta função manipula a operação de buscar uma empresa no banco de dados utilizando o ID fornecido.
    Ela utiliza um repositório específico para realizar a busca e retorna os detalhes do empresa, se encontrada.

    Args:
        id (str): O ID do empresa a ser buscado.

    Returns:
        dict: Um dicionário contendo o status da operação, uma mensagem de sucesso ou erro, e os dados do empresa.

    Raises:
        ValueError: Se houver um erro de validação ao buscar a empresa.
        Exception: Se ocorrer um erro inesperado durante a operação.

    Exemplo:
        >>> response = await handle_get_empresas_by_id('abc123')
        >>> print(response)
    """
    response = {
        "is_error": False,
        "message": "",
        "empresa": None
    }

    try:
        # Usa o repositório do Firebase para buscar a empresa
        repository = FirebaseEmpresasRepository()
        empresas_services = EmpresasServices(repository)

        empresa = None

        if id:
            # Busca a empresa pelo ID
            empresa = await empresas_services.find_by_id(id)
        else:
            raise ValueError("Busca empresa por ID: O id deve ser informado")

        if empresa:
            response["message"] = "Empresa encontrada com sucesso!"
            response["empresa"] = empresa
        else:
            # Improvável, pois se não encontrar a empresa, é retornado uma exceção
            # Mas, caso aconteça, é tratado aqui
            response["is_error"] = True
            response["message"] = f"Empresa não encontrada id {id}"

    except ValueError as e:
        response["is_error"] = True
        response["message"] = f"handle_get_empresas_by_id ValueError: Erro de validação: {str(e)}"
        logger.error(response["message"])
    except Exception as e:
        response["is_error"] = True
        response["message"] = str(e)

    return response


async def handle_get_empresas_by_cnpj(cnpj: CNPJ) -> dict:
    """
    Manipula a operação de buscar empresa.

    Esta função manipula a operação de buscar uma empresa no banco de dados utilizando o CNPJ fornecido.
    Ela utiliza um repositório específico para realizar a busca e retorna os detalhes do empresa, se encontrada.

    Args:
        id (str): O ID do empresa a ser buscado. Se for None, verifica se a buscar é por CNPJ
        cnpj (CNPJ): O CNPJ do empresa a ser buscada. Se for None, verifica se a busca é por id

    Returns:
        dict: Um dicionário contendo o status da operação, uma mensagem de sucesso ou erro, e os dados do empresa.

    Raises:
        ValueError: Se houver um erro de validação ao buscar a empresa.
        Exception: Se ocorrer um erro inesperado durante a operação.

    Exemplo:
        >>> cnpj = CNPJ("00.000.000/0000-00")
        >>> response = await handle_get_empresas_by_cnpj(cnpj)
        >>> print(response)
    """
    response = {
        "is_error": False,
        "message": "",
        "empresa": None
    }

    try:
        # Usa o repositório do Firebase para buscar a empresa
        repository = FirebaseEmpresasRepository()
        empresas_services = EmpresasServices(repository)

        empresa = None

        if cnpj:
            # Busca a empresa pelo CNPJ
            empresa = await empresas_services.find_by_cnpj(cnpj)
        else:
            raise ValueError("O CNPJ deve ser passado")

        if empresa:
            response["message"] = "Empresa encontrada com sucesso!"
            response["empresa"] = empresa
        else:
            # Improvável, pois se não encontrar a empresa, é retornado uma exceção
            # Mas, caso aconteça, é tratado aqui
            response["is_error"] = True
            response["message"] = "Empresa não encontrada"

    except ValueError as e:
        response["is_error"] = True
        response["message"] = f"handle_get_empresas_by_cnpj ValueError: Erro de validação: {str(e)}"
        logger.error(response["message"])
    except Exception as e:
        response["is_error"] = True
        response["message"] = str(e)

    return response


async def handle_get_empresas(ids_empresas: set[str]|list[str], status_active: bool = True) -> list:
    """
    Busca todas as empresas do usuário logado que sejam ativa ou não, dependendo do status_active desejado.

    Esta função retorna todas as empresas do usuário logado, se não houver empresas, retorna uma lista vazia.
    Ela utiliza um repositório específico para realizar a busca e retorna a lista de empresas, se encontrada.

    Args:
        ids_empresas (set[str]|list[str]): Uma lista ou conjunto de ID's das empresas do usuário logado.
        status_active (bool): Padrão True, define se serão filtrados somente as empresas ativas ou somente as não ativa (arquivadas ou deletadas).

    Returns:
        is_error (bool): True se houve erro na operação, False caso contrário.
        message (str): Uma mensagem de sucesso ou erro.
        data_list (list): Uma lista de empresas do usuário logado ou [].
        inactivated (int): Quantidade de empresas inativadas

    Raises:
        ValueError: Se houver um erro de validação ao buscar empresas.
        Exception: Se ocorrer um erro inesperado durante a operação.

    Exemplo:
        >>> response = await handle_get_empresas(['abc123', 'def456'])
        >>> print(response)
    """

    response = {
        "is_error": False,
        "message": "",
        "data_list": [],
        "inactivated": 0,
    }

    try:
        # Usa o repositório do Firebase para buscar as empresas
        repository = FirebaseEmpresasRepository()
        empresas_services = EmpresasServices(repository)

        if not ids_empresas or len(ids_empresas) == 0:
            raise ValueError("A lista de empresas não pode ser vazia")
        list_empresas, quantify = await empresas_services.find_all(ids_empresas=ids_empresas, status_active=status_active)
        response["inactivated"] = quantify if quantify else 0

        if list_empresas:
            response["message"] = "Empresas encontradas com sucesso!"
            response["data_list"] = list_empresas
        else:
            response["is_error"] = True
            response["message"] = "Nenhuma empresas encontrada!"
    except ValueError as e:
        response["is_error"] = True
        response["message"] = f"handle_get_empresas ValueError: Erro de validação: {str(e)}"
    except Exception as e:
        response["is_error"] = True
        response["message"] = str(e)

    return response


async def handle_update_status_empresas(empresa: Empresa, usuario: dict, status: Status) -> dict:
    """
    Manipula a operação de status para ativo, deletedo ou arquivado de uma empresa no banco de dados.
    Ela utiliza um repositório específico para realizar a exclusão e retorna True se bem sucedido ou False em caso de erro.

    Args:
        empresa (Empresa): A instância da empresa a ser alterada.
        usuario (Ususario): Usuário logado.
        status (Status): Novo status da empresa. ARCHIVED, DELETED ou ACTIVE.

    Returns:
        response (dict): Retorna as informações necessárias, inclusive as de erros.

    Raises:
        Exception: Se ocorrer um erro inesperado durante a operação.

    Exemplo:
        >>> response = await handle_update_status_empresas(empresa, Status.DELETED)
        >>> print(response)
    """

    response = {
        "is_error": False,
        "message": "",
        "status": None,
    }

    try:
        # Usa o repositório do Firebase
        repository = FirebaseEmpresasRepository()
        empresas_services = EmpresasServices(repository)

        is_updated = False

        if not usuario:
            raise ValueError("Usuário não informado em args: handle_update_status_empresas")
        if not isinstance(usuario, dict):
            raise ValueError("Usuário não é um dicionário em args: handle_update_status_empresas")
        if not empresa:
            raise ValueError("Empresa não informada em args: handle_update_status_empresas")
        if not isinstance(empresa, Empresa):
            raise ValueError("Empresa não é uma instância de Empresa em args: handle_update_status_empresas")
        if not status:
            raise ValueError("Status não informado em args: handle_update_status_empresas")
        if not isinstance(status, Status):
            raise ValueError("Argumento status não é uma instância de Status")

        is_updated = await empresas_services.update_status(empresa=empresa, usuario=usuario, status=status)

        if is_updated:
            response["status"] = status
            response["message"] = f"Status da empresa alterado com sucesso! Status: {status.value}"
        else:
            # Improvável, pois se não encontrar a empresa, é retornado uma exceção
            # Mas, caso aconteça, é tratado aqui
            response["is_error"] = True
            response["message"] = "Erro ao alterar o status da empresa"

    except ValueError as e:
        response["is_error"] = True
        response["message"] = f"handle_update_status_empresas().ValueError: Erro de validação: {str(e)}"
        logger.error(response["message"])
    except Exception as e:
        response["is_error"] = True
        response["message"] = str(e)
        logger.error(response["message"])

    return response