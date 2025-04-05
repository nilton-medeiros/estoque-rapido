import logging

from firebase_admin.auth import UserRecord

from src.domains.shared.password import Password
from src.domains.usuarios.models.usuario_model import Usuario
from src.domains.usuarios.repositories.implementations.firebase_usuarios_repository import FirebaseUsuariosRepository
from src.domains.usuarios.services.users_services import UsuariosServices

logger = logging.getLogger(__name__)


"""
Essa estrutura garante um controle claro de responsabilidades, onde usuarios_controller atua organizando
e redirecionando os dados ao repositório de dados.
Isso promove uma arquitetura mais limpa e modular, facilitando manutenção e escalabilidade do sistema.
"""


async def handle_login_usuarios(email: str, password: str) -> dict:
    response = {
        "is_error": False,
        "authenticated_user": None,
        "message": "",
    }

    try:
        # Usa o repositório do Firebase, para outro banco, apenas troque o repositório abaixo pelo novo.
        repository = FirebaseUsuariosRepository()
        usuarios_services = UsuariosServices(repository)
        authenticated_user: UserRecord = await usuarios_services.authentication(email, password)

        if authenticated_user:
            response["message"] = "Usuário autenticado com sucesso!"

            try:
                # Se usuário foi autenticado no Google Athentication, busca demais informações no Firestore
                user: Usuario = await usuarios_services.find_by_id(authenticated_user.id)

                if user:
                    if user.photo_url is None and authenticated_user.photo_url:
                        user.photo_url = authenticated_user.photo_url

                    user.password = Password(password)
                    user.disabled = authenticated_user.disabled
                    user.email_verified = authenticated_user.email_verified

                    response["authenticated_user"] = user
                else:
                    """
                    Esta é uma possibilidade remota, por alguma falha, o usuário está credenciado no Google Authentication,
                    mas não está no Firebase. Deleta do Google Authentication para uma novo credenciamento do usuário.
                    """
                    # ToDo: Tratar erros se houver ao deletar usuário
                    await usuarios_services.delete(authenticated_user.id)
                    response["is_error"] = True
                    response["message"] = "Usuário não encontrado"

            except Exception as e:
                response["is_error"] = True
                response["message"] = str(e)

        else:
            response["is_error"] = True
            response["message"] = "Credenciais inválidas"
    except ValueError as e:
        response["is_error"] = True
        response["message"] = f"Erro de validação: {str(e)}"
        logger.error(response["message"])
    except Exception as e:
        response["is_error"] = True
        response["message"] = str(e)

    return response


async def handle_save_usuarios(usuario: Usuario) -> dict:
    """
    Manipula a operação de salvar usuário.

    Esta função manipula a operação de salvar um usuário no banco de dados, seja criando um novo
    usuário ou atualizando um existente. Ela utiliza um repositório específico para realizar as
    operações necessárias.

    Args:
        usuario (Usuario): A instância do usuário a ser salvo.

    Returns:
        dict: Um dicionário contendo o status da operação, uma mensagem de sucesso ou erro, e o ID do usuário.

    Raises:
        ValueError: Se houver um erro de validação ao salvar o usuário.
        Exception: Se ocorrer um erro inesperado durante a operação.

    Exemplo:
        >>> usuario = Usuario(name="Luis Alberto", email="luis.a@mail.com")
        >>> response = await handle_save_usuarios(usuario)
        >>> print(response)
    """
    response = {
        "is_error": False,
        "message": "",
        "id": None
    }

    try:
        # Usa o repositório do Firebase, para outro banco, apenas troque o repositório abaixo pelo novo.
        repository = FirebaseUsuariosRepository()
        usuarios_services = UsuariosServices(repository)

        operation = "criado" if usuario.id else "alterado"
        id = None

        if usuario.id is None:
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
            usuario = await usuarios_services.find_by_id(id)
        elif email:
            # Busca o usuário pelo email
            usuario = await usuarios_services.find_by_email(email)
        else:
            raise ValueError("Um dos argumentos id ou email deve ser passado")

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


async def handle_update_photo_usuarios(id: str, photo_url: str) -> dict:
    """
    Update no campo photo_url do usuário.

    Esta função manipula a operação de atualizar um único campo 'photo_url' do usuário. Ela utiliza um repositório
    específico para realizar as operações necessárias.

    Args:
        id (str): ID do usuário.
        photo_url (str): String com o link ou path e nome da foto do usuário a ser atualizado.

    Returns:
        dict: Um dicionário contendo o status da operação, uma mensagem de sucesso ou erro, e o ID do usuário.

    Raises:
        ValueError: Se houver um erro de validação ao atualizar o campo photo_url do usuário.
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

        # Atualiza o campo photo_url no usuário
        usuario = await usuarios_services.update_photo(id, photo_url)

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


async def handle_update_color_usuarios(id: str, color: str) -> bool:
    """
    Update no campo color do usuário.

    Esta função manipula a operação de atualizar um único campo 'user_color' do usuário. Ela utiliza um repositório
    específico para realizar as operações necessárias.

    Args:
        id (str): ID do usuário.
        color (str): String com o nome da cor (const do flet como 'blue', 'orange') do usuário a ser atualizado.

    Returns:
        bool: True se user_color foi atualizado com sucesso, False caso contrário.

    Raises:
        ValueError: Se houver um erro de validação ao atualizar o campo user_color do usuário.
        Exception: Se ocorrer um erro inesperado durante a operação.

    Exemplo:
        >>> id = '12345678901234567890123456789012'
        >>> response = await handle_update_color_usuarios(id, 'blue')
        >>> print(response)
    """
    response = {
        "is_error": False,
        "message": "",
    }

    try:
        # Usa o repositório do Firebase, para outro banco, apenas troque o repositório abaixo pelo novo.
        repository = FirebaseUsuariosRepository()
        usuarios_services = UsuariosServices(repository)

        # Atualiza o campo color no usuário
        is_updated = await usuarios_services.update_color(id, color)
        response["is_error"] = not is_updated

        if is_updated:
            response["message"] = "Cor preferncial do Usuário atualizada com sucessso!"
        else:
            response["message"] = "Falha ao atualizar a cor preferncial do Usuário!"

    except ValueError as e:
        response["is_error"] = True
        response["message"] = f"Erro de validação: {str(e)}"
        logger.error(response["message"])
    except Exception as e:
        response["is_error"] = True
        response["message"] = str(e)
        logger.error(response["message"])

    return response
