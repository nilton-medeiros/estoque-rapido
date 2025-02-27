import logging
from src.domain.models.cnpj import CNPJ
from src.domain.models.company import Company
from src.services.entities.company_service import CompanyService
from storage.data.firebase.firebase_company_repository import FirebaseCompanyRepository

logger = logging.getLogger(__name__)

"""
Essa estrutura garante um controle claro de responsabilidades, onde company_controller atua organizando
e redirecionando os dados ao repositório de dados.
Isso promove uma arquitetura mais limpa e modular, facilitando manutenção e escalabilidade do sistema.
"""

async def handle_save_company(company: Company, create_new: bool) -> dict:
    """
    Manipula a operação de salvar empresa.

    Esta função manipula a operação de salvar uma empresa no banco de dados, seja criando uma nova
    empresa ou atualizando uma existente. Ela utiliza um repositório específico para realizar as
    operações necessárias.

    Args:
        company (Company): A instância da empresa a ser salva.
        create_new (bool): Um booleano indicando se a empresa deve ser criada (True) ou atualizada (False).

    Returns:
        dict: Um dicionário contendo o status da operação, uma mensagem de sucesso ou erro, e o ID da empresa.

    Raises:
        ValueError: Se houver um erro de validação ao salvar a empresa.
        Exception: Se ocorrer um erro inesperado durante a operação.

    Exemplo:
        >>> company = Company(name="Minha Empresa", cnpj=CNPJ("00.000.000/0000-00"))
        >>> response = await handle_save_company(company, create_new=True)
        >>> print(response)
    """
    response = {
        "is_error": False,
        "message": "",
        "company_id": None
    }

    try:
        # Usa o repositório do Firebase! Para outro banco, apenas troque o repositório abaixo pelo novo.
        repository = FirebaseCompanyRepository()
        company_service = CompanyService(repository)

        operation = "criada" if create_new else "alterada"
        company_id = None

        if create_new:
            # Criar nova empresa
            company_id = await company_service.create_company(company)
        else:
            # Alterar empresa existente
            company_id = await company_service.update_company(company)

        response["message"] = f"Empresa {operation} com sucesso!"
        response["company_id"] = company_id

    except ValueError as e:
        response["is_error"] = True
        response["message"] = f"Erro de validação: {str(e)}"
        logger.error(response["message"])
    except Exception as e:
        response["is_error"] = True
        response["message"] = str(e)
        logger.error(response["message"])

    return response


async def handle_get_company(company_id: str = None, cnpj: CNPJ = None) -> dict:
    """
    Manipula a operação de buscar empresa.

    Esta função manipula a operação de buscar uma empresa no banco de dados utilizando o CNPJ fornecido.
    Ela utiliza um repositório específico para realizar a busca e retorna os detalhes da empresa, se encontrada.

    Args:
        company_id (str): O ID da empresa a ser buscado. Se for None, verifica se a buscar é por CNPJ
        cnpj (CNPJ): O CNPJ da empresa a ser buscada. Se for None, verifica se a busca é por company_id

    Returns:
        dict: Um dicionário contendo o status da operação, uma mensagem de sucesso ou erro, e os dados da empresa.

    Raises:
        ValueError: Se houver um erro de validação ao buscar a empresa.
        Exception: Se ocorrer um erro inesperado durante a operação.

    Exemplo:
        >>> cnpj = CNPJ("00.000.000/0000-00")
        >>> response = await handle_get_company(cnpj)
        >>> print(response)
    """
    response = {
        "is_error": False,
        "message": "",
        "company": None
    }

    try:
        # Usa o repositório do Firebase para buscar a empresa
        repository = FirebaseCompanyRepository()
        company_service = CompanyService(repository)

        company = None

        if company_id:
            # Busca a empresa pelo ID
            company = await company_service.find_by_id(company_id)
        elif cnpj:
            # Busca a empresa pelo CNPJ
            company = await company_service.find_by_cnpj(cnpj)
        else: raise ValueError("Um dos argumentos company_id ou CNPJ deve ser passado")

        if company:
            response["message"] = "Empresa encontrada com sucesso!"
            response["company"] = company
        else:
            response["is_error"] = True
            response["message"] = "Empresa não encontrada"

    except ValueError as e:
        response["is_error"] = True
        response["message"] = f"Erro de validação: {str(e)}"
        logger.error(response["message"])
    except Exception as e:
        response["is_error"] = True
        response["message"] = str(e)
        logger.error(response["message"])

    return response
