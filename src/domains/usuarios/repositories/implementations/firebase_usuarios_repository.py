import logging

from typing import List, Optional

from firebase_admin import auth
from firebase_admin import firestore
from firebase_admin import exceptions

from src.domains.shared import NomePessoa, PhoneNumber
from src.domains.usuarios.models.usuario_model import Usuario
from src.domains.usuarios.repositories.contracts.usuarios_repository import UsuariosRepository
from src.shared import deepl_translator, get_first_and_last_name
from storage.data.firebase.firebase_initialize import get_firebase_app

logger = logging.getLogger(__name__)


# Repositório do Firebase, usa a classe abstrata UsuariosRepositoy para forçar a implementação de métodos conforme contrato em UsuariosRepository
class FirebaseUsuariosRepository(UsuariosRepository):
    """
    Um repositório para gerenciar usuários utilizando o Firebase Firestore.

    Esta classe fornece métodos para realizar operações de CRUD em dados de usuários
    armazenados em um banco de dados Firestore.
    Utiliza Google Authorization para autenticação de usuarios.
    """

    def __init__(self, password: str = None):
        """
        Inicializa o cliente do Firebase Firestore e conecta-se à coleção 'usuarios'.

        Garante que o aplicativo Firebase seja inicializado antes de criar o cliente Firestore.
        """
        get_firebase_app()

        self.db = firestore.client()
        self.collection = self.db.collection('usuarios')
        self.password = None

        if password is not None and password != "":
            self.password = password

    async def count(self, empresa_id: str) -> int:
        """
        Conta o número de usuários que possuem um empresa_id específico no campo 'empresas'.

        Args:
            empresa_id (str): O ID da empresa a ser buscado.

        Returns:
            int: O número de usuários encontrados.
        """
        try:
            query = self.collection.where(
                field_path='empresas', op_string='array_contains', value=empresa_id)
            docs = query.get()
            return len(docs)
        except Exception as e:
            logging.error(f"Erro ao contar usuários: {e}")
            raise e

    async def delete(self, usuario_id: str) -> None:
        """
        Excluir um usuário pelo seu identificador único do Firestore e também do Firebase Authentication.

        Args:
            usuario_id (str): O identificador único do usuário.

        Retorna:
            bool: True se a exclusão for bem-sucedida, False caso contrário.

        Levanta:
            Exception: Se ocorrer um erro no Firebase ou outro erro inesperado durante a exclusão.
        """
        try:
            # Deleta do Firebase Authentication
            auth.delete_usuario(usuario_id)

            # Deleta do Firestore
            self.collection.document(usuario_id).delete()
            return True
        except exceptions.FirebaseError as e:
            translated_error = deepl_translator(str(e))
            logger.error(f"Erro ao deletar usuário com id '{usuario_id}': {translated_error}")
            raise Exception(
                f"Erro ao deletar usuário com id '{usuario_id}': {translated_error}")
        except Exception as e:
            logger.error(f"Erro inesperado ao deletar usuário com id '{usuario_id}': {str(e)}")
            raise Exception(
                f"Erro inesperado ao deletar usuário com id '{usuario_id}': {str(e)}")

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

    async def find_all(self, empresa_id, limit: int = 100, offset: int = 0) -> List[Usuario]:
        """
        Retorna uma lista paginada de usuários.

        Args:
            limit (int): Número máximo de registros a retornar
            offset (int): Número de registros a pular

        Returns:
            List[Usuario]: Lista de usuários encontrados

        Raises:
            Exception: Em caso de erro na operação de banco de dados
        """
        try:
            query = self.collection.where(
                field_path='empresas', op_string='array_contains', value=empresa_id).offset(offset).limit(limit)

            docs = query.stream()

            usuarios = []
            for doc in docs:
                usuario_data = doc.to_dict()
                usuario_data['id'] = doc.id
                usuario = self._doc_to_usuario(usuario_data)
                usuarios.append(usuario)

            return usuarios
        except Exception as e:
            # Lida com possíveis exceções, se necessário
            logger.error(f"Erro ao buscar usuários: {e}")
            raise e

    async def find_by_email(self, email: str) -> Optional[Usuario]:
        """
        Encontrar um usuário pelo seu email.

        Args:
            email (str): O email do usuário a ser encontrado.

        Retorna:
            Optional[Usuario]: Uma instância do usuário se encontrado, None caso contrário.

        Levanta:
            Exception: Se ocorrer um erro no Firebase ou outro erro inesperado durante a busca.
        """
        try:
            query = self.collection.where(
                field_path='email', op_string='==', value=email).limit(1)
            docs = query.stream()

            for doc in docs:
                usuario_data = doc.to_dict()
                usuario_data['id'] = doc.id
                return self._doc_to_usuario(usuario_data)

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

    async def find_by_id(self, id: str) -> Optional[Usuario]:
        """
        Busca um usuário pelo ID.

        Args:
            id (str): ID do usuário

        Returns:
            Optional[Usuario]: Usuário encontrado ou None se não existir

        Raises:
            Exception: Em caso de erro na operação de banco de dados
        """
        try:
            doc = self.collection.document(id).get()
            if doc.exists:
                usuario_data = doc.to_dict()
                usuario_data['id'] = doc.id
                return self._doc_to_usuario(usuario_data)
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

    async def find_by_name(self, empresa_id, name: str) -> List[Usuario]:
        """
        Busca usuários da empresa logada que contenham o nome especificado

        Args:
            name (str): Nome ou parte do nome a ser buscado

        Returns:
            List[Usuario]: Lista de usuários que correspondem à busca

        Raises:
            Exception: Em caso de erro na operação de banco de dados
        """
        try:
            query = self.collection.where(field_path='empresas', op_string='array_contains', value=empresa_id).where(
                'display_name', '>=', name, '<=', name + '\uf8ff')

            docs = query.stream()

            for doc in docs:
                usuario_data = doc.to_dict()
                usuario_data['id'] = doc.id
                return self._doc_to_usuario(usuario_data)

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

    async def find_by_profile(self, empresa_id: str, profile: str) -> List[Usuario]:
        """
        Busca usuários por perfil.

        Args:
            profile (str): Perfil a ser buscado

        Returns:
            List[Usuario]: Lista de usuários com o perfil especificado

        Raises:
            Exception: Em caso de erro na operação de banco de dados
        """
        try:
            query = self.collection.where(field_path='empresas', op_string='array_contains', value=empresa_id).where(
                field_path='profile', op_string='==', value=profile)
            docs = query.stream()

            for doc in docs:
                usuario_data = doc.to_dict()
                usuario_data["id"] = doc.id
                return self._doc_to_usuario(usuario_data)

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

    async def save(self, usuario: Usuario) -> str:
        """
        Salvar um usuário no banco de dados Firestore.

        Se o usuário já existir pelo seu id, atualiza o documento existente em vez
        de criar um novo.

        Args:
            usuario (Usuario): A instância do usuário a ser salvo.

        Retorna:
            str: O ID do documento do usuário salvo.
        """
        try:
            usuario_dict = self._usuario_to_dict(usuario)

            if usuario.id:
                # Update na coleção usuarios, merge=True para não sobrescrever (remover) os campos não mencionados no usuario_dict
                self.collection.document(usuario.id).set(usuario_dict, merge=True)
            else:

                if self.password:
                    # 1. Criar usuário no Firebase Authentication
                    usuario_db = auth.create_user(
                        email=usuario.email,
                        password=self.password,
                        display_name=usuario.name.nome_completo,
                        phone_number=usuario.phone_number.get_e164()
                    )

                    # 2. Obtem o uid do usuário Credenciado e Autenticado e insere o uid em usuario.id e cria usuário no Firestore
                    usuario.id = usuario_db.uid
                    # Cria um novo documento com o mesmo uid da Authentication
                    doc_ref = self.collection.document(usuario.id)
                    doc_ref.set(usuario_dict)  # Adiciona os demais campos
                else:
                    raise Exception("Password é necessário para criar usuário")

            return usuario.id
        except exceptions.FirebaseError as e:
            translated_error = deepl_translator(str(e))
            logger.error(f"Erro ao salvar usuário: {translated_error}")
            raise Exception(f"Erro ao salvar usuário: {translated_error}")
        except Exception as e:
            logger.error(f"Erro inesperado ao salvar usuário: {str(e)}")
            raise Exception(f"Erro inesperado ao salvar usuário: {str(e)}")

    async def update_profile(self, id: str, new_profile: str) -> Optional[Usuario]:
        """
        Atualiza o perfil de um usuário.

        Args:
            id (str): ID do usuário
            new_profile (str): Novo perfil a ser atribuído

        Returns:
            Optional[Usuario]: Usuário atualizado ou None se não existir

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
            empresas: List[str] = data.get('empresas', [])
            usuario_photo: str = data.get('photo', None)

            updated_usuario = Usuario(
                id=doc.id,
                email=data['email'],
                name=NomePessoa(first_name, last_name),
                phone_number=PhoneNumber(data['phone_number']),
                profile=data['profile'],
                empresas=empresas,
                photo=usuario_photo,
            )

            return updated_usuario
        except Exception as e:
            # Lida com possíveis exceções, se necessário
            logger.error(f"Erro ao atualizar o perfil do usuário: {e}")
            raise e


    async def update_photo(self, id: str, new_photo: str) -> Optional[Usuario]:
        """
        Atualiza a foto de um usuário.

        Args:
            id (str): ID do usuário
            new_profile (str): Novo perfil a ser atribuído

        Returns:
            Optional[Usuario]: Usuário atualizado ou None se não existir

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
            empresas: List[str] = data.get('empresas', [])
            usuario_photo: str = data.get('photo', None)

            updated_usuario = Usuario(
                id=doc.id,
                email=data['email'],
                name=NomePessoa(first_name, last_name),
                phone_number=PhoneNumber(data['phone_number']),
                profile=data['profile'],
                empresas=empresas,
                photo=usuario_photo,
            )

            return updated_usuario
        except Exception as e:
            # Lida com possíveis exceções, se necessário
            logger.error(f"Erro ao atualizar o perfil do usuário: {e}")
            raise e

    def _doc_to_usuario(self, doc_data: dict) -> Usuario:
        """
        Converter os dados de um documento do Firestore em uma instância de usuário.

        Args:
            doc_data (dict): Os dados do documento Firestore representando um usuário.

        Retorna:
            Usuario: A instância correspondente do usuário.
        """


        # Recontruir campos opcionais
        first_name, last_name = get_first_and_last_name(
            doc_data['display_name'])
        empresas: List[str] = doc_data.get('empresas', [])
        usuario_photo: str = doc_data.get('photo', None)

        return Usuario(
            id=doc_data['id'],
            email=doc_data['email'],
            name=NomePessoa(first_name, last_name),
            phone_number=PhoneNumber(doc_data['phone_number']),
            profile=doc_data['profile'],
            empresas=empresas,
            photo=usuario_photo,
        )

    def _usuario_to_dict(self, usuario: Usuario) -> dict:
        """
        Converter uma instância de usuário em um dicionário para armazenamento no Firestore.

        Args:
            usuario (Usuario): A instância de usuário a ser convertida.

        Retorna:
            dict: A representação do usuário em formato de dicionário.
        """
        # Não adicione id no usuario_dict, pois o Firebase providenciar um uid se não existir
        usuario_dict = {
            "email": usuario.email,
            "display_name": usuario.name.nome_completo,
            "phone_number": usuario.phone_number.get_e164(),
            "profile": usuario.profile,
            "empresas": usuario.empresas,
            "photo": usuario.photo,
        }

        return usuario_dict
