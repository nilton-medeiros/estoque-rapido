from src.domain.models.nome_pessoa import NomePessoa
from src.domain.models.phone_number import PhoneNumber
from src.domain.models.user import User
from src.services.user_service import UserService
from storage.data.firebase.firebase_user_repository import FirebaseUserRepository


async def handle_save_user(email: str, first_name: str, last_name: str, phone: str, profile: str, password: str):
    '''
    Manipula a operação salvar usuário (Controller).
    '''
    response = {
        "is_error": False,
        "message": "",
        "user": None
    }

    try:
        user = User(
            email=email,
            name=NomePessoa(first_name, last_name),
            phone_number=PhoneNumber(phone),
            profile=profile
        )

        # Usa o repositório do Firebase, para outro banco, apenas troque o repositório abaixo pelo novo.
        # print("Debug: Inicializando repositório Firebase...")
        repository = FirebaseUserRepository(password)
        user_service = UserService(repository)
        # print("Debug: Repositório e serviço inicializados")

        saved_user = await user_service.create_user(user)
        # print(f"Debug: saved_user {saved_user}")

        response["message"] = f"Usuário salvo com sucessso!"
        response["user"] = saved_user

    except ValueError as e:
        response["is_error"] = True
        response["message"] = f"Erro de validação: {str(e)}"
    except Exception as e:
        response["is_error"] = True
        response["message"] = str(e)

    return response
