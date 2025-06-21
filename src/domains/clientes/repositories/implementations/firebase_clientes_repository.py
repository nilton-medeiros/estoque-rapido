import logging

from google.cloud.firestore_v1.base_query import FieldFilter
from firebase_admin import exceptions, firestore

from src.domains.clientes.models.cliente_model import Cliente
from src.domains.clientes.repositories.contracts.clientes_repository import ClientesRepository
from src.shared.utils.deep_translator import deepl_translator
from storage.data import get_firebase_app

logger = logging.getLogger(__name__)


class FirebaseClientesRepository(ClientesRepository):
    """
    Repositório para gerenciar clientes utilizando o Firebase Firestore.

    Esta classe fornece métodos para realizar operações de CRUD em dados de clientes
    armazenados em banco de dados Firestore.
    """
    def __init__(self, empresa_id: str) -> None:
        """
        Inicializa o cliente Firebase Firestore e conecta-se à coleção de clientes.

        Args:
            empresa_id (str): O ID da empresa logada, utilizado em quase todos os métodos.

        Returns: None
        """
        get_firebase_app()
        self.db = firestore.client()
        self.collection = self.db.collection('clientes')
        self.empresa_id = empresa_id


    def save(self, cliente: Cliente) -> str | None:
        """
        Cria ou atualiza um cliente no banco de dados.
        Caso for criar o registro, o ID já foi gerado em controllers

        Args:
            cliente (Cliente): A instância do cliente a ser salvo.

        Return:
            str: O ID do cliente criado ou atualizado ou None se ocorrer um erro.
        """
        if cliente.id is None:
            raise Exception("Erro ao salvar cliente: O ID do cliente não pode ser nulo")

        try:
            cliente_data = cliente.to_dict_db()

            if not cliente_data.get("created_at"):
                cliente_data["created_at"] = firestore.SERVER_TIMESTAMP  # type: ignore [attr-defined]

            cliente_data["updated_at"] = firestore.SERVER_TIMESTAMP  # type: ignore [attr-defined]

            if cliente_data.get("status") == "ACTIVE" and not cliente_data.get("activated_at"):
                cliente_data["activated_at"] = firestore.SERVER_TIMESTAMP  # type: ignore [attr-defined]

            if cliente_data.get("status") == "DELETED" and not cliente_data.get("deleted_at"):
                cliente_data["deleted_at"] = firestore.SERVER_TIMESTAMP  # type: ignore [attr-defined]

            if cliente_data.get("status") == "INACTIVE" and not cliente_data.get("inactivated_at"):
                cliente_data["inactivated_at"] = firestore.SERVER_TIMESTAMP  # type: ignore [attr-defined]

            doc_ref = self.collection.document(cliente.id)
            doc_ref.set(cliente_data, merge=True)

            try:
                doc_snapshot = doc_ref.get()

                if not doc_snapshot.exists:
                    logger.warning(f"Documento {cliente.id} não encontrado imediatamente após o set para releitura dos timestamps.")
                    return None

                cliente_data_from_db = doc_snapshot.to_dict()

                cliente_data_from_db["id"] = doc_snapshot.id

                updated_cliente_obj = Cliente.from_dict(cliente_data_from_db)

                cliente.created_at = updated_cliente_obj.created_at
                cliente.updated_at = updated_cliente_obj.updated_at
                cliente.activated_at = updated_cliente_obj.activated_at
                cliente.inactivated_at = updated_cliente_obj.inactivated_at
                cliente.deleted_at = updated_cliente_obj.deleted_at

            except Exception as e_read:
                logger.error(f"Erro ao reler o documento {cliente.id} para atualizar timestamps: {str(e_read)}")

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
            raise Exception(f"Erro ao salvar cliente: {translated_error}")
        except Exception as e:
            # Captura erros inesperados
            translated_error = deepl_translator(str(e))
            logger.error(f"Erro inesperado ao salvar cliente: {translated_error} [{str(e)}]")
            raise

        return cliente.id


    def get_by_id(self, cliente_id: str) -> Cliente | None:
        """
        Encontra um cliente pelo seu ID no banco de dados.

        Args:
            cliente_id (str): O ID do cliente a ser encontrado.

        Returns:
            Cliente | None: Cliente encontrado ou None se não existir.

        Raises:
            Exception: Em caso de erro na operação de banco de dados.
        """
        try:
            doc_ref = self.collection.document(cliente_id).get()
            if not doc_ref.exists:
                logger.info(f"Cliente com ID {cliente_id} não encontrado.")
                return None

            cliente_data = doc_ref.to_dict()
            cliente_data["id"] = doc_ref.id
            if not cliente_data:
                logger.warning(f"Documento {cliente_id} está vazio.")
                return None

            cliente_data["id"] = doc_ref.id

            return Cliente.from_dict(cliente_data)
        except exceptions.FirebaseError as e:
            logger.error(f"Erro do Firebase ao buscar cliente por ID {cliente_id}: Código: {getattr(e, 'code', 'N/A')}, Detalhes: {e}")
            raise # Re-lança para tratamento em camadas superiores
        except Exception as e:
            logger.error(f"Erro inesperado ao buscar cliente por ID {cliente_id}: {e}")
            raise


    def get_all(self) -> tuple[list[Cliente], int]:
        """
        Obtém todos os clientes da empresa logada pelo ID self.empresa_id.

        Args:
            Sem argumentos, a empresa logada (empresa_id) foi definida no construtor (self.empresa_id).

        Returns:
            list[Cliente]: Lista de clientes.
            int: Número total de clientes marcados como "DELETED".

        Raise:
            Exception: Em caso de erro na operação de banco de dados.
        """
        try:
            query = self.collection.where(
                "empresa_id", "==", self.empresa_id).order_by("name.first_name").order_by("name.last_name")

            # ToDo: Implementar leitura de 300 registros por vez
            docs = query.stream()

            clientes_result: list[Cliente] = []
            quantidade_deletados = 0

            for doc in docs:
                clientes_data = doc.to_dict()
                clientes_data["id"] = doc.id
                clientes_result.append(Cliente.from_dict(clientes_data))

                if clientes_data["status"] == "DELETED":
                    quantidade_deletados += 1

            return clientes_result, quantidade_deletados

        except exceptions.FirebaseError as e:
            error_message_lower = str(e).lower()
            # Condição para erro de índice ausente (Failed Precondition)
            # O Firestore retorna uma mensagem específica com um link para criar o índice.
            is_missing_index_error = (
                (hasattr(e, 'code') and e.code == 'failed-precondition') or
                ("query requires an index" in error_message_lower and "create it here" in error_message_lower)
            )

            if is_missing_index_error:
                logger.error(
                    f"Erro de pré-condição ao consultar cliente (provavelmente índice ausente): {e}. "
                    "O Firestore requer um índice para esta consulta. "
                    f"A mensagem de erro original geralmente inclui um link para criá-lo: {str(e)}"
                )
                # A mensagem 'e' já deve conter o link.
                # Re-lançar com uma mensagem mais amigável, mas instruindo a verificar os logs para o link.
                raise Exception(
                    "Erro ao buscar cliente: Um índice necessário não foi encontrado no banco de dados. "
                    "Verifique os logs do servidor para uma mensagem de erro do Firestore que inclui um link para criar o índice automaticamente. "
                    f"Detalhe original: {str(e)}"
                )
            elif hasattr(e, 'code') and e.code == 'permission-denied':
                logger.warning(
                    f"Permissão negada ao consultar lista de cliente da empresa logada: {e}"
                )
                # Decide se quer re-lançar ou tratar aqui. Se re-lançar, a camada superior lida.
                # Por ora, vamos re-lançar para manter o comportamento anterior.
                raise
            elif hasattr(e, 'code') and e.code == 'unavailable':
                logger.error(
                    f"Serviço do Firestore indisponível ao consultar lista de cliente da empresa logada: {e}"
                )
                raise Exception(
                    "Serviço do Firestore temporariamente indisponível."
                )
            else:
                # Outros erros FirebaseError
                logger.error(
                    f"Erro do Firebase ao consultar lista de cliente da empresa logada: Código: {e.code}, Detalhes: {e}"
                )
            raise # Re-lança o FirebaseError original ou a Exception customizada

        except Exception as e: # Captura exceções que não são FirebaseError
            # Logar o tipo da exceção pode ajudar a diagnosticar por que não foi pega antes.
            logger.error(
                f"Erro inesperado (Tipo: {type(e)}) ao consultar lista de cliente da empresa logada: {e}"
            )
            # Mesmo aqui, vamos verificar se, por algum motivo, um erro de índice passou batido
            error_message_lower = str(e).lower()
            if "query requires an index" in error_message_lower and "create it here" in error_message_lower:
                 logger.error(
                    f"Atenção: Um erro que parece ser de índice ausente foi capturado pelo bloco 'except Exception': {e}. "
                    "Isso é inesperado se a exceção for do tipo FirebaseError ou google.api_core.exceptions.FailedPrecondition."
                 )
                #  print(f"Link de criação do índice: {str(e)}")
                 # Ainda assim, levanta uma exceção que o usuário possa entender
                 raise Exception(
                    "Erro crítico ao buscar cliente: Um índice pode ser necessário (detectado em exceção genérica). "
                    "Verifique os logs do servidor para a mensagem de erro completa do Firestore. "
                    f"Detalhe original: {str(e)}"
                 )
            raise
