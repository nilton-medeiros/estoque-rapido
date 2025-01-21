from src.domain.models.user import User
from storage.data.interfaces.user_repository import UserRepository


class UserService:
    '''
    Serviço de gerenciamento de usuários.
    Atualiza o método create_user para salvar o novo usuário usando o repositório.

    Parâmetros:
        repository: (UserRepository)

    Proriedades:
        self.repository: (repository) Repositório recebido pelo parâmetro

    Métodos:
        create_user: Cria novo usuário no banco usando repositório
            Parâmetros:
                user: (User)
            Retorna: (User) Novo usuário criado

        update_user: Atualiza usuário no banco usando repositório
            Parâmetros:
                    user: (User)
                Retorna: (User) Usuário atualizado
    '''

    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def create_user(self, user: User) -> User:
        # print("Debug: Entrou em create_user")
        # Verifica se já existe um usuário com este email
        existing_user = await self.repository.find_by_email(user.email)
        if existing_user:
            raise ValueError("Já existe um usuário com este email")

        # Salva o novo usuário usando o repositório do banco de dados escolhido
        # em user_controller
        return await self.repository.save(user)

    async def update_user(self, user: User) -> User:
        # print("Debug: Entrou em update_user")
        if not user.id:
            raise ValueError("ID do usuário é necessário para atualização")
        return await self.repository.save(user)
