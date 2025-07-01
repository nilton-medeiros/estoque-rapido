import logging
import os
from typing import Any
from dotenv import load_dotenv


from src.domains.shared.controllers.domain_exceptions import AuthenticationException, InvalidCredentialsException, UserNotFoundException
from src.domains.usuarios.models.usuarios_model import Usuario
from src.domains.shared import RegistrationStatus
from src.domains.usuarios.repositories.implementations.firebase_usuarios_repository import FirebaseUsuariosRepository
from src.domains.usuarios.services.usuarios_services import UsuariosServices
from src.services.emails.send_email import EmailAuthenticationError, EmailConnectionError, EmailMessage, EmailRecipientError, \
    EmailSendError, EmailValidationError, ModernEmailSender, create_email_config_from_env

logger = logging.getLogger(__name__)

"""
Essa estrutura garante um controle claro de responsabilidades, onde usuarios_controller atua organizando
e redirecionando os dados ao repositório de dados.
Isso promove uma arquitetura mais limpa e modular, facilitando manutenção e escalabilidade do sistema.
"""

def handle_login(email: str, password: str) -> dict[str, Any]:
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

def handle_change_password(user_id: str, new_password: str) -> dict[str, Any]:

    response: dict[str, Any] = {}

    try:
        repository = FirebaseUsuariosRepository()
        user_services = UsuariosServices(repository)

        if not user_id:
            raise ValueError("Usuário não pode ser nulo ou vazio")
        if not new_password:
            raise ValueError("Nova senha não pode ser nulo ou vazia")

        updated_pwd = user_services.change_password(user_id, new_password)

        if updated_pwd:
            response["status"] = "success"
            response["data"] = {"message": "Senha atualizada com sucesso!"}
        else:
            response["status"] = "error"
            response["message"] = "Falha ao atualizar senha"
    except ValueError as e:
        response["status"] = "error"
        response["message"] = f"Erro de validação: {str(e)}"
        logger.error(response["message"])
    except Exception as e:
        response["status"] = "error"
        response["message"] = str(e)

    return response


def handle_save(usuario: Usuario) -> dict[str, Any]:
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
        >>> response = handle_save(usuario)
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

def handle_update_photo(id: str, photo_url: str) -> dict[str, Any]:
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

def handle_update_user_colors(id: str, colors: dict[str, str]) -> dict[str, Any]:
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
        >>> response = handle_update_user_colors(id, {'base_color': 'deeporange', 'primary': '#FF5722', 'container': '#FFAB91', 'accent': '#FF6E40'})
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

def handle_update_user_companies(usuario_id: str, empresas: set, empresa_ativa_id: str|None = None) -> dict:
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
        >>> response = handle_update_user_companies(usuario_id, empresa_id, empresas)
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

def get_by_id_or_email(id: str | None = None, email: str | None = None) -> dict[str, Any]:
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
        >>> response = get_by_id_or_email(email)
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

def handle_get_all(empresa_id: str, status_deleted: bool = False) -> dict[str, Any]:
    """
    Busca todos os usuários da empresa logada que sejam ativa ou não, dependendo do status_active desejado.

    Esta função retorna todos os usuários da empresa logada, se não houver usuários, retorna uma lista vazia.
    Ela utiliza um repositório específico para realizar a busca e retorna a lista de usuários, se encontrada.

    Args:
        empresa_id (str): O ID da empresa para buscar os usuários.
        status_deleted (bool): True para usuários ativos e inativos, False para somente usuários deletados

    Returns (dict):
        is_error (bool): True se houve erro na operação, False caso contrário.
        message (str): Uma mensagem de sucesso ou erro.
        data (list): Uma lista de usuários da empresa logada ou [].
        deleted (int): Quantidade de usuários deletados (para o tooltip da lixeira).

    Raises:
        ValueError: Se houver um erro de validação ao buscar usuários.
        Exception: Se ocorrer um erro inesperado durante a operação.

    Exemplo:
        >>> response = handle_get_all(['abc123', 'def456'])
        >>> print(response)
    """

    response = {}

    try:
        # Usa o repositório do Firebase para buscar os usuarios
        repository = FirebaseUsuariosRepository()
        usuarios_services = UsuariosServices(repository)

        if not empresa_id:
            raise ValueError("ID da empresa logada não pode ser nulo ou vazio")
        usuarios_list, quantity = usuarios_services.get_all(empresa_id=empresa_id, status_deleted=status_deleted)

        response["status"] = "success"
        response["data"] = {
            "usuarios": usuarios_list if usuarios_list else [],
            "deleted": quantity if quantity else 0,
        }
    except ValueError as e:
        response["status"] = "error"
        response["message"] = f"usuarios_controllers.handle_get_all ValueError: Erro de validação: {str(e)}"
    except Exception as e:
        response["status"] = "error"
        response["message"] = str(e)

    return response

def handle_update_status(usuario: Usuario, logged_user: dict, status: RegistrationStatus) -> dict[str, Any]:
    """Manipula o status para ativo, inativo ou deletado de um usuário."""
    response = {}

    try:
        if not usuario:
            raise ValueError("Usuário não pode ser nulo ou vazio")
        if not isinstance(usuario, Usuario):
            raise ValueError("O argumento 'usuario' não é do tipo Usuario")
        if not usuario.id:
            raise ValueError("ID do usuário não pode ser nulo ou vazio")
        if not status:
            raise ValueError("Status não pode ser nulo ou vazio")
        if not isinstance(status, RegistrationStatus):
            raise ValueError("Status não é do tipo RegistrationStatus")

        repository = FirebaseUsuariosRepository()
        usuarios_services = UsuariosServices(repository)

        is_updated = usuarios_services.update_status(usuario, logged_user, status)
        operation = "ativado" if status == RegistrationStatus.ACTIVE else "inativado" if status == RegistrationStatus.INACTIVE else "marcado como excluído"

        if is_updated:
            response["status"] = "success"
            response["data"] = status
            response["message"] = f"Usuário {operation} com sucesso!"
        else:
            response["status"] = "error"
            response["message"] = f"Não foi possível atualizar o status do usuario para {str(status)}"

    except ValueError as e:
        response["status"] = "error"
        response["message"] = f"Erro de validação: {str(e)}"
        logger.error("usuarios_controllers.handle_update_status(ValueError). " + response["message"])
    except Exception as e:
        response["status"] = "error"
        response["message"] = str(e)
        logger.error(response["message"])

    return response

def send_mail_password(usuario: Usuario) -> dict[str, Any]:
    load_dotenv()
    URL_LOGIN = os.environ.get("URL_LOGIN", "")

    try:
        if not usuario:
            raise ValueError("Usuário não pode ser nulo ou vazio")
        if not isinstance(usuario, Usuario):
            raise ValueError("Usuario não é do tipo Usuario")
        if not usuario.id:
            raise ValueError("ID da usuario não pode ser nulo ou vazio")

        config = create_email_config_from_env()
        email_sender = ModernEmailSender(config)
        senha_temp = usuario.password.decrypted # Acessa a property diretamente

        # 1. Enviar email de forma síncrona
        mensagem = EmailMessage(
            subject="🔑 Sua senha temporária - Ação Necessária",
            recipients=[usuario.email],
            body_html=f"""
            <h2>Bem-vindo ao sistema Estoque Rápido!</h2>
            <p>Sua senha temporária é: <strong>{senha_temp}</strong></p>
            <p><strong>⚠️ IMPORTANTE:</strong> Troque sua senha no primeiro login!</p>
            <a href="{URL_LOGIN}">Fazer Login Agora</a>
            """
        )

        resultado = email_sender.send_email_sync_direct(mensagem)

        if resultado['success']:
            # 2. Só marca como "email enviado" se confirmou envio
            # ToDo: marcar_usuario_email_enviado(usuario.id)
            return {"success": True, "message": "Usuário criado e email enviado"}
        else:
            # 3. Se email falhou, pode reverter ou tentar novamente
            return {"success": False, "error": "Usuário criado mas email falhou"}

    except EmailValidationError as e:
        # Erros de validação - dados incorretos
        print(f"❌ Erro de validação: {e}")
        if e.field == "email_format":
            return {"success": False, "error": "Email inválido", "user_message": "Verifique o email digitado"}
        elif e.field == "subject":
            return {"success": False, "error": "Assunto inválido", "user_message": "Erro interno, tente novamente"}
        else:
            return {"success": False, "error": str(e), "user_message": "Dados inválidos"}

    except EmailAuthenticationError as e:
        # Problema de configuração do servidor
        print(f"🔐 Erro de autenticação: {e}")
        return {"success": False, "error": "Erro de configuração", "user_message": "Falha temporária, tente novamente"}

    except EmailConnectionError as e:
        # Problema de rede/servidor
        print(f"🌐 Erro de conexão: {e}")
        return {"success": False, "error": "Erro de conexão", "user_message": "Servidor indisponível, tente novamente"}

    except EmailRecipientError as e:
        # Email do destinatário rejeitado
        print(f"📧 Erro de destinatário: {e}")
        return {"success": False, "error": "Email rejeitado", "user_message": f"Email inválido: {', '.join(e.invalid_emails)}"}

    except EmailSendError as e:
        # Outros erros de envio
        print(f"📤 Erro de envio: {e}")

        if e.error_type == "QUOTA_EXCEEDED":
            return {"success": False, "error": "Cota excedida", "user_message": "Limite de emails atingido, tente mais tarde"}
        elif e.error_type == "SPAM_REJECTED":
            return {"success": False, "error": "Spam detectado", "user_message": "Email rejeitado, entre em contato conosco"}
        else:
            return {"success": False, "error": str(e), "user_message": "Falha no envio, tente novamente"}

    except Exception as e:
        # Qualquer outro erro não previsto
        print(f"💥 Erro inesperado: {e}")
        return {"success": False, "error": "Erro inesperado", "user_message": "Erro interno, entre em contato com suporte"}
