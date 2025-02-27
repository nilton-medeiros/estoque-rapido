import logging

from typing import List, Optional

from firebase_admin import auth
from firebase_admin import firestore
from firebase_admin import exceptions

from src.domain.models.nome_pessoa import NomePessoa
from src.domain.models.phone_number import PhoneNumber
from src.domain.models.user import User
from src.utils.deep_translator import deepl_translator
from src.utils.field_validation_functions import get_first_and_last_name
from storage.data.interfaces.user_repository import UserRepository
from storage.data.firebase.firebase_initialize import get_firebase_app

logger = logging.getLogger(__name__)


# Repositório do Firebase, usa a classe abstrata UserRepositoy para forçar a implementação de métodos conforme contrato em UserRepository
class FirebaseUserRepository(UserRepository):
    """
    Um repositório para gerenciar usuários utilizando o Firebase Firestore.

    Esta classe fornece métodos para realizar operações de CRUD em dados de usuários
    armazenados em um banco de dados Firestore.
    Utiliza Google Authorization para autenticação de usuarios.
    """

    def __init__(self, password: str = None):
        """
        Inicializa o cliente do Firebase Firestore e conecta-se à coleção 'users'.

        Garante que o aplicativo Firebase seja inicializado antes de criar o cliente Firestore.
        """
        get_firebase_app()

        self.db = firestore.client()
        self.collection = self.db.collection('users')
        self.password = None

        if password is not None and password != "":
            self.password = password

    async def count(self, company_id: str) -> int:
        """
        Contar o número total de usuários no banco de dados Firestore.

        Retorna:
            int: Número total de usuários da empresa logada.
        """
        try:
            query = self.collection.where(
                field_path='company_id', op_string='==', value=company_id)
            docs = query.stream()
            count = 0
            for _ in docs:
                count += 1

            return count
        except Exception as e:
            # Lida com possíveis exceções, se necessário
            logger.error(f"Erro ao contar usuários: {e}")
            raise e

    async def delete(self, user_id: str) -> None:
        """
        Excluir um usuário pelo seu identificador único do Firestore e também do Firebase Authentication.

        Args:
            user_id (str): O identificador único do usuário.

        Retorna:
            bool: True se a exclusão for bem-sucedida, False caso contrário.

        Levanta:
            Exception: Se ocorrer um erro no Firebase ou outro erro inesperado durante a exclusão.
        """
        try:
            # Deleta do Firebase Authentication
            auth.delete_user(user_id)

            # Deleta do Firestore
            self.collection.document(user_id).delete()
            return True
        except exceptions.FirebaseError as e:
            translated_error = deepl_translator(str(e))
            logger.error(f"Erro ao deletar usuário com id '{user_id}': {translated_error}")
            raise Exception(
                f"Erro ao deletar usuário com id '{user_id}': {translated_error}")
        except Exception as e:
            logger.error(f"Erro inesperado ao deletar usuário com id '{user_id}': {str(e)}")
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
            query = self.collection.where(
                field_path='email', op_string='==', value=email).limit(1)
            docs = query.stream()

            for doc in docs:
                return True
            return False
        except Exception as e:
            # Lida com possíveis exceções, se necessário
            logger.error(f"Erro ao verificar se o usuário existe: {e}")
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
                field_path='company_id', op_string='==', value=company_id).offset(offset).limit(limit)

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
            logger.error(f"Erro ao buscar usuários: {e}")
            raise e

    async def find_by_email(self, email: str) -> Optional[User]:
        """
        Encontrar um usuário pelo seu email.

        Args:
            email (str): O email do usuário a ser encontrado.

        Retorna:
            Optional[User]: Uma instância do usuário se encontrado, None caso contrário.

        Levanta:
            Exception: Se ocorrer um erro no Firebase ou outro erro inesperado durante a busca.
        """
        try:
            query = self.collection.where(
                field_path='email', op_string='==', value=email).limit(1)
            docs = query.stream()

            for doc in docs:
                user_data = doc.to_dict()
                user_data['id'] = doc.id
                return self._doc_to_user(user_data)

            return None
        except exceptions.FirebaseError as e:
            translated_error = deepl_translator(str(e))
            logger.error(f"Erro ao buscar usuário pelo email '{email}': {translated_error}")
            raise Exception(
                f"Erro ao buscar usuário pelo email '{email}': {translated_error}")
        except Exception as e:
            logger.error(f"Erro inesperado ao buscar usuário pelo email '{email}': {str(e)}")
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
            logger.error(f"Erro ao buscar usuário com ID '{id}': {translated_error}")
            raise Exception(
                f"Erro ao buscar usuário com ID '{id}': {translated_error}")
        except Exception as e:
            logger.error(f"Erro inesperado ao buscar usuário com ID '{id}': {str(e)}")
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
            query = self.collection.where(field_path='company_id', op_string='==', value=company_id).where(
                'display_name', '>=', name, '<=', name + '\uf8ff')

            docs = query.stream()

            for doc in docs:
                user_data = doc.to_dict()
                user_data['id'] = doc.id
                return self._doc_to_user(user_data)

            return None
        except exceptions.FirebaseError as e:
            translated_error = deepl_translator(str(e))
            logger.error(f"Erro ao buscar usuário pelo nome '{name}': {translated_error}")
            raise Exception(
                f"Erro ao buscar usuário pelo nome '{name}': {translated_error}")
        except Exception as e:
            logger.error(f"Erro inesperado ao buscar usuário pelo nome '{name}': {str(e)}")
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
            query = self.collection.where(field_path='company_id', op_string='==', value=company_id).where(
                field_path='profile', op_string='==', value=profile)
            docs = query.stream()

            for doc in docs:
                user_data = doc.to_dict()
                user_data["id"] = doc.id
                return self._doc_to_user(user_data)

            return None
        except exceptions.FirebaseError as e:
            translated_error = deepl_translator(str(e))
            logger.error(f"Erro ao buscar usuário pelo perfil '{profile}': {translated_error}")
            raise Exception(
                f"Erro ao buscar usuário pelo perfil '{profile}': {translated_error}")
        except Exception as e:
            logger.error(f"Erro inesperado ao buscar usuário pelo perfil '{profile}': {str(e)}")
            raise Exception(
                f"Erro inesperado ao buscar usuário pelo perfil '{profile}': {str(e)}")

    async def save(self, user: User) -> str:
        """
        Salvar um usuário no banco de dados Firestore.

        Se o usuário já existir pelo seu id, atualiza o documento existente em vez
        de criar um novo.

        Args:
            user (User): A instância do usuário a ser salvo.

        Retorna:
            str: O ID do documento do usuário salvo.
        """
        try:
            user_dict = self._user_to_dict(user)

            if user.id:
                # Update na coleção users, merge=True para não sobrescrever (remover) os campos não mencionados no user_dict
                self.collection.document(user.id).set(user_dict, merge=True)
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
                    # Cria um novo documento com o mesmo uid da Authentication
                    doc_ref = self.collection.document(user.id)
                    doc_ref.set(user_dict)  # Adiciona os demais campos
                else:
                    raise Exception("Password é necessário para criar usuário")

            return user.id
        except exceptions.FirebaseError as e:
            translated_error = deepl_translator(str(e))
            logger.error(f"Erro ao salvar usuário: {translated_error}")
            raise Exception(f"Erro ao salvar usuário: {translated_error}")
        except Exception as e:
            logger.error(f"Erro inesperado ao salvar usuário: {str(e)}")
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

            first_name, last_name = get_first_and_last_name(data['display_name'])
            companies: List[str] = data.get('companies', [])
            user_photo = str = data.get('photo', None)

            updated_user = User(
                id=doc.id,
                email=data['email'],
                name=NomePessoa(first_name, last_name),
                phone_number=PhoneNumber(data['phone_number']),
                profile=data['profile'],
                companies=companies,
                photo=user_photo,
            )

            return updated_user
        except Exception as e:
            # Lida com possíveis exceções, se necessário
            logger.error(f"Erro ao atualizar o perfil do usuário: {e}")
            raise e


    async def update_photo(self, id: str, new_photo: str) -> Optional[User]:
        """
        Atualiza a foto de um usuário.

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
            # Verifica se a nova foto é válido
            if not new_photo:
                raise ValueError("A nova foto não pode ser vazio")

            doc_ref = self.collection.document(id)
            doc = doc_ref.get()

            if not doc.exists:
                return None

            # Atualiza a foto do usuário
            doc_ref.update({"photo": new_photo})

            data = doc_ref.get().to_dict()

            first_name, last_name = get_first_and_last_name(data['display_name'])
            companies: List[str] = data.get('companies', [])
            user_photo: str = data.get('photo', None)

            updated_user = User(
                id=doc.id,
                email=data['email'],
                name=NomePessoa(first_name, last_name),
                phone_number=PhoneNumber(data['phone_number']),
                profile=data['profile'],
                companies=companies,
                photo=user_photo,
            )

            return updated_user
        except Exception as e:
            # Lida com possíveis exceções, se necessário
            logger.error(f"Erro ao atualizar o perfil do usuário: {e}")
            raise e

    def _doc_to_user(self, doc_data: dict) -> User:
        """
        Converter os dados de um documento do Firestore em uma instância de usuário.

        Args:
            doc_data (dict): Os dados do documento Firestore representando um usuário.

        Retorna:
            User: A instância correspondente do usuário.
        """

        from src.domain.models.nome_pessoa import NomePessoa
        from src.domain.models.phone_number import PhoneNumber

        # Recontruir campos opcionais
        first_name, last_name = get_first_and_last_name(
            doc_data['display_name'])
        companies: List[str] = doc_data.get('companies', [])
        user_photo: str = doc_data.get('photo', None)

        return User(
            id=doc_data['id'],
            email=doc_data['email'],
            name=NomePessoa(first_name, last_name),
            phone_number=PhoneNumber(doc_data['phone_number']),
            profile=doc_data['profile'],
            companies=companies,
            photo=user_photo,
        )

    def _user_to_dict(self, user: User) -> dict:
        """
        Converter uma instância de usuário em um dicionário para armazenamento no Firestore.

        Args:
            user (User): A instância de usuário a ser convertida.

        Retorna:
            dict: A representação do usuário em formato de dicionário.
        """
        # Não adicione id no user_dict, pois o Firebase providenciar um uid se não existir
        user_dict = {
            "email": user.email,
            "display_name": user.name.nome_completo,
            "phone_number": user.phone_number.get_e164(),
            "profile": user.profile,
            "companies": user.companies,
            "photo": user.photo,
        }

        return user_dict
