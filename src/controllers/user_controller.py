from src.domain.models.user import User
from src.services.entities.user_service import UserService
from storage.data.firebase.firebase_user_repository import FirebaseUserRepository

"""
Essa estrutura garante um controle claro de responsabilidades, onde user_controller atua organizando
e redirecionando os dados ao repositório de dados.
Isso promove uma arquitetura mais limpa e modular, facilitando manutenção e escalabilidade do sistema.
"""

async def handle_save_user(user: User, create_new: bool, password: str = None) -> dict:
    """
    Manipula a operação de salvar usuário.

    Esta função manipula a operação de salvar um usuário no banco de dados, seja criando uma novo
    usuário ou atualizando uma existente. Ela utiliza um repositório específico para realizar as
    operações necessárias.

    Args:
        user (User): A instância do usuário a ser salvo.
        create_new (bool): Um booleano indicando se o usuário deve ser criado (True) ou atualizado (False).

    Returns:
        dict: Um dicionário contendo o status da operação, uma mensagem de sucesso ou erro, e o ID do usuário.

    Raises:
        ValueError: Se houver um erro de validação ao salvar o usuário.
        Exception: Se ocorrer um erro inesperado durante a operação.

    Exemplo:
        >>> user = User(name="Luis Alberto", email="luis.a@mail.com")
        >>> response = await handle_save_user(user, create_new=True)
        >>> print(response)
    """
    response = {
        "is_error": False,
        "message": "",
        "user_id": None
    }

    try:
        # Usa o repositório do Firebase, para outro banco, apenas troque o repositório abaixo pelo novo.
        repository = FirebaseUserRepository(password)
        user_service = UserService(repository)

        operation = "criado" if create_new else "alterado"
        user_id = None

        if create_new:
            # Criar novo usuário
            user_id = await user_service.create_user(user)
        else:
            # Alterar usuário existente
            user_id = await user_service.update_user(user)

        response["message"] = f"Usuário {operation} com sucessso!"
        response["user_id"] = user_id

    except ValueError as e:
        response["is_error"] = True
        response["message"] = f"Erro de validação: {str(e)}"
    except Exception as e:
        response["is_error"] = True
        response["message"] = str(e)

    return response


async def handle_get_user(user_id: str = None, email: str = None) -> dict:
    """
    Manipula a operação de buscar usuário.

    Esta função manipula a operação de buscar um usuário no banco de dados utilizando o email fornecido.
    Ela utiliza um repositório específico para realizar a busca e retorna os detalhes do usuário, se encontrado.

    Args:
        user_id (str): O ID do usuário a ser buscado. Se for None, verifica se é para buscar por email
        email (str): O email do usuário a ser buscado. Se for None, verifica se é para buscar por user_id

    Returns:
        dict: Um dicionário contendo o status da operação, uma mensagem de sucesso ou erro, e os dados do usuário ou None.

    Raises:
        ValueError: Se houver um erro de validação ao buscar o usuário.
        Exception: Se ocorrer um erro inesperado durante a operação.

    Exemplo:
        >>> email = "angelina.jolie@gmail.com"
        >>> response = await handle_get_user(email)
        >>> print(response)
    """
    response = {
        "is_error": False,
        "message": "",
        "user": None
    }

    try:
        # Usa o repositório do Firebase para buscar o usuário
        repository = FirebaseUserRepository()
        user_service = UserService(repository)

        user = None

        if user_id:
            # Busca o usuário pelo user_id
            user = await user_service.find_by_id(email)
        elif email:
            # Busca o usuário pelo email
            user = await user_service.find_by_email(email)
        else: raise ValueError("Um dos argumentos user_id ou email deve ser passado")

        if user:
            response["message"] = "Usuário encontrado com sucesso!"
            response["user"] = user
        else:
            response["is_error"] = True
            response["message"] = "Usuário não encontrado"

    except ValueError as e:
        response["is_error"] = True
        response["message"] = f"Erro de validação: {str(e)}"
        print(":")
        print("================================================================================")
        print(f"Debug | ValueError: {response["message"]}")
        print("================================================================================")

    except Exception as e:
        response["is_error"] = True
        response["message"] = str(e)
        print(":")
        print("================================================================================")
        print(f"Debug | Exception: {response["message"]}")
        print("================================================================================")

    return response


async def handle_update_photo_user(user_id: str, photo: str) -> dict:
    """
    Update no campo photo do usuário.

    Esta função manipula a operação de atualizar um único campo 'photo' do usuário. Ela utiliza um repositório
    específico para realizar as operações necessárias.

    Args:
        user_id (str): ID do usuário.
        photo (str): String com o link ou path e nome da foto do usuário a ser atualizado.

    Returns:
        dict: Um dicionário contendo o status da operação, uma mensagem de sucesso ou erro, e o ID do usuário.

    Raises:
        ValueError: Se houver um erro de validação ao atualizar o campo photo do usuário.
        Exception: Se ocorrer um erro inesperado durante a operação.

    Exemplo:
        >>> user_id = '12345678901234567890123456789012'
        >>> response = await handle_update_field_user(user_id, photo_url)
        >>> print(response)
    """
    response = {
        "is_error": False,
        "message": "",
        "user": None
    }

    try:
        # Usa o repositório do Firebase, para outro banco, apenas troque o repositório abaixo pelo novo.
        repository = FirebaseUserRepository()
        user_service = UserService(repository)

        # Atualiza o campo photo no usuário
        user = await user_service.update_photo(user_id, photo)

        response["message"] = "Foto do Usuário atualizada com sucessso!"
        response["user"] = user

    except ValueError as e:
        response["is_error"] = True
        response["message"] = f"Erro de validação: {str(e)}"
    except Exception as e:
        response["is_error"] = True
        response["message"] = str(e)

    return response
