from typing import Optional
from src.domain.models.user import User
from storage.data.interfaces.user_repository import UserRepository


class UserService:
    '''
    Serviço de gerenciamento de usuários.

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
        """
        Envia dados do Usuário para o Repositório do database instânciado (repository) em user_controller.

        :param user: Instância do Usuário a salvar
        :return: ID do documento do Usuário salvo
        """
        # Verifica se já existe um usuário com este email
        existing_user = await self.repository.find_by_email(user.email)

        if existing_user:
            raise ValueError("Já existe um usuário com este email")

        # Envia para o repositório selecionado em user_controllrer salvar
        return await self.repository.save(user)

    async def update_user(self, user: User) -> User:
        # print("Debug: Entrou em update_user")
        if not user.id:
            raise ValueError("ID do usuário é necessário para atualização")
        return await self.repository.save(user)

    async def find_user_by_email(self, email: str) -> Optional[User]:
        """
        Encontra um usuário pelo email usando o repositório.

        Parâmetros:
            email (str): Email do usuário a ser encontrado

        Retorna:
            Optional[User]: Usuário encontrado ou None se não existir
        """
        return await self.repository.find_by_email(email)
