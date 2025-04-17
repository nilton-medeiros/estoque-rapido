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
                logger.error(
                    f"Usuário com email '{email}' não encontrado no Firestore.")
                raise UserNotFoundException("Usuário não encontrado")
            elif e.code == 'permission-denied':
                logger.error(
                    "Permissão negada para acessar os dados do usuário.")
                raise AuthenticationException(
                    "Erro de permissão ao autenticar usuário")
            elif e.code == 'resource-exhausted':
                logger.error(
                    "Cota do Firebase excedida ao tentar autenticar o usuário.")
                raise AuthenticationException("Cota do Firebase excedida")
            elif e.code == 'unavailable':
                logger.error("Serviço do Firestore indisponível no momento.")
                raise AuthenticationException(
                    "Serviço indisponível no momento")
            else:
                logger.error(
                    f"Erro desconhecido do Firebase ao autenticar usuário: {e.code}")
                translated_error = deepl_translator(str(e))
                raise AuthenticationException(
                    f"Erro ao autenticar usuário: {translated_error}")
        except Exception as e:
            logger.error(f"Erro de autenticação: {str(e)}")
            # translated_error = deepl_translator(str(e))
            raise AuthenticationException(f"Erro de autenticação: {str(e)}")

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
            # Insere ou Atualiza na coleção usuarios, merge=True para não sobrescrever (remover) os campos não mencionados no usuario_dict
            self.collection.document(usuario.id).set(usuario.to_dict_db(), merge=True)
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
            raise Exception(
                f"Erro inesperado ao salvar usuário: {translated_error}")

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
                return Usuario.from_dict(usuario_data)
            return None  # Retorna None se o documento não existir
        except exceptions.FirebaseError as e:
            if e.code == 'permission-denied':
                logger.warning(
                    f"Permissão negada ao consultar usuário com id '{id}': {e}")
            elif e.code == 'unavailable':
                logger.error(
                    f"Serviço do Firestore indisponível ao consultar usuário com id '{id}': {e}")
                # Pode considerar re-lançar uma exceção específica para tratamento de disponibilidade
                raise Exception(
                    f"Serviço do Firestore temporariamente indisponível.")
            else:
                logger.error(
                    f"Erro do Firebase ao consultar usuário com id '{id}': Código: {e.code}, Detalhes: {e}")
            raise  # Re-lançar a exceção para tratamento em camadas superiores
        except Exception as e:
            # Captura outros erros inesperados (problemas de rede, etc.)
            logger.error(
                f"Erro inesperado ao consultar usuário com id '{id}': {e}")
            raise

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
            if e.code == 'permission-denied':
                logger.warning(
                    f"Permissão negada ao consultar usuário pelo email '{email}': {e}")
            elif e.code == 'unavailable':
                logger.error(
                    f"Serviço do Firestore indisponível ao consultar usuário pelo email '{email}': {e}")
                # Pode considerar re-lançar uma exceção específica para tratamento de disponibilidade
                raise Exception(
                    f"Serviço do Firestore temporariamente indisponível.")
            else:
                logger.error(
                    f"Erro do Firebase ao consultar usuário pelo email '{email}': Código: {e.code}, Detalhes: {e}")
            raise  # Re-lançar a exceção para tratamento em camadas superiores
        except Exception as e:
            # Captura outros erros inesperados (problemas de rede, etc.)
            logger.error(
                f"Erro inesperado ao consultar usuário pelo email '{email}': {e}")
            raise

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
                usuarios.append(Usuario.from_dict(usuario_data))

            return usuarios
        except exceptions.FirebaseError as e:
            if e.code == 'permission-denied':
                logger.warning(
                    f"Permissão negada ao consultar usuários da empresa id '{empresa_id}': {e}")
            elif e.code == 'unavailable':
                logger.error(
                    f"Serviço do Firestore indisponível ao consultar usuários da empresa id '{empresa_id}': {e}")
                # Pode considerar re-lançar uma exceção específica para tratamento de disponibilidade
                raise Exception(
                    f"Serviço do Firestore temporariamente indisponível.")
            else:
                logger.error(
                    f"Erro do Firebase ao consultar usuários da empresa id '{empresa_id}': Código: {e.code}, Detalhes: {e}")
            raise  # Re-lançar a exceção para tratamento em camadas superiores
        except Exception as e:
            # Captura outros erros inesperados (problemas de rede, etc.)
            logger.error(
                f"Erro inesperado ao consultar usuários da empresa id '{empresa_id}': {e}")
            raise

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
                return Usuario.from_dict(usuario_data)

            return None
        except exceptions.FirebaseError as e:
            if e.code == 'permission-denied':
                logger.warning(
                    f"Permissão negada ao consultar usuário pelo email '{email}': {e}")
            elif e.code == 'unavailable':
                logger.error(
                    f"Serviço do Firestore indisponível ao consultar usuário pelo email '{email}': {e}")
                # Pode considerar re-lançar uma exceção específica para tratamento de disponibilidade
                raise Exception(
                    f"Serviço do Firestore temporariamente indisponível.")
            else:
                logger.error(
                    f"Erro do Firebase ao consultar usuário pelo email '{email}': Código: {e.code}, Detalhes: {e}")
            raise  # Re-lançar a exceção para tratamento em camadas superiores
        except Exception as e:
            # Captura outros erros inesperados (problemas de rede, etc.)
            logger.error(
                f"Erro inesperado ao consultar usuário pelo email '{email}': {e}")
            raise

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
            ).where('name', '>=', name).where('name', '<=', name + '\uf8ff')

            docs = query.stream()
            usuarios: List[Usuario] = []

            for doc in docs:
                usuario_data = doc.to_dict()
                usuario_data['id'] = doc.id
                usuarios.append(Usuario.from_dict(usuario_data))

            return usuarios  # Retorna uma lista de usuários encontrados ou lista vazia se nenhum for encontrado
        except exceptions.FirebaseError as e:
            if e.code == 'permission-denied':
                logger.warning(
                    f"Permissão negada ao consultar usuário pelo nome '{name}': {e}")
            elif e.code == 'unavailable':
                logger.error(
                    f"Serviço do Firestore indisponível ao consultar usuário pelo nome '{name}': {e}")
                # Pode considerar re-lançar uma exceção específica para tratamento de disponibilidade
                raise Exception(
                    f"Serviço do Firestore temporariamente indisponível.")
            else:
                logger.error(
                    f"Erro do Firebase ao consultar usuário pelo nome '{name}': Código: {e.code}, Detalhes: {e}")
            raise  # Re-lançar a exceção para tratamento em camadas superiores
        except Exception as e:
            # Captura outros erros inesperados (problemas de rede, etc.)
            logger.error(
                f"Erro inesperado ao consultar usuário pelo nome '{name}': {e}")
            raise

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
                usuarios.append(Usuario.from_dict(usuario_data))

            return usuarios  # Retorna uma lista de usuários encontrados ou lista vazia se nenhum for encontrado
        except exceptions.FirebaseError as e:
            if e.code == 'permission-denied':
                logger.warning(
                    f"Permissão negada ao consultar usuário pelo pefil do usuário '{profile}': {e}")
            elif e.code == 'unavailable':
                logger.error(
                    f"Serviço do Firestore indisponível ao consultar usuário pelo pefil do usuário '{profile}': {e}")
                # Pode considerar re-lançar uma exceção específica para tratamento de disponibilidade
                raise Exception(
                    f"Serviço do Firestore temporariamente indisponível.")
            else:
                logger.error(
                    f"Erro do Firebase ao consultar usuário pelo pefil do usuário '{profile}': Código: {e.code}, Detalhes: {e}")
            raise  # Re-lançar a exceção para tratamento em camadas superiores
        except Exception as e:
            # Captura outros erros inesperados (problemas de rede, etc.)
            logger.error(
                f"Erro inesperado ao consultar usuário pelo pefil do usuário '{profile}': {e}")
            raise

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
            logger.info(f"Usuário com id '{usuario_id}' excluído com sucesso.")
        except exceptions.FirebaseError as e:
            if e.code == 'not-found':
                logger.error(
                    f"Documento com id '{usuario_id}' não encontrado.")
            elif e.code == 'permission-denied':
                logger.error(
                    f"Permissão negada para excluir o documento com id '{usuario_id}'.")
            elif e.code == 'resource-exhausted':
                logger.error(
                    "Cota do Firebase excedida ao tentar excluir o documento.")
            elif e.code == 'unavailable':
                logger.error("Serviço do Firestore indisponível no momento.")
            elif e.code == 'deadline-exceeded':
                logger.error(
                    "Tempo limite para a operação de exclusão excedido.")
            else:
                logger.error(
                    f"Erro desconhecido do Firebase ao excluir o documento: {e.code}")
            translated_error = deepl_translator(str(e))
            raise Exception(
                f"Erro ao deletar usuário com id '{usuario_id}': {translated_error}")
        except Exception as e:
            logger.error(
                f"Erro inesperado ao deletar usuário com id '{usuario_id}': {str(e)}")
            raise Exception(
                f"Erro inesperado ao deletar usuário com id '{usuario_id}': {str(e)}")

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
            usuario_data = doc_ref.get().to_dict()
            usuario_data['id'] = doc.id
            return Usuario.from_dict(usuario_data)
        except exceptions.FirebaseError as e:
            if e.code == 'not-found':
                logger.error(f"Documento com ID '{id}' não encontrado.")
            elif e.code == 'permission-denied':
                logger.error(
                    f"Permissão negada para atualizar o perfil do usuário com ID '{id}'.")
            elif e.code == 'resource-exhausted':
                logger.error(
                    "Cota do Firebase excedida ao tentar atualizar o perfil.")
            elif e.code == 'unavailable':
                logger.error("Serviço do Firestore indisponível no momento.")
            elif e.code == 'deadline-exceeded':
                logger.error(
                    "Tempo limite para a operação de atualização excedido.")
            else:
                logger.error(
                    f"Erro desconhecido do Firebase ao atualizar o perfil: {e.code}")
            translated_error = deepl_translator(str(e))
            raise Exception(
                f"Erro ao atualizar o perfil do usuário com ID '{id}': {translated_error}")
        except Exception as e:
            logger.error(
                f"Erro inesperado ao atualizar o perfil do usuário com ID '{id}': {str(e)}")
            raise Exception(
                f"Erro inesperado ao atualizar o perfil do usuário com ID '{id}': {str(e)}")

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
            usuario_data = doc_ref.get().to_dict()
            usuario_data['id'] = doc.id
            return Usuario.from_dict(usuario_data)
        except exceptions.FirebaseError as e:
            if e.code == 'not-found':
                logger.error(f"Documento com ID '{id}' não encontrado.")
            elif e.code == 'permission-denied':
                logger.error(
                    f"Permissão negada para atualizar a foto do usuário com ID '{id}'.")
            elif e.code == 'resource-exhausted':
                logger.error(
                    "Cota do Firebase excedida ao tentar atualizar a foto.")
            elif e.code == 'unavailable':
                logger.error("Serviço do Firestore indisponível no momento.")
            elif e.code == 'deadline-exceeded':
                logger.error(
                    "Tempo limite para a operação de atualização excedido.")
            else:
                logger.error(
                    f"Erro desconhecido do Firebase ao atualizar a foto: {e.code}")
            print(f"DEBUG (e): {str(e)}")
            translated_error = deepl_translator(str(e))
            raise Exception(
                f"Erro ao atualizar a foto do usuário com ID '{id}': {translated_error}")
        except Exception as e:
            print(f"DEBUG (e): {str(e)}")
            logger.error(
                f"Erro inesperado ao atualizar a foto do usuario com ID '{id}': {str(e)}")
            raise Exception(
                f"Erro inesperado ao atualizar a foto do usuário com ID '{id}': {str(e)}")

    async def update_colors(self, id: str, new_colors: dict) -> bool:
        """
        Atualiza cor preferencial de um usuário.

        Args:
            id (str): ID do usuário
            new_colors (dict): Nova cor preferencial a ser atribuída

        Returns:
            bool: True se a atualização foi bem-sucedida, False caso contrário

        Raises:
            Exception: Em caso de erro na operação de banco de dados
            ValueError: Se a nova cor não for válida
        """
        try:
            if not new_colors or not new_colors.get('primary'):
                raise ValueError("A nova cor não pode ser vazia")

            doc_ref = self.collection.document(id)
            doc = doc_ref.get()

            if not doc.exists:
                return False

            doc_ref.update({"user_colors": new_colors})
            return True
        except exceptions.FirebaseError as e:
            if e.code == 'not-found':
                logger.error(f"Documento com ID '{id}' não encontrado.")
            elif e.code == 'permission-denied':
                logger.error(
                    f"Permissão negada para atualizar a cor do usuário com ID '{id}'.")
            elif e.code == 'resource-exhausted':
                logger.error(
                    "Cota do Firebase excedida ao tentar atualizar a cor.")
            elif e.code == 'unavailable':
                logger.error("Serviço do Firestore indisponível no momento.")
            elif e.code == 'deadline-exceeded':
                logger.error(
                    "Tempo limite para a operação de atualização excedido.")
            else:
                logger.error(
                    f"Erro desconhecido do Firebase ao atualizar a cor: {e.code}")
            translated_error = deepl_translator(str(e))
            raise Exception(
                f"Erro ao atualizar a cor do usuário com ID '{id}': {translated_error}")
        except Exception as e:
            logger.error(
                f"Erro inesperado ao atualizar a cor do usuário com ID '{id}': {str(e)}")
            raise Exception(
                f"Erro inesperado ao atualizar a cor do usuário com ID '{id}': {str(e)}")

    async def update_empresas(self, usuario_id: str, empresa_id: str, empresas: set) -> bool:
        """
        Atualiza campos empresa_id e empresas do usuário.

        Args:
            user_id (str): ID do usuário.
            empresa_id (str): ID da empresa ativa.
            empresas (set): Conjunto de empresas associada ao usuário.

        Returns:
            bool: True se a atualização foi bem-sucedida, False caso contrário

        Raises:
            Exception: Em caso de erro na operação de banco de dados
            ValueError: Se os campos não forem válidas
        """
        try:
            if not usuario_id or not empresa_id or not empresas:
                raise ValueError(
                    "Os campos usuario_id, empresa_id e empresas não podem ser vazios")

            doc_ref = self.collection.document(usuario_id)
            doc = doc_ref.get()

            if not doc.exists:
                return False

            doc_ref.update({"empresa_id": empresa_id, "empresas": list(empresas)})
            return True
        except exceptions.FirebaseError as e:
            if e.code == 'not-found':
                logger.error(
                    f"Documento com ID '{usuario_id}' não encontrado.")
            elif e.code == 'permission-denied':
                logger.error(
                    f"Permissão negada para atualizar a empresa do usuário com ID '{usuario_id}'.")
            elif e.code == 'resource-exhausted':
                logger.error(
                    "Cota do Firebase excedida ao tentar atualizar a empresa.")
            elif e.code == 'unavailable':
                logger.error("Serviço do Firestore indisponível no momento.")
            elif e.code == 'deadline-exceeded':
                logger.error(
                    "Tempo limite para a operação de atualização excedido.")
            else:
                logger.error(
                    f"Erro desconhecido do Firebase ao atualizar a empresa: {e.code}")
            translated_error = deepl_translator(str(e))
            raise Exception(
                f"Erro ao atualizar a empresa do usuário com ID '{usuario_id}': {translated_error}")
        except Exception as e:
            msg = f"Erro inesperado ao atualizar a empresa do usuário com ID '{usuario_id}': {str(e)}"
            logger.error(msg)
            raise Exception(msg)
