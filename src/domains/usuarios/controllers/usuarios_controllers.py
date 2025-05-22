import logging
from typing import Any


from src.domains.shared.domain_exceptions import AuthenticationException, InvalidCredentialsException, UserNotFoundException
from src.domains.usuarios.models.usuario_model import Usuario
from src.domains.usuarios.repositories.implementations.firebase_usuarios_repository import FirebaseUsuariosRepository
from src.domains.usuarios.services.usuarios_services import UsuariosServices

logger = logging.getLogger(__name__)


"""
Essa estrutura garante um controle claro de responsabilidades, onde usuarios_controller atua organizando
e redirecionando os dados ao repositório de dados.
Isso promove uma arquitetura mais limpa e modular, facilitando manutenção e escalabilidade do sistema.
"""


def handle_login_usuarios(email: str, password: str) -> dict[str, Any]:
    response: dict[str, Any] = {}

    try:
        # Usa o repositório do Firebase, para outro banco, apenas troque o repositório abaixo pelo novo.
        repository = FirebaseUsuariosRepository()
        usuarios_services = UsuariosServices(repository)
        user = usuarios_services.authentication(email=email, password=password)

        response["status"] = "success"
        response["data"] = {
            "authenticated_user": user,
            "message": "Usuário autenticado com sucesso!"
        }


    except UserNotFoundException as e:
        response["status"] = "error"
        response["message"] = str(e)

    except InvalidCredentialsException as e:
        response["status"] = "error"
        # str(e) # Não deve ser exposto para o usuário, mensagem genérica
        response["message"] = "Credenciais inválidas"

    except AuthenticationException as e:
        response["status"] = "error"
        response["message"] = str(e)

    except Exception as e:
        response["status"] = "error"
        response["message"] = f"Erro interno do servidor: {str(e)}"

    return response


def handle_save_usuarios(usuario: Usuario) -> dict[str, Any]:
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
        >>> response = handle_save_usuarios(usuario)
        >>> print(response)
    """
    response: dict[str, Any] = {}

    try:
        # Usa o repositório do Firebase, para outro banco, apenas troque o repositório abaixo pelo novo.
        repository = FirebaseUsuariosRepository()
        usuarios_services = UsuariosServices(repository)

        operation = "atualizado"
        id = None

        if usuario.id:
            # Alterar usuário existente
            id = usuarios_services.update(usuario)
        else:
            # Criar novo usuário
            operation = "criado"
            id = usuarios_services.create(usuario)

        response["status"] = "success"
        response["data"] = {"id": id, "message": f"Usuário {operation} com sucessso!"}

    except ValueError as e:
        response["status"] = "error"
        response["message"] = f"Erro de validação: {str(e)}"
    except Exception as e:
        response["status"] = "error"
        response["message"] = str(e)

    return response


def handle_get_usuarios(id: str | None = None, email: str | None = None) -> dict[str, Any]:
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
        >>> response = handle_get_usuarios(email)
        >>> print(response)
    """
    response: dict[str, Any] = {}

    # Verifica se o id ou email foram passados
    if not id and not email:
        response["status"] = "error"
        response["message"] = "Um dos argumentos id ou email deve ser passado"
        logger.warning(response["message"])
        return response

    try:
        # Usa o repositório do Firebase para buscar o usuário
        repository = FirebaseUsuariosRepository()
        usuarios_services = UsuariosServices(repository)

        usuario = None

        if id:
            usuario = usuarios_services.find_by_id(id)
        elif email:
            usuario = usuarios_services.find_by_email(email)

        if usuario:
            response["status"] = "success"
            response["data"] = {"usuario": usuario, "message": "Usuário encontrado com sucesso!"}
        else:
            response["status"] = "error"
            response["message"] = f"Usuário não encontrado. Verifique o id ou email: {id or email}"

    except ValueError as e:
        response["status"] = "error"
        response["message"] = f"Erro de validação: {str(e)}"
        logger.error(response["message"])
    except Exception as e:
        response["status"] = "error"
        response["message"] = str(e)
        logger.error(response["message"])

    return response


def handle_update_photo_usuarios(id: str, photo_url: str) -> dict[str, Any]:
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
        >>> response = handle_update_field_usuarios(id, photo_url)
        >>> print(response)
    """
    response: dict[str, Any] = {}

    try:
        # Usa o repositório do Firebase, para outro banco, apenas troque o repositório abaixo pelo novo.
        repository = FirebaseUsuariosRepository()
        usuarios_services = UsuariosServices(repository)

        # Atualiza o campo photo_url no usuário
        usuario = usuarios_services.update_photo(id, photo_url)

        response["status"] = "success"
        response["data"] = {"usuario": usuario, "message": "Foto do Usuário atualizada com sucesso!"}


    except ValueError as e:
        response["status"] = "error"
        response["message"] = f"Erro de validação: {str(e)}"
        logger.error(response["message"])
    except Exception as e:
        response["status"] = "error"
        response["message"] = str(e)

    return response


def handle_update_colors_usuarios(id: str, colors: dict[str, str]) -> dict[str, Any]:
    """
    Update no campo colors do usuário.

    Esta função manipula a operação de atualizar um único campo 'user_colors' do usuário. Ela utiliza um repositório
    específico para realizar as operações necessárias.

    Args:
        id (str): ID do usuário.
        colors (str): String com o nome da cor (const do flet como 'blue', 'orange') do usuário a ser atualizado.

    Returns:
        bool: True se user_colors foi atualizado com sucesso, False caso contrário.

    Raises:
        ValueError: Se houver um erro de validação ao atualizar o campo user_colors do usuário.
        Exception: Se ocorrer um erro inesperado durante a operação.

    Exemplo:
        >>> id = '12345678901234567890123456789012'
        >>> response = handle_update_colors_usuarios(id, {'base_color': 'deeporange', 'primary': '#FF5722', 'container': '#FFAB91', 'accent': '#FF6E40'})
        >>> print(response)
    """
    response: dict[str, Any] = {}

    # Verifica se o id ou colors foram passados
    if not id or not colors:
        response["status"] = "error"
        response["message"] = "Um dos argumentos id ou colors deve ser passado"
        logger.warning(response["message"])
        return response

    # Verifica se colors é um dicionário e contém os campos corretos
    if not all(key in colors for key in ['base_color', 'primary', 'container', 'accent']):
        response["status"] = "error"
        response["message"] = "O argumento color deve ser um dicionário com os campos 'base_color', 'primary', 'container' e 'accent'"
        logger.warning(response["message"])
        return response

    try:
        # Usa o repositório do Firebase, para outro banco, apenas troque o repositório abaixo pelo novo.
        repository = FirebaseUsuariosRepository()
        usuarios_services = UsuariosServices(repository)

        # Atualiza o campo color no usuário
        is_updated = usuarios_services.update_colors(id, colors)

        if is_updated:
            response["status"] = "success"
            response["data"] = {"message": "Cor preferncial do Usuário atualizada com sucessso!"}
        else:
            response["status"] = "error"
            response["message"] = "Falha ao atualizar a cor preferncial do Usuário!"

    except ValueError as e:
        response["status"] = "error"
        response["message"] = f"Erro de validação: {str(e)}"
        logger.error(response["message"])
    except Exception as e:
        response["status"] = "error"
        response["message"] = str(e)

    return response


def handle_update_empresas_usuarios(usuario_id: str, empresas: set, empresa_ativa_id: str|None = None) -> dict:
    """
    Update nos campos empresa_id e empresas do usuário.

    Args:
        usuario_id (str): ID do usuário.
        empresa_id (str): ID da empresa ativa.
        empresas (set): Conjunto de empresas associada ao usuário.

    Returns:
        response (dict): Dicionário contendo is_error e uma mensagem.

    Raises:
        ValueError: Se houver um erro de validação ao atualizar usuário.
        Exception: Se ocorrer um erro inesperado durante a operação.

    Exemplo:
        >>> usuario_id = '12345678901234567890123456789012'
        >>> empresa_id = '12345678901234567890123456789012'
        >>> empresas = {'12345678901234567890123456789012', '12345678901234567890123456789012'}
        >>> response = handle_update_empresas_usuarios(usuario_id, empresa_id, empresas)
        >>> print(response)
    """
    response = {}

    # Verifica se o id e empresas foram passados
    if not usuario_id or empresas is None:
        response["status"] = "error"
        msg = f"Os argumentos usuario_id e empresas devem ser passados. usuario_id: {usuario_id}, empresas: {empresas}"
        response["message"] = msg
        logger.error(msg)

    try:
        # Usa o repositório do Firebase, para outro banco, apenas troque o repositório abaixo pelo novo.
        repository = FirebaseUsuariosRepository()
        usuarios_services = UsuariosServices(repository)

        # Atualiza o campo color no usuário
        is_updated = usuarios_services.update_empresas(usuario_id=usuario_id, empresas=empresas, empresa_id=empresa_ativa_id)

        if is_updated:
            response["status"] = "success"
            response["data"] = {"message": "Empresa(s) do Usuário atualizada com sucessso!"}
        else:
            response["status"] = "error"
            response[
                "message"] = f"Falha ao atualizar empresa(s) do Usuário: Usuário não encontrado com ID {usuario_id}"
            logger.error(response["message"])
    except ValueError as e:
        response["status"] = "error"
        response["message"] = f"Erro de validação: {str(e)}"
        logger.error(response["message"])
    except Exception as e:
        response["is_error"] = True
        response["message"] = str(e)
        logger.error(response["message"])

    return response


def handle_find_all_usuarios(empresa_id: str) -> dict[str, Any]:
    """Busca todos os usuário da empresa_id"""
    # Exemplo de tipagem profunda: dict[str, bool|str|list[Usuario|None]]. Esta é mais simples: dict[str, Any]
    response: dict[str, Any] = {}

    # Verifica se o id da empresa foi passado.
    if not empresa_id:
        response["status"] = "error"
        response["message"] = "O ID da empresa deve ser passado"
        logger.warning(response["message"])
        return response

    try:
        # Usa o repositório do Firebase para buscar o usuário
        repository = FirebaseUsuariosRepository()
        usuarios_services = UsuariosServices(repository)

        usuarios = usuarios_services.find_all(empresa_id)

        if len(usuarios) > 0:
            # Retorna lista de usuários
            response["status"] = "success"
            response["data"] = {"usuarios": usuarios, "message": "Usuários encontrados com sucesso!"}
        else:
            response["status"] = "error"
            response[
                "message"] = f"Usuários não encontrados. Verifique o empresa_id: {empresa_id}"

    except ValueError as e:
        response["status"] = "error"
        response["message"] = f"Erro de validação: {str(e)}"
        logger.error(response["message"])
    except Exception as e:
        response["status"] = "error"
        response["message"] = str(e)
        logger.error(response["message"])

    return response
