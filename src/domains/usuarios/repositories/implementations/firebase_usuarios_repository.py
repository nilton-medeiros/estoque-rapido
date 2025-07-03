import logging

from typing import Optional

from google.cloud.firestore_v1.base_query import FieldFilter
from google.api_core import exceptions as google_api_exceptions
from firebase_admin import exceptions, firestore

from src.domains.shared.controllers.domain_exceptions import AuthenticationException, InvalidCredentialsException, UserNotFoundException
from src.domains.usuarios.models.usuarios_model import Usuario
from src.domains.shared.models.registration_status import RegistrationStatus
from src.domains.usuarios.repositories.contracts.usuarios_repository import UsuariosRepository
from src.shared.utils import deepl_translator
from storage.data import get_firebase_app

logger = logging.getLogger(__name__)


# Repositório do Firebase, usa a classe abstrata UsuariosRepositoy para forçar a implementação de métodos conforme contrato em UsuariosRepository
class FirebaseUsuariosRepository(UsuariosRepository):
    """
    Um repositório para gerenciar usuários utilizando o Firebase Firestore.

    Esta classe fornece métodos para realizar operações de CRUD em dados de usuários
    armazenados em um banco de dados Firestore.
    Não Utiliza mais o Google Authorization para autenticação de usuarios.
    """

    def __init__(self):
        """
        Inicializa o cliente do Firebase Firestore e conecta-se à coleção 'usuarios'.

        Garante que o aplicativo Firebase seja inicializado antes de criar o cliente Firestore.
        """
        get_firebase_app()

        self.db = firestore.client()
        self.collection = self.db.collection('usuarios')

    def authentication(self, email, password) -> Usuario | None:
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
            # Busca o usuário pelo email, aqui é necessário
            user = self.find_by_email(email)
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
            translated_error = deepl_translator(str(e))
            raise AuthenticationException(f"Erro de autenticação: {translated_error}")

    def save(self, usuario: Usuario) -> str | None:
        """
        Salvar um usuário no banco de dados Firestore.

        Se o usuário já existir pelo seu id, atualiza o documento existente em vez
        de criar um novo.

        Args:
            usuario (Usuario): A instância do usuário a ser salvo.

        Retorna:
            str: O ID do documento do usuário salvo.
        """
        # usuario.id é adicionado em usuarios_services.create(), como o id pode ser None no model, o pylance acusa que o return empresa.id não pode ser str|None
        if usuario.id is None:
            raise Exception("Erro ao salvar usuário: ID não informado")

        try:
            data_to_save = usuario.to_dict_db()

            # Define created_at apenas na criação inicial
            if not data_to_save.get("created_at"):
                data_to_save['created_at'] = firestore.SERVER_TIMESTAMP # type: ignore [attr-defined]

            # updated_at é sempre definido/atualizado com o timestamp do servidor
            data_to_save['updated_at'] = firestore.SERVER_TIMESTAMP # type: ignore [attr-defined]

            # Gerencia os timestamps de status (ACTIVE, DELETED, INACTIVE)
            if data_to_save.get("status") == RegistrationStatus.ACTIVE.name and not data_to_save.get("activated_at"):
                data_to_save['activated_at'] = firestore.SERVER_TIMESTAMP # type: ignore [attr-defined]

            if data_to_save.get("status") == RegistrationStatus.DELETED.name and not data_to_save.get("deleted_at"):
                data_to_save['deleted_at'] = firestore.SERVER_TIMESTAMP # type: ignore [attr-defined]

            if data_to_save.get("status") == RegistrationStatus.INACTIVE.name and not data_to_save.get("inactivated_at"):
                data_to_save['inactivated_at'] = firestore.SERVER_TIMESTAMP # type: ignore [attr-defined]

            doc_ref = self.collection.document(usuario.id)
            doc_ref.set(data_to_save, merge=True) # Chamada síncrona

            # Após salvar, lê o documento de volta para obter os timestamps resolvidos
            try:
                doc_snapshot = doc_ref.get() # Chamada síncrona

                if not doc_snapshot.exists:
                    logger.warning(
                        f"Documento {usuario.id} não encontrado imediatamente após o set para releitura dos timestamps."
                    )
                    return None # Retorna None, pois o usuario não foi confirmado ou não pôde ser relido.

                # Re-hidrata o objeto 'usuario' em memória com os dados do DB (que incluem os timestamps reais)
                user_data_from_db = doc_snapshot.to_dict()

                # Garante que o ID esteja presente no dicionário antes de passar para from_dict
                user_data_from_db['id'] = doc_snapshot.id

                # Cria um novo objeto Usuario a partir dos dados do DB
                # e transfere os timestamps reais para o objeto 'usuario' original
                # que foi passado para o método 'save'.
                updated_usuario_obj = Usuario.from_dict(user_data_from_db)

                usuario.created_at = updated_usuario_obj.created_at
                usuario.updated_at = updated_usuario_obj.updated_at
                usuario.activated_at = updated_usuario_obj.activated_at
                usuario.deleted_at = updated_usuario_obj.deleted_at
                usuario.inactivated_at = updated_usuario_obj.inactivated_at

            except Exception as e_read:
                logger.error(
                    f"Erro ao reler o documento {usuario.id} para atualizar timestamps no objeto em memória: {str(e_read)}"
                )
                # A operação de save principal foi bem-sucedida, mas a releitura falhou.
                # O objeto 'usuario' em memória não terá os timestamps reais, mas o registro no DB está correto.
                return usuario.id # Ainda retorna o ID, pois o save no DB foi OK.

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
            translated_error = deepl_translator(str(e))
            logger.error(f"Erro inesperado ao salvar usuário: {translated_error} [{str(e)}]")
            raise

        return usuario.id

    def count(self, empresa_id: str) -> int:
        """
        Conta o número de usuários que possuem um empresa_id específico no campo 'empresas'.

        Args:
            empresa_id (str): O ID da empresa a ser buscado.

        Returns:
            int: O número de usuários encontrados.
        """
        try:
            query = (self.collection
                     .where(filter=FieldFilter("empresas", "array_contains", empresa_id)))
            # query = self.collection.where(field_path='empresas', op_string='array_contains', value=empresa_id) # método antigo
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

    def find_by_id(self, id: str) -> Usuario | None:
        """
        Busca um usuário pelo ID.

        Args:
            id (str): ID do usuário.

        Returns:
            Usuario | None: Usuário encontrado ou None se não existir.

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

    def exists_by_email(self, email: str) -> bool:
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
            query = (self.collection
                     .where(filter=FieldFilter("email", "==", email))
                     .limit(1))
            docs = query.get()
            return len(docs) > 0
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

    def find_all(self, empresa_id: str, status_deleted: bool = False) -> tuple[list[Usuario], int]:
        """
        Retorna uma lista paginada de usuários.

        Args:
            empresa_id (str): ID da empresa a ser buscada.
            status_deleted (bool): Se True, somente usuários deletados serão retornados.
            limit (int): Número máximo de registros a retornar.
            offset (int): Número de registros a pular.

        Returns:
            list[Usuario]: Lista de usuários encontrados.
            int: Quantidade total de usuários marcados como "DELETED".

        Raises:
            Exception: Em caso de erro na operação de banco de dados.
        """
        try:
            query = (self.collection
                     .where(filter=FieldFilter("empresas", "array_contains", empresa_id))
                     .order_by("name.first_name_lower")
                     .order_by("name.last_name_lower"))

            docs = query.get()

            usuarios_result: list[Usuario] = []
            quantity_deleted = 0

            for doc in docs:
                user_data = doc.to_dict()
                if user_data: # Garante que o documento não esteja vazio
                    user_data['id'] = doc.id
                    user_obj = Usuario.from_dict(user_data)

                    # Modificação 4: Corrigir comparação de status
                    # Conta todos os usuarios deletados, independentemente do filtro principal
                    if user_obj.status == RegistrationStatus.DELETED:
                        quantity_deleted += 1

                    # Adiciona o usuário à lista de resultados com base no filtro 'status_deleted'
                    if status_deleted: # Se o filtro é para mostrar deletados
                        if user_obj.status == RegistrationStatus.DELETED:
                            usuarios_result.append(user_obj)
                    else: # not status_deleted (mostrar não deletados)
                        if user_obj.status != RegistrationStatus.DELETED:
                            usuarios_result.append(user_obj)

            # Modificação 2: Remover ordenação em memória, pois o Firestore já fez isso.
            # usuarios_result.sort(key=lambda usuario: usuario.categoria_name) # REMOVIDO

            return usuarios_result, quantity_deleted

        except google_api_exceptions.FailedPrecondition as e:
            # Esta é a exceção específica para erros de "índice ausente".
            # A mensagem de erro 'e' já contém o link para criar o índice.
            logger.error(
                f"Erro de pré-condição ao consultar usuário (provavelmente índice ausente): {e}. "
                "O Firestore requer um índice para esta consulta. "
                f"A mensagem de erro original geralmente inclui um link para criá-lo: {str(e)}"
            )
            raise Exception(
                "Erro ao buscar usuário: Um índice necessário não foi encontrado no banco de dados. "
                "Verifique os logs do servidor para uma mensagem de erro do Firestore que inclui um link para criar o índice automaticamente. "
                f"Detalhe original: {str(e)}"
            )
        except exceptions.FirebaseError as e:
            if hasattr(e, 'code') and e.code == 'permission-denied':
                logger.warning(
                    f"Permissão negada ao consultar lista de usuário: {e}"
                )
                # Decide se quer re-lançar ou tratar aqui. Se re-lançar, a camada superior lida.
                # Por ora, vamos re-lançar para manter o comportamento anterior.
                raise
            elif hasattr(e, 'code') and e.code == 'unavailable':
                logger.error(
                    f"Serviço do Firestore indisponível ao consultar lista de usuário: {e}"
                )
                raise Exception(
                    "Serviço do Firestore temporariamente indisponível."
                )
            else:
                # Outros erros FirebaseError
                logger.error(
                    f"Erro do Firebase ao consultar lista de usuário: Código: {e.code}, Detalhes: {e}"
                )
            raise  # Re-lança o FirebaseError original ou a Exception customizada

        except Exception as e:  # Captura exceções que não são FirebaseError
            # Logar o tipo da exceção pode ajudar a diagnosticar por que não foi pega antes.
            logger.error(
                f"Erro inesperado (Tipo: {type(e)}) ao consultar lista de usuário: {e}"
            )
            raise


    def find_by_email(self, email: str) -> Usuario | None:
        """
        Encontrar um usuário pelo seu email.

        Args:
            email (str): O email do usuário a ser encontrado.

        Returns:
            Usuario | None: Uma instância do usuário se encontrado, None caso contrário.

        Raises:
            Exception: Em caso de erro na operação de banco de dados.
        """
        try:
            query = (self.collection
                     .where(filter=FieldFilter("email", "==", email)).limit(1))
            docs = query.get()

            if docs:
                # Pega o primeiro elemento e vaza (só tem um mesmo, limitado por .limit(1))
                doc = docs[0]
                usuario_data = doc.to_dict()
                if not usuario_data:
                    return None
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

    def find_by_name(self, empresa_id, name: str) -> list[Usuario]:
        """
        Busca usuários da empresa logada que contenham o nome especificado.

        Args:
            empresa_id (str): ID da empresa.
            name (str): Nome ou parte do nome a ser buscado.

        Returns:
            list[Usuario]: Lista de usuários que correspondem à busca.

        Raises:
            Exception: Em caso de erro na operação de banco de dados.
        """
        try:
            research_data_normalized = name.lower().strip()
            query = (self.collection
                     .where(filter=FieldFilter("empresas", "array_contains", empresa_id))
                     .where(filter=FieldFilter("name.first_name_lower", ">=", research_data_normalized))
                     .where(filter=FieldFilter("name.first_name_lower", "<=", research_data_normalized + '\uf8ff'))
                     .order_by("name.first_name_lower")
                     .order_by("name.last_name_lower"))

            docs = query.stream()
            usuarios: list[Usuario] = []

            for doc in docs:
                usuario_data = doc.to_dict()
                usuario_data['id'] = doc.id
                usuarios.append(Usuario.from_dict(usuario_data))

            return usuarios  # Retorna uma lista de usuários encontrados ou lista vazia se nenhum for encontrado
        except google_api_exceptions.FailedPrecondition as e:
            # Esta é a exceção específica para erros de "índice ausente".
            # A mensagem de erro 'e' já contém o link para criar o índice.
            logger.error(
                f"Erro de pré-condição ao consultar usuário (provavelmente índice ausente): {e}. "
                "O Firestore requer um índice para esta consulta. "
                f"A mensagem de erro original geralmente inclui um link para criá-lo: {str(e)}"
            )
            raise Exception(
                "Erro ao buscar usuário: Um índice necessário não foi encontrado no banco de dados. "
                "Verifique os logs do servidor para uma mensagem de erro do Firestore que inclui um link para criar o índice automaticamente. "
                f"Detalhe original: {str(e)}"
            )
        except exceptions.FirebaseError as e:
            if hasattr(e, 'code') and e.code == 'permission-denied':
                logger.warning(
                    f"Permissão negada ao consultar lista de usuário: {e}"
                )
                # Decide se quer re-lançar ou tratar aqui. Se re-lançar, a camada superior lida.
                # Por ora, vamos re-lançar para manter o comportamento anterior.
                raise
            elif hasattr(e, 'code') and e.code == 'unavailable':
                logger.error(
                    f"Serviço do Firestore indisponível ao consultar lista de usuário: {e}"
                )
                raise Exception(
                    "Serviço do Firestore temporariamente indisponível."
                )
            else:
                # Outros erros FirebaseError
                logger.error(
                    f"Erro do Firebase ao consultar lista de usuário: Código: {e.code}, Detalhes: {e}"
                )
            raise  # Re-lança o FirebaseError original ou a Exception customizada

        except Exception as e:  # Captura exceções que não são FirebaseError
            # Logar o tipo da exceção pode ajudar a diagnosticar por que não foi pega antes.
            logger.error(
                f"Erro inesperado (Tipo: {type(e)}) ao consultar lista de usuário: {e}"
            )
            raise


    def find_by_profile(self, empresa_id: str, profile: str) -> list[Usuario]:
        """
        Busca usuários por perfil.

        Args:
            empresa_id (str): ID da empresa.
            profile (str): Perfil a ser buscado.

        Returns:
            list[Usuario]: Lista de usuários com o perfil especificado.

        Raises:
            Exception: Em caso de erro na operação de banco de dados.
        """
        try:
            query = (self.collection
                     .where(filter=FieldFilter("empresas", "array_contains", empresa_id))
                     .where(filter=FieldFilter("profile", "==", profile))
                     .order_by("name.first_name_lower")
                     .order_by("name.last_name_lower"))
            # query = self.collection.where(field_path='empresas', op_string='array_contains', value=empresa_id).where(field_path='profile', op_string='==', value=profile)  # Método antigo

            docs = query.stream()
            usuarios: list[Usuario] = []

            for doc in docs:
                usuario_data = doc.to_dict()
                usuario_data["id"] = doc.id
                usuarios.append(Usuario.from_dict(usuario_data))

            return usuarios  # Retorna uma lista de usuários encontrados ou lista vazia se nenhum for encontrado
        except google_api_exceptions.FailedPrecondition as e:
            # Esta é a exceção específica para erros de "índice ausente".
            # A mensagem de erro 'e' já contém o link para criar o índice.
            logger.error(
                f"Erro de pré-condição ao consultar usuário (provavelmente índice ausente): {e}. "
                "O Firestore requer um índice para esta consulta. "
                f"A mensagem de erro original geralmente inclui um link para criá-lo: {str(e)}"
            )
            raise Exception(
                "Erro ao buscar usuário: Um índice necessário não foi encontrado no banco de dados. "
                "Verifique os logs do servidor para uma mensagem de erro do Firestore que inclui um link para criar o índice automaticamente. "
                f"Detalhe original: {str(e)}"
            )
        except exceptions.FirebaseError as e:
            if hasattr(e, 'code') and e.code == 'permission-denied':
                logger.warning(
                    f"Permissão negada ao consultar lista de usuário: {e}"
                )
                # Decide se quer re-lançar ou tratar aqui. Se re-lançar, a camada superior lida.
                # Por ora, vamos re-lançar para manter o comportamento anterior.
                raise
            elif hasattr(e, 'code') and e.code == 'unavailable':
                logger.error(
                    f"Serviço do Firestore indisponível ao consultar lista de usuário: {e}"
                )
                raise Exception(
                    "Serviço do Firestore temporariamente indisponível."
                )
            else:
                # Outros erros FirebaseError
                logger.error(
                    f"Erro do Firebase ao consultar lista de usuário: Código: {e.code}, Detalhes: {e}"
                )
            raise  # Re-lança o FirebaseError original ou a Exception customizada

        except Exception as e:  # Captura exceções que não são FirebaseError
            # Logar o tipo da exceção pode ajudar a diagnosticar por que não foi pega antes.
            logger.error(
                f"Erro inesperado (Tipo: {type(e)}) ao consultar lista de usuário: {e}"
            )
            raise


    # ToDo: Excluir este método, esta aplicação usa soft delete
    def delete(self, usuario_id: str) -> bool:
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
            return True
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

    def change_password(self, id: str, new_password: bytes) -> bool:
        """
        Troca a senha do usuário.

        Args:
            id (str): ID do usuário
            new_password (bytes): Nova senha encriptada

        Returns:
            bool: True se a senha foi alterada com sucesso, False caso contrário

        Raises:
            Exception: Em caso de erro na operação de banco de dados
        """
        try:
            if not new_password:
                raise ValueError("A nova senha não pode ser vazio")
            if not isinstance(new_password, bytes):
                raise ValueError("A nova senha tem que estar criptografada")

            doc_ref = self.collection.document(id)
            doc = doc_ref.get()

            if not doc.exists:
                return False

            doc_ref.update({"password": new_password, "temp_password": False})
            return True
        except exceptions.FirebaseError as e:
            if e.code == 'not-found':
                logger.error(f"Documento com ID '{id}' não encontrado.")
            elif e.code == 'permission-denied':
                logger.error(
                    f"Permissão negada para atualizar a senha do usuário com ID '{id}'.")
            elif e.code == 'resource-exhausted':
                logger.error(
                    "Cota do Firebase excedida ao tentar atualizar a senha.")
            elif e.code == 'unavailable':
                logger.error("Serviço do Firestore indisponível no momento.")
            elif e.code == 'deadline-exceeded':
                logger.error(
                    "Tempo limite para a operação de atualização excedido.")
            else:
                logger.error(
                    f"Erro desconhecido do Firebase ao atualizar a senha: {e.code}")
            translated_error = deepl_translator(str(e))
            raise Exception(
                f"Erro ao atualizar a senha do usuário com ID '{id}': {translated_error}")
        except Exception as e:
            logger.error(
                f"Erro inesperado ao atualizar a senha do usuário com ID '{id}': {str(e)}")
            raise Exception(
                f"Erro inesperado ao atualizar a senha do usuário com ID '{id}': {str(e)}")

    def update_profile(self, id: str, new_profile: str) -> Usuario | None:
        """
        Atualiza o perfil de um usuário.

        Args:
            id (str): ID do usuário
            new_profile (str): Novo perfil a ser atribuído

        Returns:
            Usuario | None: Usuário atualizado ou None se não existir

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

    def update_photo(self, id: str, new_photo: str) -> Usuario | None:
        """
        Atualiza a foto de um usuário.

        Args:
            id (str): ID do usuário
            new_photo (str): Link para a nova foto a ser atribuída

        Returns:
            Usuario | None: Usuário atualizado ou None se não existir

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
            translated_error = deepl_translator(str(e))
            raise Exception(
                f"Erro ao atualizar a foto do usuário com ID '{id}': {translated_error}")
        except Exception as e:
            logger.error(
                f"Erro inesperado ao atualizar a foto do usuario com ID '{id}': {str(e)}")
            raise Exception(
                f"Erro inesperado ao atualizar a foto do usuário com ID '{id}': {str(e)}")

    def update_colors(self, id: str, new_colors: dict) -> bool:
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

    def update_empresas(self, usuario_id: str, empresas: set, empresa_id: str|None = None) -> bool:
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
            if not usuario_id or empresas is None:
                raise ValueError(
                    "Os campos usuario_id e empresas não podem ser vazios")

            # Obtem o documento pelo seu id
            doc_ref = self.collection.document(usuario_id)
            doc = doc_ref.get()

            if not doc.exists:
                return False

            if empresa_id:
                # Atualiza a empresa ativa e a lista de empresas (registra lista vazia também)
                doc_ref.update({"empresa_id": empresa_id,
                                "empresas": list(empresas)})
            else:
                # Atualiza a lista de empresas (pode ser vazia)
                doc_ref.update({"empresas": list(empresas)})
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
