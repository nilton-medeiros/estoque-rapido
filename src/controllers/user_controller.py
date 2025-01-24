from src.domain.models.user import User
from src.services.entities.user_service import UserService
from storage.data.firebase.firebase_user_repository import FirebaseUserRepository


async def handle_save_user(user: User, create_new: bool, password: str = None):
    '''
    Manipula a operação salvar usuário.
    '''
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


async def handle_get_user(email: str):
    '''
    Manipula a operação de buscar usuário (Controller).
    '''
    response = {
        "is_error": False,
        "message": "",
        "user": None
    }

    try:
        # Usa o repositório do Firebase para buscar o usuário
        repository = FirebaseUserRepository()
        user_service = UserService(repository)

        # Busca o usuário pelo email
        user = await user_service.find_user_by_email(email)

        if user:
            response["message"] = "Usuário encontrado com sucesso!"
            response["user"] = user
        else:
            response["is_error"] = True
            response["message"] = "Usuário não encontrado"

    except ValueError as e:
        response["is_error"] = True
        response["message"] = f"Erro de validação: {str(e)}"
    except Exception as e:
        response["is_error"] = True
        response["message"] = str(e)

    return response
