import logging

from firebase_admin import exceptions, firestore

from src.domains.pedidos.models.pedidos_model import Pedido
from src.domains.pedidos.repositories.contracts.pedidos_repository import PedidosRepository
from src.domains.shared.models.registration_status import RegistrationStatus
from src.domains.shared.models.sequential_number import SequentialNumber
from src.shared.utils.deep_translator import deepl_translator
from storage.data import get_firebase_app

logger = logging.getLogger(__name__)


class FirebasePedidosRepository(PedidosRepository):
    """Repositorio de pedidos do Firestore."""
    def __init__(self):
        get_firebase_app()  # Garante que o aplicativo Firebase esteja inicializado
        self.db = firestore.client()
        self.pedidos_collection = self.db.collection("pedidos")
        self.numbers_collection_name = "numbers"  # Sub-coleção dentro de empresa

    def _get_empresa_numbers_collection(self, empresa_id: str):
        """Retorna a referência para a subcoleção 'numbers' de uma empresa específica."""
        return self.db.collection("empresas").document(empresa_id).collection(self.numbers_collection_name)

    def get_next_pedido_number(self, empresa_id: str) -> str:
        """
        Obtém o próximo número sequencial para um pedido da empresa e o incrementa.
        Usa uma transação do Firestore para garantir a atomicidade.
        """
        numbers_ref = self._get_empresa_numbers_collection(
            empresa_id).document("pedido")

        @firestore.transactional  # type: ignore [attr-defined]
        def update_next_number_transaction(transaction):
            # Abre uma transação para garantir atomicidade (É tudo ou nada!)
            snapshot = numbers_ref.get(transaction=transaction)
            if not snapshot.exists:
                # Se o documento 'pedido' não existe, cria com o primeiro número (1)
                sequential_number = SequentialNumber(
                    name="pedido",
                    next_number=1,
                    empresa_id=empresa_id
                )
                transaction.set(numbers_ref, sequential_number.to_dict_db())
                return "000001"  # Primeiro número formatado
            else:
                current_sequential_number = SequentialNumber.from_dict(
                    snapshot.to_dict())
                next_available_number = current_sequential_number.next_number
                current_sequential_number.next_number += 1
                transaction.update(
                    numbers_ref, current_sequential_number.to_dict_db())
                # Formata com 6 zeros à esquerda
                return f"{next_available_number:06d}"

        try:
            # Obtem o próximo número do pedido
            return update_next_number_transaction(self.db.transaction())
        except Exception as e:
            logger.error(
                f"Erro ao obter ou incrementar o número do pedido para empresa {empresa_id}: {e}")
            raise

    def save_pedido(self, pedido: Pedido) -> str | None:
        """Adiciona um novo pedido ou altera um existente ao Firestore."""
        try:
            # Obtém e incrementa o número do pedido antes de salvar caso seja um novo pedido
            if not pedido.order_number:  # Garante que só obtenha um novo número se não houver um já atribuído
                pedido.order_number = self.get_next_pedido_number(
                    pedido.empresa_id)

            pedido_data = pedido.to_dict_db()

            # Define created_at apenas na criação inicial
            if not pedido_data.get("created_at"):
                pedido_data['created_at'] = firestore.SERVER_TIMESTAMP  # type: ignore [attr-defined]

            # updated_at é sempre definido/atualizado com o timestamp do servidor
            pedido_data['updated_at'] = firestore.SERVER_TIMESTAMP  # type: ignore [attr-defined]

            # Gerencia os timestamps de status (ACTIVE, DELETED, INACTIVE)
            if pedido_data.get("status") == RegistrationStatus.ACTIVE.name and not pedido_data.get("activated_at"):
                pedido_data['activated_at'] = firestore.SERVER_TIMESTAMP  # type: ignore [attr-defined]

            if pedido_data.get("status") == RegistrationStatus.DELETED.name and not pedido_data.get("deleted_at"):
                pedido_data['deleted_at'] = firestore.SERVER_TIMESTAMP  # type: ignore [attr-defined]

            if pedido_data.get("status") == RegistrationStatus.INACTIVE.name and not pedido_data.get("inactivated_at"):
                pedido_data['inactivated_at'] = firestore.SERVER_TIMESTAMP  # type: ignore [attr-defined]

            # Salva o pedido no Firestore, se é um novo pedido, o pedido.id foi definido em services antes de vir para este método save
            # Se existe, faz o update, se não, cria um novo pedido no Firestore
            doc_ref = self.pedidos_collection.document(pedido.id)
            # Se update, será sem merge (merge=False), garante que o pedido no banco tenha somente os campos enviados em pedido_data
            doc_ref.set(pedido_data)

            # Após salvar, lê o documento de volta para obter os timestamps resolvidos
            try:
                doc_snapshot = doc_ref.get()  # Chamada síncrona

                if not doc_snapshot.exists:
                    logger.warning(
                        f"Documento {pedido.id} não encontrado imediatamente após o set para releitura dos timestamps."
                    )
                    # Retorna None, pois o pedido não foi confirmado ou não pôde ser relido.
                    return None

                # Re-hidrata o objeto 'pedido' em memória com os dados do DB (que incluem os timestamps reais)
                pedido_data_from_db = doc_snapshot.to_dict()

                # Garante que o ID esteja presente no dicionário antes de passar para from_dict
                pedido_data_from_db['id'] = doc_snapshot.id

                # Cria um novo objeto Pedido a partir dos dados do DB
                # e transfere os timestamps reais para o objeto 'pedido' original
                # que foi passado para o método 'save'.
                updated_pedido_obj = Pedido.from_dict(pedido_data_from_db)

                pedido.created_at = updated_pedido_obj.created_at
                pedido.updated_at = updated_pedido_obj.updated_at
                pedido.activated_at = updated_pedido_obj.activated_at
                pedido.deleted_at = updated_pedido_obj.deleted_at
                pedido.inactivated_at = updated_pedido_obj.inactivated_at

            except Exception as e_read:
                logger.error(
                    f"Erro ao reler o documento {pedido.id} para atualizar timestamps no objeto em memória: {str(e_read)}"
                )
                # A operação de save principal foi bem-sucedida, mas a releitura falhou.
                # O objeto 'pedido' em memória não terá os timestamps reais, mas o registro no DB está correto.
                # Ainda retorna o ID, pois o save no DB foi OK.
                return pedido.id

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
            raise Exception(f"Erro ao salvar pedido: {translated_error}")
        except Exception as e:
            # Captura erros inesperados
            translated_error = deepl_translator(str(e))
            logger.error(
                f"Erro inesperado ao salvar pedido: {translated_error} [{str(e)}]")
            raise

        return pedido.id

    def get_pedido_by_id(self, pedido_id: str) -> Pedido | None:
        """Busca um pedido pelo seu ID."""
        try:
            doc = self.pedidos_collection.document(pedido_id).get()
            if doc.exists:
                return Pedido.from_dict(doc.to_dict(), doc.id)
            return None
        except exceptions.FirebaseError as e:
            if e.code == 'permission-denied':
                logger.warning(
                    f"Permissão negada ao consultar pedido com id '{pedido_id}': {e}")
            elif e.code == 'unavailable':
                logger.error(
                    f"Serviço do Firestore indisponível ao consultar pedido com id '{pedido_id}': {e}")
                # Pode considerar re-lançar uma exceção específica para tratamento de disponibilidade
                raise Exception(
                    f"Serviço do Firestore temporariamente indisponível.")
            else:
                logger.error(
                    f"Erro do Firebase ao consultar pedido com id '{pedido_id}': Código: {e.code}, Detalhes: {e}")
            raise  # Re-lançar a exceção para tratamento em camadas superiores
        except Exception as e:
            # Captura outros erros inesperados (problemas de rede, etc.)
            logger.error(
                f"Erro inesperado ao consultar pedido com id '{pedido_id}': {e}")
            raise

    def get_pedidos_by_empresa_id(self, empresa_id: str, status: RegistrationStatus | None = None) -> tuple[list[Pedido], int]:
        """Busca todos os pedidos de uma empresa, opcionalmente filtrando por status."""
        try:
            query = self.pedidos_collection.where(
                "empresa_id", "==", empresa_id)
            if status:
                # Filtros para somente pedidos 'ACTIVE' ou 'INACTIVE', não haverá contagem de deletados
                query = query.where("status", "==", status.name)
            query = query.order_by("order_number")

            docs = query.get()

            pedidos_result: list[Pedido] = []
            quantidade_deletados = 0

            for doc in docs:
                pedido_data = doc.to_dict()
                if pedido_data:
                    pedido_obj = Pedido.from_dict(pedido_data, doc.id)

                    # Se for um pedido 'DELETED', independente do filtro 'status', adiciona em quantidade_deletados
                    if pedido_obj.status == RegistrationStatus.DELETED:
                        quantidade_deletados += 1

                    # Adiciona o pedido à lista de resultados com base no filtro 'status'
                    if status == RegistrationStatus.DELETED:
                        # Adiciona somente os deletados
                        pedidos_result.append(pedido_obj)
                    else:
                        # Adiciona somente os ativos e inativos, mas envia a contagem de deletados
                        if pedido_obj.status != RegistrationStatus.DELETED:
                            pedidos_result.append(pedido_obj)

            return pedidos_result, quantidade_deletados
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
                    f"Erro de pré-condição ao consultar pedidos (provavelmente índice ausente): {e}. "
                    "O Firestore requer um índice para esta consulta. "
                    f"A mensagem de erro original geralmente inclui um link para criá-lo: {str(e)}"
                )
                # A mensagem 'e' já deve conter o link.
                # Re-lançar com uma mensagem mais amigável, mas instruindo a verificar os logs para o link.
                raise Exception(
                    "Erro ao buscar pedidos: Um índice necessário não foi encontrado no banco de dados. "
                    "Verifique os logs do servidor para uma mensagem de erro do Firestore que inclui um link para criar o índice automaticamente. "
                    f"Detalhe original: {str(e)}"
                )
            elif hasattr(e, 'code') and e.code == 'permission-denied':
                logger.warning(
                    f"Permissão negada ao consultar lista de pedidos da empresa logada: {e}"
                )
                # Decide se quer re-lançar ou tratar aqui. Se re-lançar, a camada superior lida.
                # Por ora, vamos re-lançar para manter o comportamento anterior.
                raise
            elif hasattr(e, 'code') and e.code == 'unavailable':
                logger.error(
                    f"Serviço do Firestore indisponível ao consultar lista de pedidos da empresa logada: {e}"
                )
                raise Exception(
                    "Serviço do Firestore temporariamente indisponível."
                )
            else:
                # Outros erros FirebaseError
                logger.error(
                    f"Erro do Firebase ao consultar lista de pedidos da empresa logada: Código: {e.code}, Detalhes: {e}"
                )
            raise  # Re-lança o FirebaseError original ou a Exception customizada

        except Exception as e:  # Captura exceções que não são FirebaseError
            # Logar o tipo da exceção pode ajudar a diagnosticar por que não foi pega antes.
            logger.error(
                f"Erro inesperado (Tipo: {type(e)}) ao consultar lista de pedidos da empresa logada: {e}"
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
                    "Erro crítico ao buscar pedidos: Um índice pode ser necessário (detectado em exceção genérica). "
                    "Verifique os logs do servidor para a mensagem de erro completa do Firestore. "
                    f"Detalhe original: {str(e)}"
                )
            raise

    # def update_pedido(self, pedido: Pedido) -> Pedido:
    #     """Atualiza um pedido existente no Firestore."""
    #     if not pedido.id:
    #         raise ValueError("ID do pedido é necessário para atualização.")
    #     try:
    #         self.pedidos_collection.document(pedido.id).update(pedido.to_dict_db())
    #         logger.info(f"Pedido {pedido.id} atualizado com sucesso.")
    #         return pedido
    #     except Exception as e:
    #         logger.error(f"Erro ao atualizar pedido {pedido.id}: {e}")
    #         raise

    def delete_pedido(self, pedido: Pedido) -> bool:
        """Realiza um soft delete em um pedido, definindo deleted_at."""
        try:
            if not pedido.id:
                raise ValueError("ID do pedido é necessário para deleção.")

            updates = {
                # type: ignore [attr-defined]
                "deleted_at": firestore.SERVER_TIMESTAMP,  # type: ignore [attr-defined]
                "deleted_by_id": pedido.created_by_id,
                "deleted_by_name": pedido.created_by_name,
                "status": RegistrationStatus.DELETED.name
            }
            self.pedidos_collection.document(pedido.id).update(updates)
            logger.info(
                f"Pedido {pedido.id} marcado como deletado (soft delete).")
            return True
        except Exception as e:
            logger.error(f"Erro ao deletar pedido {pedido.id}: {e}")
            raise Exception(
                f"Erro inesperado ao deletar pedido com id '{pedido.id}': {e}")

    def hard_delete_pedido(self, pedido_id: str):
        """Remove um pedido completamente do Firestore (uso cauteloso)."""
        try:
            self.pedidos_collection.document(pedido_id).delete()
            logger.info(f"Pedido {pedido_id} removido permanentemente.")
        except Exception as e:
            logger.error(f"Erro ao remover pedido {pedido_id}: {e}")
            raise Exception(f"Erro inesperado ao remover pedido: {e}")

    def restore_pedido(self, pedido: Pedido) -> bool:
        """Restaura um pedido da lixeira."""
        try:
            if not pedido.id:
                raise ValueError("ID do pedido é necessário para restauração.")

            updates = {
                "activated_at": firestore.SERVER_TIMESTAMP,  # type: ignore [attr-defined]
                "activated_by_id": pedido.activated_by_id,
                "activated_by_name": pedido.activated_by_name,
                "status": RegistrationStatus.ACTIVE.name
            }
            self.pedidos_collection.document(pedido.id).update(updates)
            logger.info(
                f"Pedido {pedido.id} marcado como ACTIVE.")
            return True
        except Exception as e:
            logger.error(f"Erro ao restaurar pedido {pedido.id}: {e}")
            raise Exception(
                f"Erro inesperado ao restaurar pedido #'{pedido.order_number}': {e}")
