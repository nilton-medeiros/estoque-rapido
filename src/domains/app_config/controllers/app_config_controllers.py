import logging
from typing import Any, Optional

from src.domains.app_config.models.app_config_model import AppConfig
from src.domains.app_config.repositories.implementations.firebase_app_config_repository import FirebaseAppConfigRepository
from src.domains.app_config.services.app_config_services import AppConfigServices

"""
Essa estrutura garante um controle claro de responsabilidades, onde user_controller atua organizando
e redirecionando os dados ao repositório de dados.
Isso promove uma arquitetura mais limpa e modular, facilitando manutenção e escalabilidade do sistema.
"""

logger = logging.getLogger(__name__)

def handle_save_config(settings: AppConfig, create_new: bool) -> dict:
    """
    Manipula a operação de salvar Configuração do sistema.

    Esta função manipula a operação de salvar uma configuração no banco de dados, seja criando uma nova
    configuração ou atualizando uma existente. Ela utiliza um repositório específico para realizar as
    operações necessárias.

    Args:
        settings (AppConfig): A instância de configuração do sistema a ser salvo.
        create_new (bool): Um booleano indicando se a configuração deve ser criado (True) ou atualizado (False).

    Returns:
        dict: Um dicionário contendo o status da operação, uma mensagem de sucesso ou erro e o ID da configuração.

    Raises:
        ValueError: Se houver um erro de validação ao salvar o settings.
        Exception: Se ocorrer um erro inesperado durante a operação.

    Exemplo:
        >>> settings = AppConfig(dfe_api_token="abc123", dfe_api_token_expires_in="AbC123Key", debug=True, timeout=30)
        >>> response = await handle_save_config(settings, create_new=True)
        >>> print(response)
    """
    response = {}

    try:
        # Usa o repositório do Firebase, para outro banco, apenas troque o repositório abaixo pelo novo.
        repository = FirebaseAppConfigRepository()
        settings_services = AppConfigServices(repository)

        operation = "criada" if create_new else "alterada"
        config_id = None

        if create_new:
            # Criar nova configuração
            config_id = settings_services.create(settings)
        else:
            # Alterar configuração existente
            config_id = settings_services.update(settings)

        response["status"] = "success"
        response["data"] = {"id": config_id, "message": f"Configuração {operation} com sucessso!"}

    except ValueError as e:
        response["status"] = "error"
        response["message"] = f"Erro de validação: {str(e)}"
        logger.error(response["message"])
    except Exception as e:
        response["status"] = "error"
        response["message"] = str(e)
        logger.error(response["message"])

    return response


def handle_get_config(config_id: str) -> dict:
    """
    Manipula a operação de buscar uma configuração.

    Esta função manipula a operação de buscar uma configuração no banco de dados utilizando o id fornecido.
    Ela utiliza um repositório específico para realizar a busca e retorna os detalhes da configuração, se encontrado.

    Args:
        config_id (str): O ID da configuração a ser buscado.

    Returns:
        dict: Um dicionário contendo o status da operação, uma mensagem de sucesso ou erro e os dados da configuração ou None.

    Raises:
        ValueError: Se houver um erro de validação ao buscar a configuração.
        Exception: Se ocorrer um erro inesperado durante a operação.

    Exemplo:
        >>> id = "Abc123adfEDK"
        >>> response = handle_get_config(id)
        >>> print(response)
    """
    response: dict = {}

    try:
        # Usa o repositório do Firebase para buscar a configuração
        repository = FirebaseAppConfigRepository()
        settings_services = AppConfigServices(repository)

        app_config = None

        # Busca configuração do sistema pelo config_id
        app_config = settings_services.find_config_by_id(config_id)

        if app_config:
            response["status"] = "success"
            response["data"] = {"settings": app_config, "message": "Configuração encontrada com sucesso!"}
        else:
            # Configuração não encontrada, obtem um novo token e cria uma nova config
            response["status"] = "error"
            response["message"] = "Configuração não encontrada"

    except ValueError as e:
        response["status"] = "error"
        response["message"] = f"Erro de validação: {str(e)}"
        logger.error(response["message"])
    except Exception as e:
        response["status"] = "error"
        response["message"] = str(e)
        logger.error(response["message"])

    return response
