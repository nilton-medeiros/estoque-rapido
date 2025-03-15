import logging

from src.domains.usuarios.models.usuario_model import Usuario
from src.domains.usuarios.repositories.implementations.firebase_usuarios_repository import FirebaseUsuariosRepository
from src.domains.usuarios.services.users_services import UsuariosServices

logger = logging.getLogger(__name__)


"""
Essa estrutura garante um controle claro de responsabilidades, onde usuarios_controller atua organizando
e redirecionando os dados ao repositório de dados.
Isso promove uma arquitetura mais limpa e modular, facilitando manutenção e escalabilidade do sistema.
"""

async def handle_save_usuarios(usuario: Usuario, create_new: bool, password: str = None) -> dict:
    """
    Manipula a operação de salvar usuário.

    Esta função manipula a operação de salvar um usuário no banco de dados, seja criando um novo
    usuário ou atualizando um existente. Ela utiliza um repositório específico para realizar as
    operações necessárias.

    Args:
        usuario (Usuario): A instância do usuário a ser salvo.
        create_new (bool): Um booleano indicando se o usuário deve ser criado (True) ou atualizado (False).

    Returns:
        dict: Um dicionário contendo o status da operação, uma mensagem de sucesso ou erro, e o ID do usuário.

    Raises:
        ValueError: Se houver um erro de validação ao salvar o usuário.
        Exception: Se ocorrer um erro inesperado durante a operação.

    Exemplo:
        >>> usuario = Usuario(name="Luis Alberto", email="luis.a@mail.com")
        >>> response = await handle_save_usuarios(usuario, create_new=True)
        >>> print(response)
    """
    response = {
        "is_error": False,
        "message": "",
        "id": None
    }

    try:
        # Usa o repositório do Firebase, para outro banco, apenas troque o repositório abaixo pelo novo.
        repository = FirebaseUsuariosRepository(password)
        usuarios_services = UsuariosServices(repository)

        operation = "criado" if create_new else "alterado"
        id = None

        if create_new:
            # Criar novo usuário
            id = await usuarios_services.create_usuario(usuario)
        else:
            # Alterar usuário existente
            id = await usuarios_services.update_usuario(usuario)

        response["message"] = f"Usuário {operation} com sucessso!"
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


async def handle_get_usuarios(id: str = None, email: str = None) -> dict:
    """
    Manipula a operação de buscar usuário.

    Esta função manipula a operação de buscar um usuário no banco de dados utilizando o email fornecido.
    Ela utiliza um repositório específico para realizar a busca e retorna os detalhes do usuário, se encontrado.

    Args:
        id (str): O ID do usuário a ser buscado. Se for None, verifica se é para buscar por email
        email (str): O email do usuário a ser buscado. Se for None, verifica se é para buscar por id

    Returns:
        dict: Um dicionário contendo o status da operação, uma mensagem de sucesso ou erro, e os dados do usuário ou None.

    Raises:
        ValueError: Se houver um erro de validação ao buscar o usuário.
        Exception: Se ocorrer um erro inesperado durante a operação.

    Exemplo:
        >>> email = "angelina.jolie@gmail.com"
        >>> response = await handle_get_usuarios(email)
        >>> print(response)
    """
    response = {
        "is_error": False,
        "message": "",
        "usuario": None
    }

    try:
        # Usa o repositório do Firebase para buscar o usuário
        repository = FirebaseUsuariosRepository()
        usuarios_services = UsuariosServices(repository)

        usuario = None

        if id:
            # Busca o usuário pelo id
            usuario = await usuarios_services.find_by_id(email)
        elif email:
            # Busca o usuário pelo email
            usuario = await usuarios_services.find_by_email(email)
        else: raise ValueError("Um dos argumentos id ou email deve ser passado")

        if usuario:
            response["message"] = "Usuário encontrado com sucesso!"
            response["usuario"] = usuario
        else:
            response["is_error"] = True
            response["message"] = "Usuário não encontrado"

    except ValueError as e:
        response["is_error"] = True
        response["message"] = f"Erro de validação: {str(e)}"
        logger.error(response["message"])
    except Exception as e:
        response["is_error"] = True
        response["message"] = str(e)
        logger.error(response["message"])

    return response


async def handle_update_photo_usuarios(id: str, photo: str) -> dict:
    """
    Update no campo photo do usuário.

    Esta função manipula a operação de atualizar um único campo 'photo' do usuário. Ela utiliza um repositório
    específico para realizar as operações necessárias.

    Args:
        id (str): ID do usuário.
        photo (str): String com o link ou path e nome da foto do usuário a ser atualizado.

    Returns:
        dict: Um dicionário contendo o status da operação, uma mensagem de sucesso ou erro, e o ID do usuário.

    Raises:
        ValueError: Se houver um erro de validação ao atualizar o campo photo do usuário.
        Exception: Se ocorrer um erro inesperado durante a operação.

    Exemplo:
        >>> id = '12345678901234567890123456789012'
        >>> response = await handle_update_field_usuarios(id, photo_url)
        >>> print(response)
    """
    response = {
        "is_error": False,
        "message": "",
        "usuario": None
    }

    try:
        # Usa o repositório do Firebase, para outro banco, apenas troque o repositório abaixo pelo novo.
        repository = FirebaseUsuariosRepository()
        usuarios_services = UsuariosServices(repository)

        # Atualiza o campo photo no usuário
        usuario = await usuarios_services.update_photo(id, photo)

        response["message"] = "Foto do Usuário atualizada com sucessso!"
        response["usuario"] = usuario

    except ValueError as e:
        response["is_error"] = True
        response["message"] = f"Erro de validação: {str(e)}"
        logger.error(response["message"])
    except Exception as e:
        response["is_error"] = True
        response["message"] = str(e)
        logger.error(response["message"])

    return response
