import logging


from src.domains.empresas.models.cnpj import CNPJ
from src.domains.empresas.models.empresa_model import Empresa
from src.domains.empresas.repositories.implementations.firebase_empresas_repository import FirebaseEmpresasRepository
from src.domains.empresas.services.empresas_services import EmpresasServices

logger = logging.getLogger(__name__)

"""
Essa estrutura garante um controle claro de responsabilidades, onde empresas_controller atua organizando
e redirecionando os dados ao repositório de dados.
Isso promove uma arquitetura mais limpa e modular, facilitando manutenção e escalabilidade do sistema.
"""

async def handle_save_empresas(empresa: Empresa) -> dict:
    """
    Manipula a operação de salvar empresa.

    Esta função manipula a operação de salvar uma empresa no banco de dados, seja criando uma nova
    empresa ou atualizando uma existente. Ela utiliza um repositório específico para realizar as
    operações necessárias.

    Args:
        empresa (Empresa): A instância do empresa a ser salva.

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
            id = await empresas_services.update(empresa)
        else:
            # Criar novo empresa
            operation = "criada"
            id = await empresas_services.create(empresa)

        response["message"] = f"Empresa {operation} com sucesso!"
        response["id"] = id

    except ValueError as e:
        response["is_error"] = True
        response["message"] = f"Erro de validação: {str(e)}"
        logger.error(response["message"])
    except Exception as e:
        response["is_error"] = True
        response["message"] = str(e)
        logger.error(response["message"])

    return response


async def handle_get_empresas(id: str = None, cnpj: CNPJ = None) -> dict:
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
        >>> response = await handle_get_empresas(cnpj)
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
        elif cnpj:
            # Busca a empresa pelo CNPJ
            empresa = await empresas_services.find_by_cnpj(cnpj)
        else: raise ValueError("Um dos argumentos id ou CNPJ deve ser passado")

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
        response["message"] = f"Erro de validação: {str(e)}"
        logger.error(response["message"])
    except Exception as e:
        response["is_error"] = True
        response["message"] = str(e)

    return response
