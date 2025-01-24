from typing import List, Optional

from firebase_admin import auth
from firebase_admin import firestore
from firebase_admin import exceptions

from src.domain.models.user import User
from src.utils.deep_translator import deepl_translator
from src.utils.field_validation_functions import get_first_and_last_name
from storage.data.interfaces.user_repository import UserRepository
from storage.data.firebase.firebase_initialize import get_firebase_app


# Repositório do Firebase, usa a classe abstrata UserRepositoy para forçar a implementação de métodos conforme contrato em UserRepository
class FirebaseUserRepository(UserRepository):
    """
    Implementação de UserRepository usando Firebase Firestore.
    Utiliza Google Authorization para autenticar e salvar os dados dos usuários.
    """

    def __init__(self, password: str = None):
        get_firebase_app()  # Inicializa o Firebase
        self.db = firestore.client()
        self.collection = self.db.collection('users')
        self.password = None

        if password is not None and password != "":
            self.password = password

    async def count(self, company_id: str) -> int:
        """Retorna o número total de usuários da empresa logada."""
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

    async def delete(self, user_id: str) -> None:
        """
        Deleta um usuário do Firestore e do Firebase Authentication.
        """
        try:
            # Deleta do Firebase Authentication
            auth.delete_user(user_id)

            # Deleta do Firestore
            self.collection.document(user_id).delete()
            return True
        except exceptions.FirebaseError as e:
            translated_error = deepl_translator(str(e))
            raise Exception(
                f"Erro ao deletar usuário com id '{user_id}': {translated_error}")
        except Exception as e:
            raise Exception(
                f"Erro inesperado ao deletar usuário com id '{user_id}': {str(e)}")

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
                user_data = doc.to_dict()
                user_data['id'] = doc.id
                user = self._doc_to_user(user_data)
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
                user_data = doc.to_dict()
                user_data['id'] = doc.id
                return self._doc_to_user(user_data)

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
                user_data = doc.to_dict()
                user_data['id'] = doc.id
                return self._doc_to_user(user_data)
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
                user_data = doc.to_dict()
                user_data['id'] = doc.id
                return self._doc_to_user(user_data)

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
                user_data = doc.to_dict()
                user_data["id"] = doc.id
                return self._doc_to_user(user_data)

            return None
        except exceptions.FirebaseError as e:
            translated_error = deepl_translator(str(e))
            raise Exception(
                f"Erro ao buscar usuário pelo perfil '{profile}': {translated_error}")
        except Exception as e:
            raise Exception(
                f"Erro inesperado ao buscar usuário pelo perfil '{profile}': {str(e)}")

    async def save(self, user: User) -> User:
        """
        Salvar um usuário no Firestore.

        :param user: Instância do Usuário a salvar
        :return: ID do documento do usuário salvo
        """

        try:
            user_dict = self._user_to_dict(user)

            if user.id:
                # Update na coleção users
                self.collection.document(user.id).set(user_dict)
            else:

                if self.password:
                    # 1. Criar usuário no Firebase Authentication
                    user_db = auth.create_user(
                        email=user.email,
                        password=self.password,
                        display_name=user.name.nome_completo,
                        phone_number=user.phone_number.get_e164()
                    )

                    # 2. Obtem o uid do usuário Credenciado e Autenticado e insere o uid em user.id e cria usuário no Firestore
                    user.id = user_db.uid
                    doc_ref = self.db.collection('users').document(user.id)  # Cria um novo documento com o mesmo uid da Authentication
                    doc_ref.set(user_dict)  # Adiciona os demais campos
                else:
                    raise Exception("Password é necessário para criar usuário")

            return user.id
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

    def _doc_to_user(self, doc_data: dict) -> User:
        """Converte dados de documento do Firebase para instância de Usuário"""

        from src.domain.models.nome_pessoa import NomePessoa
        from src.domain.models.phone_number import PhoneNumber

        # Recontruir campos opcionais
        first_name, last_name = get_first_and_last_name(doc_data['display_name'])
        companies: List[str] = doc_data.get('companies', [])

        return User(
            id=doc_data['id'],
            email=doc_data['email'],
            name=NomePessoa(first_name, last_name),
            phone_number=PhoneNumber(doc_data['phone_number']),
            profile=doc_data['profile'],
            companies=companies,
        )

    def _user_to_dict(self, user: User) -> dict:
        """
        Converter instância de Usuário para dicionário para armazenamento no Firestore.

        :param user: Instância do Ususário
        :return: Representação em dicionário do usuário
        """
        # Não adicionar o id no user_dict, pois o Firebase criará se não existir
        user_dict = {
            "email": user.email,
            "display_name": user.name.nome_completo,
            "phone_number": user.phone_number.get_e164,
            "profile": user.profile,
            "companies": user.companies,
        }

        return user_dict
