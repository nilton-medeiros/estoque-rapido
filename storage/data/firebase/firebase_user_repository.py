from typing import List, Optional

from firebase_admin import auth
from firebase_admin import firestore
from firebase_admin import exceptions

from src.domain.models.user import User
from src.domain.models.nome_pessoa import NomePessoa
from src.domain.models.phone_number import PhoneNumber
from src.utils.deep_translator import deepl_translator
from src.utils.field_validation_functions import get_first_and_last_name
from storage.data.interfaces.user_repository import UserRepository
from storage.data.firebase.firebase_initialize import get_firebase_app


# Repositório do Firebase, usa a classe abstrata UserRepositoy para forçar a implementação de métodos conforme contrato em UserRepository
class FirebaseUserRepository(UserRepository):
    '''
    Firebase user repository:
    Utiliza Google Authorization para autenticar e salvar os dados dos usuários.
    Nota: Esta classe Herda da classe abstrata UserRepository as especificações para
    implementar todos os métodos em conformidade com UserRepository.

    Args:
        password (str): Senha do usuário no Google Authorization
        db (firestore.Client): Objeto do Firestore

    Methods:
        count: Retorna o número total de usuários da empresa logada
        delete: Deleta um usuário do Firestore e do Google Authorization
        exists_by_email: Verifica se existe um usuário com o email especificado
        find_all: Busca todos os usuários da empresa logada
        find_by_email: Busca um usuário pelo email
        find_by_id: Busca um usuário pelo id
        find_by_name: Busca usuários da empresa logada que contenham o nome especificado
        find_by_profile: Busca um usuários por perfil
        save: Salva usuário no Google Authorization e no Firestore (inclui ou altera)
        update_profile: Atualiza o perfil de um usuário

    deepl_translator: Traduz os erros em inglês recebidos do Firebase para o português brasil
    '''

    def __init__(self, password: str):
        get_firebase_app()  # Inicializa o Firebase
        self.db = firestore.client()
        self.collection = self.db.collection('users')
        self.password = None

        if password is not None and password != "":
            self.password = password

    async def count(self, company_id: str) -> int:
        """
        Retorna o número total de usuários da empresa logada.

        Returns:
            int: Número total de usuários

        Raises:
            Exception: Em caso de erro na operação de banco de dados
        """
        try:
            query = self.collection.where('company_id', '==', company_id)
            docs = query.stream()
            count = 0
            for _ in docs:
                count += 1

            return count
        except Exception as e:
            # Lida com possíveis exceções, se necessário
            print(f"Erro ao contar usuários: {e}")
            raise e

    async def delete(self, id: str) -> None:
        """
        Deleta um usuário do Firestore e do Firebase Authentication.
        """
        try:
            # Deleta do Firebase Authentication
            auth.delete_user(id)

            # Deleta do Firestore
            self.collection.document(id).delete()
        except exceptions.FirebaseError as e:
            translated_error = deepl_translator(str(e))
            raise Exception(
                f"Erro ao deletar usuário com ID '{id}': {translated_error}")
        except Exception as e:
            raise Exception(
                f"Erro inesperado ao deletar usuário com ID '{id}': {str(e)}")

    async def exists_by_email(self, email: str) -> bool:
        """
        Verifica se existe um usuário com o email especificado.

        Args:
            email (str): Email a ser verificado

        Returns:
            bool: True se existe um usuário com o email, False caso contrário

        Raises:
            Exception: Em caso de erro na operação de banco de dados
        """
        try:
            query = self.collection.where('email', '==', email).limit(1)
            docs = query.stream()

            for doc in docs:
                return True
            return False
        except Exception as e:
            # Lida com possíveis exceções, se necessário
            print(f"Erro ao verificar se o usuário existe: {e}")
            return False

    async def find_all(self, company_id, limit: int = 100, offset: int = 0) -> List[User]:
        """
        Retorna uma lista paginada de usuários.

        Args:
            limit (int): Número máximo de registros a retornar
            offset (int): Número de registros a pular

        Returns:
            List[User]: Lista de usuários encontrados

        Raises:
            Exception: Em caso de erro na operação de banco de dados
        """
        try:
            query = self.collection.where(
                'company_id', '==', company_id).offset(offset).limit(limit)
            docs = query.stream()

            users = []
            for doc in docs:
                data = doc.to_dict()
                user = User(
                    id=doc.id,
                    email=data['email'],
                    name=NomePessoa(data['display_name']),
                    phone_number=PhoneNumber(data['phone_number']),
                    profile=data['profile']
                )
                users.append(user)

            return users
        except Exception as e:
            # Lida com possíveis exceções, se necessário
            print(f"Erro ao buscar usuários: {e}")
            raise e

    async def find_by_email(self, email: str) -> Optional[User]:
        try:
            query = self.collection.where('email', '==', email).limit(1)
            docs = query.stream()

            for doc in docs:
                data = doc.to_dict()
                first_name, last_name = get_first_and_last_name(
                    data['display_name'])
                return User(
                    id=doc.id,
                    email=data['email'],
                    name=NomePessoa(first_name, last_name),
                    phone_number=PhoneNumber(data['phone_number']),
                    profile=data['profile']
                )
            return None
        except exceptions.FirebaseError as e:
            translated_error = deepl_translator(str(e))
            raise Exception(
                f"Erro ao buscar usuário pelo email '{email}': {translated_error}")
        except Exception as e:
            raise Exception(
                f"Erro inesperado ao buscar usuário pelo email '{email}': {str(e)}")

    async def find_by_id(self, id: str) -> Optional[User]:
        """
        Busca um usuário pelo ID.

        Args:
            id (str): ID do usuário

        Returns:
            Optional[User]: Usuário encontrado ou None se não existir

        Raises:
            Exception: Em caso de erro na operação de banco de dados
        """
        try:
            doc = self.collection.document(id).get()
            if doc.exists:
                data = doc.to_dict()
                first_name, last_name = get_first_and_last_name(
                    data['display_name'])
                return User(
                    id=id,
                    email=data['email'],
                    name=NomePessoa(first_name, last_name),
                    phone_number=PhoneNumber(data['phone_number']),
                    profile=data['profile']
                )
            return None
        except exceptions.FirebaseError as e:
            translated_error = deepl_translator(str(e))
            raise Exception(
                f"Erro ao buscar usuário com ID '{id}': {translated_error}")
        except Exception as e:
            raise Exception(
                f"Erro inesperado ao buscar usuário com ID '{id}': {str(e)}")

    async def find_by_name(self, company_id, name: str) -> List[User]:
        """
        Busca usuários da empresa logada que contenham o nome especificado
        (primeiro nome ou sobrenome).

        Args:
            name (str): Nome ou parte do nome a ser buscado

        Returns:
            List[User]: Lista de usuários que correspondem à busca

        Raises:
            Exception: Em caso de erro na operação de banco de dados
        """
        try:
            query = self.collection.where('company_id', '==', company_id).where(
                'display_name', '>=', name).where('display_name', '<=', name + '\uf8ff')
            docs = query.stream()

            for doc in docs:
                data = doc.to_dict()
                first_name, last_name = get_first_and_last_name(
                    data['display_name'])
                return User(
                    id=doc.id,
                    email=data['email'],
                    name=NomePessoa(first_name, last_name),
                    phone_number=PhoneNumber(data['phone_number']),
                    profile=data['profile']
                )
            return None
        except exceptions.FirebaseError as e:
            translated_error = deepl_translator(str(e))
            raise Exception(
                f"Erro ao buscar usuário pelo nome '{name}': {translated_error}")
        except Exception as e:
            raise Exception(
                f"Erro inesperado ao buscar usuário pelo nome '{name}': {str(e)}")

    async def find_by_profile(self, company_id: str, profile: str) -> List[User]:
        """
        Busca usuários por perfil.

        Args:
            profile (str): Perfil a ser buscado

        Returns:
            List[User]: Lista de usuários com o perfil especificado

        Raises:
            Exception: Em caso de erro na operação de banco de dados
        """
        try:
            query = self.collection.where(
                'company_id', '==', company_id).where('profile', '==', profile)
            docs = query.stream()

            for doc in docs:
                data = doc.to_dict()
                first_name, last_name = get_first_and_last_name(
                    data['display_name'])
                return User(
                    id=doc.id,
                    email=data['email'],
                    name=NomePessoa(first_name, last_name),
                    phone_number=PhoneNumber(data['phone_number']),
                    profile=data['profile']
                )
            return None
        except exceptions.FirebaseError as e:
            translated_error = deepl_translator(str(e))
            raise Exception(
                f"Erro ao buscar usuário pelo perfil '{profile}': {translated_error}")
        except Exception as e:
            raise Exception(
                f"Erro inesperado ao buscar usuário pelo perfil '{profile}': {str(e)}")

    async def save(self, user: User) -> User:
        # print("Degub: Entrou em FirebaseUserRepository.save()")
        try:
            # Converte o objeto User para um dicionário que o Firestore aceita
            user_dict = {
                'email': user.email,
                'display_name': user.name.nome_completo,
                'phone_number': user.phone_number.get_e164(),
                'profile': user.profile
            }

            if user.id:
                # Update
                self.collection.document(user.id).set(user_dict)
            else:
                # 1. Criar usuário no Firebase Authentication
                user_db = auth.create_user(
                    email=user.email,
                    password=self.password,
                    display_name=user.name.nome_completo,
                    phone_number=user.phone_number.get_e164()
                )

                # 2. Cria usuário no Firestore
                user.id = user_db.uid
                doc_ref = self.db.collection('users').document(user.id)
                doc_ref.set(user_dict)

            return user
        except exceptions.FirebaseError as e:
            translated_error = deepl_translator(str(e))
            raise Exception(f"Erro ao salvar usuário: {translated_error}")
        except Exception as e:
            raise Exception(f"Erro inesperado ao salvar usuário: {str(e)}")

    async def update_profile(self, id: str, new_profile: str) -> Optional[User]:
        """
        Atualiza o perfil de um usuário.

        Args:
            id (str): ID do usuário
            new_profile (str): Novo perfil a ser atribuído

        Returns:
            Optional[User]: Usuário atualizado ou None se não existir

        Raises:
            Exception: Em caso de erro na operação de banco de dados
            ValueError: Se o novo perfil não for válido
        """

        try:
            # Verifica se o novo perfil é válido
            if not new_profile:
                raise ValueError("O novo perfil não pode ser vazio")

            doc_ref = self.collection.document(id)
            doc = doc_ref.get()

            if not doc.exists:
                return None

            # Atualiza o perfil do usuário
            doc_ref.update({"profile": new_profile})

            data = doc_ref.get().to_dict()
            first_name, last_name = get_first_and_last_name(
                data['display_name'])

            updated_user = User(
                id=doc.id,
                email=data['email'],
                name=NomePessoa(first_name, last_name),
                phone_number=PhoneNumber(data['phone_number']),
                profile=data['profile']
            )

            return updated_user
        except Exception as e:
            # Lida com possíveis exceções, se necessário
            print(f"Erro ao atualizar o perfil do usuário: {e}")
            raise e
