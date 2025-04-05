import logging

from typing import List, Optional

from firebase_admin import exceptions, firestore

from src.domains.shared import NomePessoa, PhoneNumber
from src.domains.shared.domain_exceptions import AuthenticationException, InvalidCredentialsException, UserNotFoundException
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

    def __init__(self):
        """
        Inicializa o cliente do Firebase Firestore e conecta-se à coleção 'usuarios'.

        Garante que o aplicativo Firebase seja inicializado antes de criar o cliente Firestore.
        """
        get_firebase_app()

        self.db = firestore.client()
        self.collection = self.db.collection('usuarios')

    async def authentication(self, email, password) -> Optional[Usuario]:
        """
        Autentica um usuário com o email e senha fornecidos.

        Args:
            email (str): O email do usuário.
            password (str): A senha do usuário.

        Returns:
            Usuario: Usuário autenticado ou None caso credenciais inválidas.

        Raises:
            UserNotFoundException: Se o usuário não for encontrado.
            InvalidCredentialsException: Se a senha estiver incorreta.
            Exception: Para outros erros inesperados.
        """
        try:
            # Busca o usuário pelo email
            user = await self.find_by_email(email)
            if not user:
                raise UserNotFoundException("Usuário não encontrado")

            # Valida a senha descriptografada
            if user.password.decrypted == password:
                return user

            raise InvalidCredentialsException("Senha incorreta")
        except exceptions.FirebaseError as e:
            if e.code == 'not-found':
                logger.error(f"Usuário com email '{email}' não encontrado no Firestore.")
                raise UserNotFoundException("Usuário não encontrado")
            elif e.code == 'permission-denied':
                logger.error("Permissão negada para acessar os dados do usuário.")
                raise AuthenticationException("Erro de permissão ao autenticar usuário")
            elif e.code == 'resource-exhausted':
                logger.error("Cota do Firebase excedida ao tentar autenticar o usuário.")
                raise AuthenticationException("Cota do Firebase excedida")
            elif e.code == 'unavailable':
                logger.error("Serviço do Firestore indisponível no momento.")
                raise AuthenticationException("Serviço indisponível no momento")
            else:
                logger.error(f"Erro desconhecido do Firebase ao autenticar usuário: {e.code}")
                translated_error = deepl_translator(str(e))
                raise AuthenticationException(f"Erro ao autenticar usuário: {translated_error}")
        except Exception as e:
            logger.error(f"Erro inesperado ao autenticar usuário: {str(e)}")
            translated_error = deepl_translator(str(e))
            raise AuthenticationException(f"Erro inesperado ao autenticar usuário: {translated_error}")

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
            # Insere ou Atualiza na coleção usuarios, merge=True para não sobrescrever (remover) os campos não mencionados no usuario_dict
            self.collection.document(usuario.id).set(usuario_dict, merge=True)
            return usuario.id
        except exceptions.FirebaseError as e:
            if e.code == 'invalid-argument':
                logger.error("Argumento inválido fornecido.")
            elif e.code == 'not-found':
                logger.error("Documento ou recurso não encontrado.")
            elif e.code == 'permission-denied':
                logger.error("Permissão negada para realizar a operação.")
            elif e.code == 'resource-exhausted':
                logger.error("Cota do Firebase excedida.")
            else:
                logger.error(f"Erro desconhecido do Firebase: {e.code}")
            translated_error = deepl_translator(str(e))
            raise Exception(f"Erro ao salvar usuário: {translated_error}")
        except Exception as e:
            # Captura erros inesperados
            logger.error(f"Erro inesperado ao salvar usuário: {str(e)}")
            translated_error = deepl_translator(str(e))
            raise Exception(f"Erro inesperado ao salvar usuário: {translated_error}")

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
        except exceptions.FirebaseError as e:
            if e.code == 'invalid-argument':
                logger.error("Argumento inválido fornecido para a consulta.")
            elif e.code == 'not-found':
                logger.error("Recurso ou coleção não encontrado.")
            elif e.code == 'permission-denied':
                logger.error("Permissão negada para acessar a coleção.")
            elif e.code == 'resource-exhausted':
                logger.error("Cota do Firebase excedida.")
            elif e.code == 'unavailable':
                logger.error("Serviço do Firestore indisponível no momento.")
            elif e.code == 'deadline-exceeded':
                logger.error("Tempo limite para a operação excedido.")
            else:
                logger.error(f"Erro desconhecido do Firebase: {e.code}")
            translated_error = deepl_translator(str(e))
            raise Exception(f"Erro ao contar usuários: {translated_error}")
        except Exception as e:
            logger.error(f"Erro inesperado ao contar usuários: {e}")
            raise e

    async def delete(self, usuario_id: str) -> None:
        """
        Excluir um usuário pelo seu identificador único do Firestore e também do Firebase Authentication.

        Args:
            usuario_id (str): O identificador único do usuário.

        Raises:
            Exception: Se ocorrer um erro no Firebase ou outro erro inesperado durante a exclusão.
        """
        try:
            # Deleta do Firestore
            self.collection.document(usuario_id).delete()
            logger.info(f"Usuário com ID '{usuario_id}' excluído com sucesso.")
        except exceptions.FirebaseError as e:
            if e.code == 'not-found':
                logger.error(f"Documento com ID '{usuario_id}' não encontrado.")
            elif e.code == 'permission-denied':
                logger.error(f"Permissão negada para excluir o documento com ID '{usuario_id}'.")
            elif e.code == 'resource-exhausted':
                logger.error("Cota do Firebase excedida ao tentar excluir o documento.")
            elif e.code == 'unavailable':
                logger.error("Serviço do Firestore indisponível no momento.")
            elif e.code == 'deadline-exceeded':
                logger.error("Tempo limite para a operação de exclusão excedido.")
            else:
                logger.error(f"Erro desconhecido do Firebase ao excluir o documento: {e.code}")
            translated_error = deepl_translator(str(e))
            raise Exception(f"Erro ao deletar usuário com ID '{usuario_id}': {translated_error}")
        except Exception as e:
            logger.error(f"Erro inesperado ao deletar usuário com ID '{usuario_id}': {str(e)}")
            raise Exception(f"Erro inesperado ao deletar usuário com ID '{usuario_id}': {str(e)}")

    async def exists_by_email(self, email: str) -> bool:
        """
        Verifica se existe um usuário com o email especificado.

        Args:
            email (str): Email a ser verificado.

        Returns:
            bool: True se existe um usuário com o email, False caso contrário.

        Raises:
            Exception: Em caso de erro na operação de banco de dados.
        """
        try:
            query = self.collection.where(
                field_path='email', op_string='==', value=email).limit(1)
            docs = query.stream()

            for doc in docs:
                return True
            return False
        except exceptions.FirebaseError as e:
            if e.code == 'invalid-argument':
                logger.error("Argumento inválido fornecido para a consulta.")
            elif e.code == 'permission-denied':
                logger.error("Permissão negada para acessar a coleção.")
            elif e.code == 'resource-exhausted':
                logger.error("Cota do Firebase excedida.")
            elif e.code == 'unavailable':
                logger.error("Serviço do Firestore indisponível no momento.")
            elif e.code == 'deadline-exceeded':
                logger.error("Tempo limite para a operação excedido.")
            else:
                logger.error(f"Erro desconhecido do Firebase: {e.code}")
            translated_error = deepl_translator(str(e))
            raise Exception(f"Erro ao verificar existência de usuário com email '{email}': {translated_error}")
        except Exception as e:
            logger.error(f"Erro inesperado ao verificar existência de usuário com email '{email}': {str(e)}")
            raise Exception(f"Erro inesperado ao verificar existência de usuário com email '{email}': {str(e)}")

    async def find_all(self, empresa_id, limit: int = 100, offset: int = 0) -> List[Usuario]:
        """
        Retorna uma lista paginada de usuários.

        Args:
            empresa_id (str): ID da empresa a ser buscada.
            limit (int): Número máximo de registros a retornar.
            offset (int): Número de registros a pular.

        Returns:
            List[Usuario]: Lista de usuários encontrados.

        Raises:
            Exception: Em caso de erro na operação de banco de dados.
        """
        try:
            query = self.collection.where(
                field_path='empresas', op_string='array_contains', value=empresa_id
            ).offset(offset).limit(limit)

            docs = query.stream()
            usuarios: List[Usuario] = []

            for doc in docs:
                usuario_data = doc.to_dict()
                usuario_data['id'] = doc.id
                usuarios.append(self._doc_to_usuario(usuario_data))

            return usuarios
        except exceptions.FirebaseError as e:
            translated_error = deepl_translator(str(e))
            logger.error(f"Erro ao buscar usuários: {translated_error}")
            raise Exception(f"Erro ao buscar usuários: {translated_error}")
        except Exception as e:
            logger.error(f"Erro inesperado ao buscar usuários: {str(e)}")
            raise Exception(f"Erro inesperado ao buscar usuários: {str(e)}")

    async def find_by_email(self, email: str) -> Optional[Usuario]:
        """
        Encontrar um usuário pelo seu email.

        Args:
            email (str): O email do usuário a ser encontrado.

        Returns:
            Optional[Usuario]: Uma instância do usuário se encontrado, None caso contrário.

        Raises:
            Exception: Em caso de erro na operação de banco de dados.
        """
        try:
            query = self.collection.where(
                field_path='email', op_string='==', value=email
            ).limit(1)
            docs = query.stream()

            for doc in docs:
                usuario_data = doc.to_dict()
                usuario_data['id'] = doc.id
                return self._doc_to_usuario(usuario_data)

            return None
        except exceptions.FirebaseError as e:
            translated_error = deepl_translator(str(e))
            logger.error(f"Erro ao buscar usuário pelo email '{email}': {translated_error}")
            raise Exception(f"Erro ao buscar usuário pelo email '{email}': {translated_error}")
        except Exception as e:
            logger.error(f"Erro inesperado ao buscar usuário pelo email '{email}': {str(e)}")
            raise Exception(f"Erro inesperado ao buscar usuário pelo email '{email}': {str(e)}")

    async def find_by_id(self, id: str) -> Optional[Usuario]:
        """
        Busca um usuário pelo ID.

        Args:
            id (str): ID do usuário.

        Returns:
            Optional[Usuario]: Usuário encontrado ou None se não existir.

        Raises:
            Exception: Em caso de erro na operação de banco de dados.
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
            raise Exception(f"Erro ao buscar usuário com ID '{id}': {translated_error}")
        except Exception as e:
            logger.error(f"Erro inesperado ao buscar usuário com ID '{id}': {str(e)}")
            raise Exception(f"Erro inesperado ao buscar usuário com ID '{id}': {str(e)}")

    async def find_by_name(self, empresa_id, name: str) -> List[Usuario]:
        """
        Busca usuários da empresa logada que contenham o nome especificado.

        Args:
            empresa_id (str): ID da empresa.
            name (str): Nome ou parte do nome a ser buscado.

        Returns:
            List[Usuario]: Lista de usuários que correspondem à busca.

        Raises:
            Exception: Em caso de erro na operação de banco de dados.
        """
        try:
            query = self.collection.where(
                field_path='empresas', op_string='array_contains', value=empresa_id
            ).where('display_name', '>=', name).where('display_name', '<=', name + '\uf8ff')

            docs = query.stream()
            usuarios: List[Usuario] = []

            for doc in docs:
                usuario_data = doc.to_dict()
                usuario_data['id'] = doc.id
                usuarios.append(self._doc_to_usuario(usuario_data))

            return usuarios
        except exceptions.FirebaseError as e:
            translated_error = deepl_translator(str(e))
            logger.error(f"Erro ao buscar usuário pelo nome '{name}': {translated_error}")
            raise Exception(f"Erro ao buscar usuário pelo nome '{name}': {translated_error}")
        except Exception as e:
            logger.error(f"Erro inesperado ao buscar usuário pelo nome '{name}': {str(e)}")
            raise Exception(f"Erro inesperado ao buscar usuário pelo nome '{name}': {str(e)}")

    async def find_by_profile(self, empresa_id: str, profile: str) -> List[Usuario]:
        """
        Busca usuários por perfil.

        Args:
            empresa_id (str): ID da empresa.
            profile (str): Perfil a ser buscado.

        Returns:
            List[Usuario]: Lista de usuários com o perfil especificado.

        Raises:
            Exception: Em caso de erro na operação de banco de dados.
        """
        try:
            query = self.collection.where(
                field_path='empresas', op_string='array_contains', value=empresa_id
            ).where(field_path='profile', op_string='==', value=profile)

            docs = query.stream()
            usuarios: List[Usuario] = []

            for doc in docs:
                usuario_data = doc.to_dict()
                usuario_data["id"] = doc.id
                usuarios.append(self._doc_to_usuario(usuario_data))

            return usuarios
        except exceptions.FirebaseError as e:
            translated_error = deepl_translator(str(e))
            logger.error(f"Erro ao buscar usuário pelo perfil '{profile}': {translated_error}")
            raise Exception(f"Erro ao buscar usuário pelo perfil '{profile}': {translated_error}")
        except Exception as e:
            logger.error(f"Erro inesperado ao buscar usuário pelo perfil '{profile}': {str(e)}")
            raise Exception(f"Erro inesperado ao buscar usuário pelo perfil '{profile}': {str(e)}")

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
            if not new_profile:
                raise ValueError("O novo perfil não pode ser vazio")

            doc_ref = self.collection.document(id)
            doc = doc_ref.get()

            if not doc.exists:
                return None

            doc_ref.update({"profile": new_profile})
            data = doc_ref.get().to_dict()

            return self._doc_to_usuario(data)
        except exceptions.FirebaseError as e:
            if e.code == 'not-found':
                logger.error(f"Documento com ID '{id}' não encontrado.")
            elif e.code == 'permission-denied':
                logger.error(f"Permissão negada para atualizar o perfil do usuário com ID '{id}'.")
            elif e.code == 'resource-exhausted':
                logger.error("Cota do Firebase excedida ao tentar atualizar o perfil.")
            elif e.code == 'unavailable':
                logger.error("Serviço do Firestore indisponível no momento.")
            elif e.code == 'deadline-exceeded':
                logger.error("Tempo limite para a operação de atualização excedido.")
            else:
                logger.error(f"Erro desconhecido do Firebase ao atualizar o perfil: {e.code}")
            translated_error = deepl_translator(str(e))
            raise Exception(f"Erro ao atualizar o perfil do usuário com ID '{id}': {translated_error}")
        except Exception as e:
            logger.error(f"Erro inesperado ao atualizar o perfil do usuário com ID '{id}': {str(e)}")
            raise Exception(f"Erro inesperado ao atualizar o perfil do usuário com ID '{id}': {str(e)}")

    async def update_photo(self, id: str, new_photo: str) -> Optional[Usuario]:
        """
        Atualiza a foto de um usuário.

        Args:
            id (str): ID do usuário
            new_photo (str): Link para a nova foto a ser atribuída

        Returns:
            Optional[Usuario]: Usuário atualizado ou None se não existir

        Raises:
            Exception: Em caso de erro na operação de banco de dados
            ValueError: Se a nova foto não for válida
        """
        try:
            if not new_photo:
                raise ValueError("A nova foto não pode ser vazia")

            doc_ref = self.collection.document(id)
            doc = doc_ref.get()

            if not doc.exists:
                return None

            doc_ref.update({"photo_url": new_photo})
            data = doc_ref.get().to_dict()

            return self._doc_to_usuario(data)
        except exceptions.FirebaseError as e:
            if e.code == 'not-found':
                logger.error(f"Documento com ID '{id}' não encontrado.")
            elif e.code == 'permission-denied':
                logger.error(f"Permissão negada para atualizar a foto do usuário com ID '{id}'.")
            elif e.code == 'resource-exhausted':
                logger.error("Cota do Firebase excedida ao tentar atualizar a foto.")
            elif e.code == 'unavailable':
                logger.error("Serviço do Firestore indisponível no momento.")
            elif e.code == 'deadline-exceeded':
                logger.error("Tempo limite para a operação de atualização excedido.")
            else:
                logger.error(f"Erro desconhecido do Firebase ao atualizar a foto: {e.code}")
            translated_error = deepl_translator(str(e))
            raise Exception(f"Erro ao atualizar a foto do usuário com ID '{id}': {translated_error}")
        except Exception as e:
            logger.error(f"Erro inesperado ao atualizar a foto do usuário com ID '{id}': {str(e)}")
            raise Exception(f"Erro inesperado ao atualizar a foto do usuário com ID '{id}': {str(e)}")

    async def update_color(self, id: str, new_color: str) -> bool:
        """
        Atualiza a cor preferencial de um usuário.

        Args:
            id (str): ID do usuário
            new_color (str): Nova cor preferencial a ser atribuída

        Returns:
            bool: True se a atualização foi bem-sucedida, False caso contrário

        Raises:
            Exception: Em caso de erro na operação de banco de dados
            ValueError: Se a nova cor não for válida
        """
        try:
            if not new_color:
                raise ValueError("A nova cor não pode ser vazia")

            doc_ref = self.collection.document(id)
            doc = doc_ref.get()

            if not doc.exists:
                return False

            doc_ref.update({"user_color": new_color})
            return True
        except exceptions.FirebaseError as e:
            if e.code == 'not-found':
                logger.error(f"Documento com ID '{id}' não encontrado.")
            elif e.code == 'permission-denied':
                logger.error(f"Permissão negada para atualizar a cor do usuário com ID '{id}'.")
            elif e.code == 'resource-exhausted':
                logger.error("Cota do Firebase excedida ao tentar atualizar a cor.")
            elif e.code == 'unavailable':
                logger.error("Serviço do Firestore indisponível no momento.")
            elif e.code == 'deadline-exceeded':
                logger.error("Tempo limite para a operação de atualização excedido.")
            else:
                logger.error(f"Erro desconhecido do Firebase ao atualizar a cor: {e.code}")
            translated_error = deepl_translator(str(e))
            raise Exception(f"Erro ao atualizar a cor do usuário com ID '{id}': {translated_error}")
        except Exception as e:
            logger.error(f"Erro inesperado ao atualizar a cor do usuário com ID '{id}': {str(e)}")
            raise Exception(f"Erro inesperado ao atualizar a cor do usuário com ID '{id}': {str(e)}")

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
        photo_url: str = doc_data.get('photo_url', None)

        from src.domains.shared.password import Password

        return Usuario(
            id=doc_data['id'],
            email=doc_data['email'],
            password=Password.from_encrypted(doc_data['password']),
            name=NomePessoa(first_name, last_name),
            phone_number=PhoneNumber(doc_data['phone_number']),
            profile=doc_data['profile'],
            empresa_id=doc_data.get('empresa_id', None),
            empresas=empresas,
            photo_url=photo_url,
            user_color=doc_data.get('user_color', 'blue'),
        )

    def _usuario_to_dict(self, usuario: Usuario) -> dict:
        """
        Converter uma instância de usuário em um dicionário para armazenamento no Firestore.

        Args:
            usuario (Usuario): A instância de usuário a ser convertida.

        Retorna:
            dict: A representação do usuário em formato de dicionário.
        """
        # Não adicione id no usuario_dict, pois é passado o id no documento de referencia
        usuario_dict = {
            "email": usuario.email,
            "password": usuario.password.value,  # Senha encriptada
            "display_name": usuario.name.nome_completo,
            "phone_number": usuario.phone_number.get_e164(),
            "profile": usuario.profile,
            "empresa_id": usuario.empresa_id,   # Ultima Empresa logada pelo usuário
            # Lista de IDs de empresas que o usuário gerencia
            "empresas": usuario.empresas,
            "photo_url": usuario.photo_url,
            # Ultima cor preferencial do usuário (interface)
            "user_color": usuario.user_color,
        }

        return usuario_dict
