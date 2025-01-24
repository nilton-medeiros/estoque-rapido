from models.cnpj import CNPJ
from models.company import Company
from src.services.entities.company_service import CompanyService
from storage.data.firebase.firebase_company_repository import FirebaseCompanyRepository

"""
Essa estrutura garante um controle claro de responsabilidades, onde company_controller atua organizando
e redirecionando os dados ao repositório de dados.
Isso promove uma arquitetura mais limpa e modular, facilitando manutenção e escalabilidade do sistema.
"""

async def handle_save_company(company: Company, create_new: bool) -> dict:
    """Manipula a operação salvar empresa.

    Descrição mais detalhada do método, incluindo objetivo, comportamento e casos especiais,
    se necessário.

    Args:
        parametro1 (str): Descrição do primeiro parâmetro.
        parametro2 (int): Descrição do segundo parâmetro.

    Returns:
        bool: Descrição do que o método retorna.

    Raises:
        ValueError: Descrição da exceção que pode ser lançada, se aplicável.

    Exemplo:
        Exemplo de como usar o método, se relevante.
        >>> obj = MinhaClasse()
        >>> resultado = obj.meu_metodo('teste', 42)
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

        response["message"] = f"Empresa {operation} com sucessso!"
        response["company_id"] = company_id

    except ValueError as e:
        response["is_error"] = True
        response["message"] = f"Erro de validação: {str(e)}"
    except Exception as e:
        response["is_error"] = True
        response["message"] = str(e)

    return response


async def handle_get_company(cnpj: CNPJ):
    '''
    Manipula a operação de buscar empresa.
    '''
    response = {
        "is_error": False,
        "message": "",
        "company": None
    }

    try:
        # Usa o repositório do Firebase para buscar o usuário
        repository = FirebaseCompanyRepository()
        company_service = CompanyService(repository)

        # Busca a empresa pelo CNPJ
        company = await company_service.find_user_by_cnpj(cnpj)

        if company:
            response["message"] = "Empresa encontrada com sucesso!"
            response["company"] = company
        else:
            response["is_error"] = True
            response["message"] = "Empresa não encontrada"

    except ValueError as e:
        response["is_error"] = True
        response["message"] = f"Erro de validação: {str(e)}"
    except Exception as e:
        response["is_error"] = True
        response["message"] = str(e)

    return response
