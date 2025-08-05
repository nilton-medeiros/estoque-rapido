import logging
import datetime

from google.cloud.firestore_v1.base_query import FieldFilter
from firebase_admin import exceptions, firestore
from google.api_core import exceptions as google_api_exceptions

from src.domains.pedidos.models.pedidos_model import Pedido
from src.domains.pedidos.models.pedidos_subclass import DeliveryStatus
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

    def save_pedido(self, pedido: Pedido) -> Pedido | None:
        """
        Adiciona um novo pedido ou altera um existente ao Firestore.
        Realiza baixa de estoque quando necessário usando transação atômica.
        """
        try:
            # Obtém e incrementa o número do pedido antes de salvar caso seja um novo pedido
            if not pedido.order_number:  # Garante que só obtenha um novo número se não houver um já atribuído
                pedido.order_number = self.get_next_pedido_number(
                    pedido.empresa_id)

            # Verifica se é necessário realizar baixa de estoque
            needs_stock_reduction = (
                not pedido.stock_reduction and
                pedido.delivery_status in [DeliveryStatus.IN_TRANSIT, DeliveryStatus.DELIVERED]
            )

            if needs_stock_reduction:
                # Usa transação para garantir atomicidade entre baixa de estoque e salvamento do pedido
                return self._save_pedido_with_stock_reduction(pedido)
            else:
                # Salva apenas o pedido sem alteração de estoque
                return self._save_pedido_only(pedido)

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

    def _save_pedido_with_stock_reduction(self, pedido: Pedido) -> Pedido | None:
        """
        Salva o pedido e realiza baixa de estoque em uma transação atômica.
        """
        @firestore.transactional  # type: ignore [attr-defined]
        def save_with_stock_transaction(transaction):
            # 1. Verifica disponibilidade de estoque para todos os itens antes de qualquer alteração
            produtos_refs = {}
            produtos_data = {}

            for item in pedido.items:
                produto_ref = (self.db.collection("empresas")
                               .document(pedido.empresa_id)
                               .collection("produtos")
                               .document(item.product_id))
                produtos_refs[item.product_id] = produto_ref

                # Busca o produto atual
                produto_doc = produto_ref.get(transaction=transaction)
                if not produto_doc.exists:
                    raise ValueError(f"Produto {item.product_id} não encontrado.")

                produto_data = produto_doc.to_dict()
                produtos_data[item.product_id] = produto_data

                # Verifica se há estoque suficiente
                current_stock = produto_data.get('quantity_on_hand', 0)
                if current_stock < item.quantity:
                    raise ValueError(
                        f"Estoque insuficiente para o produto '{item.description}'. "
                        f"Disponível: {current_stock}, Solicitado: {item.quantity}"
                    )

            # 2. Se chegou até aqui, há estoque suficiente para todos os itens
            # Realiza a baixa de estoque para cada item
            for item in pedido.items:
                produto_ref = produtos_refs[item.product_id]
                produto_data = produtos_data[item.product_id]

                # Calcula o novo estoque
                new_stock = produto_data['quantity_on_hand'] - item.quantity

                # Prepara os dados de atualização do produto
                produto_updates = {
                    'quantity_on_hand': new_stock,
                    'updated_at': firestore.SERVER_TIMESTAMP  # type: ignore [attr-defined]
                }

                # Atualiza o produto
                transaction.update(produto_ref, produto_updates)

                logger.info(
                    f"Estoque do produto {item.product_id} reduzido em {item.quantity} unidades. "
                    f"Estoque atual: {new_stock}"
                )

            # 3. Marca que a baixa de estoque foi realizada
            pedido.stock_reduction = True

            # 4. Salva o pedido
            pedido_data = self._prepare_pedido_data_for_save(pedido)
            pedido_ref = self.pedidos_collection.document(pedido.id)
            transaction.set(pedido_ref, pedido_data)

            return pedido_ref

        try:
            # Executa a transação
            pedido_ref = save_with_stock_transaction(self.db.transaction())

            # Relê o pedido salvo para obter os timestamps atualizados
            return self._read_saved_pedido(pedido_ref, pedido)

        except ValueError as e:
            # Erros de negócio (estoque insuficiente, produto não encontrado)
            logger.error(f"Erro de validação ao salvar pedido com baixa de estoque: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Erro na transação de salvamento com baixa de estoque: {str(e)}")
            raise

    def _save_pedido_only(self, pedido: Pedido) -> Pedido | None:
        """
        Salva apenas o pedido, sem alteração de estoque.
        """
        # Prepara os dados do pedido para salvamento
        pedido_data = self._prepare_pedido_data_for_save(pedido)

        # Salva o pedido no Firestore
        pedido_ref = self.pedidos_collection.document(pedido.id)
        pedido_ref.set(pedido_data)

        # Relê o pedido salvo para obter os timestamps atualizados
        return self._read_saved_pedido(pedido_ref, pedido)

    def _prepare_pedido_data_for_save(self, pedido: Pedido) -> dict:
        """
        Prepara os dados do pedido para salvamento no Firestore.
        """
        # Os itens do pedido são convertidos em uma lista (items) de dict pelo método to_dict_db() para o Firestore
        pedido_data = pedido.to_dict_db()

        # Firestore não suporta nativamente objetos `datetime.date`.
        # É necessário convertê-los para `datetime.datetime` antes de salvar.
        client_birthday = pedido_data.get('client_birthday')
        if client_birthday and isinstance(client_birthday, datetime.date) and not isinstance(client_birthday, datetime.datetime):
            # Converte a data para um datetime à meia-noite.
            pedido_data['client_birthday'] = datetime.datetime.combine(client_birthday, datetime.time.min)

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

        return pedido_data

    def _read_saved_pedido(self, pedido_ref, original_pedido: Pedido) -> Pedido | None:
        """
        Relê o pedido salvo para obter os timestamps atualizados.
        """
        try:
            doc_snapshot = pedido_ref.get()  # Chamada síncrona

            if not doc_snapshot.exists:
                logger.warning(
                    f"Documento {original_pedido.id} não encontrado imediatamente após o set para releitura dos timestamps."
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
            return updated_pedido_obj

        except Exception as e_read:
            logger.error(
                f"Erro ao reler o documento {original_pedido.id} para atualizar timestamps no objeto em memória: {str(e_read)}"
            )
            # A operação de save principal foi bem-sucedida, mas a releitura falhou.
            # O objeto 'pedido' em memória não terá os timestamps reais, mas o registro no DB está correto.
            # Ainda retorna o pedido original, pois o save no DB foi OK.
            return original_pedido

    # ... resto dos métodos permanecem inalterados ...

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
            query = (self.pedidos_collection
                     .where(filter=FieldFilter("empresa_id", "==", empresa_id)))
            if status:
                # Filtros para somente pedidos 'ACTIVE' ou 'INACTIVE', não haverá contagem de deletados
                query = query.where(filter=FieldFilter("status", "==", status.name))
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
        except google_api_exceptions.FailedPrecondition as e:
            # Esta é a exceção específica para erros de "índice ausente".
            # A mensagem de erro 'e' já contém o link para criar o índice.
            logger.error(
                f"Erro de pré-condição ao consultar pedido (provavelmente índice ausente): {e}. "
                "O Firestore requer um índice para esta consulta. "
                f"A mensagem de erro original geralmente inclui um link para criá-lo: {str(e)}"
            )
            raise Exception(
                "Erro ao buscar pedido: Um índice necessário não foi encontrado no banco de dados. "
                "Verifique os logs do servidor para uma mensagem de erro do Firestore que inclui um link para criar o índice automaticamente. "
                f"Detalhe original: {str(e)}"
            )
        except exceptions.FirebaseError as e:
            if hasattr(e, 'code') and e.code == 'permission-denied':
                logger.warning(
                    f"Permissão negada ao consultar lista de pedido: {e}"
                )
                # Decide se quer re-lançar ou tratar aqui. Se re-lançar, a camada superior lida.
                # Por ora, vamos re-lançar para manter o comportamento anterior.
                raise
            elif hasattr(e, 'code') and e.code == 'unavailable':
                logger.error(
                    f"Serviço do Firestore indisponível ao consultar lista de pedido: {e}"
                )
                raise Exception(
                    "Serviço do Firestore temporariamente indisponível."
                )
            else:
                # Outros erros FirebaseError
                logger.error(
                    f"Erro do Firebase ao consultar lista de pedido: Código: {e.code}, Detalhes: {e}"
                )
            raise  # Re-lança o FirebaseError original ou a Exception customizada

        except Exception as e:  # Captura exceções que não são FirebaseError
            # Logar o tipo da exceção pode ajudar a diagnosticar por que não foi pega antes.
            logger.error(
                f"Erro inesperado (Tipo: {type(e)}) ao consultar lista de pedido: {e}"
            )
            raise

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
