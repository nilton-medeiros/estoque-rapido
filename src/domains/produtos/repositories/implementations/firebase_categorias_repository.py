import logging
from datetime import datetime, UTC

from google.cloud.firestore_v1.base_query import FieldFilter
from firebase_admin import firestore
from firebase_admin import exceptions

from src.domains.produtos.models import ProdutoCategorias
from src.domains.produtos.repositories import CategoriasRepository
from src.shared import deepl_translator
from storage.data import get_firebase_app

logger = logging.getLogger(__name__)


# O FirebaseCategoriasRepository immplementa a classe abstrata CategoriasRepository
class FirebaseCategoriasRepository(CategoriasRepository):
    def __init__(self):
        """
        Inicializa o cliente do Firebase Firestore e conecta-se à coleção 'produto_categorias'.

        Garante que o aplicativo Firebase seja inicializado antes de criar o cliente Firestore.
        """
        # fb_app = get_firebase_app()
        get_firebase_app()

        self.db = firestore.client()
        # self.transaction = self.db.transaction()
        self.collection = self.db.collection('produto_categorias')

    def save(self, categoria: ProdutoCategorias) -> str | None:
        """
        Salvar uma categoria no banco de dados Firestore.

        Args:
            categoria (ProdutoCategorias): A instância da categoria a ser salva.

        Retorna:
            str: O ID do documento da categoria salva ou None se falhar.
        """
        try:
            data_to_save = categoria.to_dict_db()

            if not data_to_save.get("created_at"):
                # Se não existe o campo created_at ou é None, atribui TIMESTAMP
                # type: ignore
                data_to_save['created_at'] = firestore.SERVER_TIMESTAMP # type: ignore
                categoria.created_at = datetime.now(UTC)  # placeholders

            # updated_at é sempre definido/atualizado com o timestamp do servidor.
            data_to_save['updated_at'] = firestore.SERVER_TIMESTAMP # type: ignore
            categoria.updated_at = datetime.now(UTC)  # placeholders

            # Se data_to_save.get("status") for 'ACTIVE' e data_to_save.get("activated_at") for None, significa que é uma entidade marcada como ACTIVE
            if data_to_save.get("status") == 'ACTIVE' and not data_to_save.get("activated_at"):
                data_to_save['activated_at'] = firestore.SERVER_TIMESTAMP # type: ignore
                categoria.activated_at = datetime.now(UTC)  # placeholders

            # SOFT DELETE: Marca a entidade como DELETADA.
            # Se data_to_save.get("status") for 'DELETED' e data_to_save.get("deleted_at") for None, significa que é uma entidade marcada como DELETED
            if data_to_save.get("status") == 'DELETED' and not data_to_save.get("deleted_at"):
                data_to_save['deleted_at'] = firestore.SERVER_TIMESTAMP # type: ignore
                categoria.deleted_at = datetime.now(UTC)  # placeholders

            # Se data_to_save.get("status") for 'INACTIVE' e data_to_save.get("inactivated_at") for None, significa que é uma entidade marcada como INACTIVE
            if data_to_save.get("status") == 'INACTIVE' and not data_to_save.get("inactivated_at"):
                data_to_save['inactivated_at'] = firestore.SERVER_TIMESTAMP # type: ignore
                categoria.inactivated_at = datetime.now(UTC)  # placeholders

            doc_ref = self.collection.document(categoria.id)
            # Insere ou atualiza o documento na coleção 'produto_categorias'
            doc_ref.set(  # Chamada síncrona
                data_to_save, merge=True)

            # Após salvar, lê o documento de volta para obter os timestamps resolvidos
            # e atualizar o objeto 'categoria' em memória.
            try:
                doc_snapshot = doc_ref.get()  # Chamada síncrona

                if not doc_snapshot.exists:
                    logger.warning(
                        f"Documento {categoria.id} não encontrado imediatamente após o set para releitura dos timestamps.")
                    return

                categoria_data_from_db = doc_snapshot.to_dict()

                # O SDK do Firestore converte timestamps para objetos datetime do Python ao ler.
                created_at_from_db = categoria_data_from_db.get(
                    'created_at')
                updated_at_from_db = categoria_data_from_db.get(
                    'updated_at')
                activated_at_from_db = categoria_data_from_db.get(
                    'activated_at')
                deleted_at_from_db = categoria_data_from_db.get(
                    'deleted_at')
                inactivated_at_from_db = categoria_data_from_db.get(
                    'inactivated_at')

                # Atribui de fato o valor que veio do firestore convertido
                if isinstance(created_at_from_db, datetime):
                    categoria.created_at = created_at_from_db

                if isinstance(updated_at_from_db, datetime):
                    categoria.updated_at = updated_at_from_db

                if isinstance(activated_at_from_db, datetime):
                    categoria.activated_at = activated_at_from_db

                if isinstance(deleted_at_from_db, datetime):
                    categoria.deleted_at = deleted_at_from_db

                if isinstance(inactivated_at_from_db, datetime):
                    categoria.inactivated_at = inactivated_at_from_db
            except Exception as e_read:
                logger.error(
                    f"Erro ao reler o documento {categoria.id} para atualizar timestamps no objeto em memória: {str(e_read)}")
                # A operação de save principal foi bem-sucedida.
                # O objeto 'categoria' em memória ainda terá os SERVER_TIMESTAMPs como placeholders nos campos de data.
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
            raise Exception(f"Erro ao salvar categoria: {translated_error}")

        return categoria.id


    def get_by_id(self, categoria_id: str) -> ProdutoCategorias | None:
        """Encontra uma categoria de produto pelo ID no repositório"""
        try:
            doc_ref = self.collection.document(categoria_id)
            doc_snapshot = doc_ref.get() # Chamada síncrona

            if not doc_snapshot.exists:
                logger.info(f"Categoria com ID {categoria_id} não encontrado.")
                return None

            categoria_data = doc_snapshot.to_dict()
            if not categoria_data: # Verifica se o documento não está vazio
                logger.warning(f"Documento {categoria_id} existe mas está vazio.")
                return None

            categoria_data['id'] = doc_snapshot.id # Inclui o ID no dicionário

            return ProdutoCategorias.from_dict(categoria_data)
        except exceptions.FirebaseError as e:
            logger.error(f"Erro do Firebase ao buscar categoria por ID {categoria_id}: Código: {e.code}, Detalhes: {e}")
            raise # Re-lança para tratamento em camadas superiores
        except Exception as e:
            logger.error(f"Erro inesperado ao buscar categoria por ID {categoria_id}: {e}")
            raise


    def get_all(self, empresa_id: str, status_deleted: bool = False) -> tuple[list[ProdutoCategorias], int]:
        """
        Obtém todas as categorias de produtos de uma empresa no repositório.

        Args:
            empresa_id (str): O ID da empresa para buscar as categorias.
            status_deleted (bool): Se True, apenas as categorias com status "DELETED" serão incluídas; caso contrário, todas as categorias, exceto as excluídas, serão retornadas.

        Return (tuple):
            list[ProdutoCategorias]: Lista das categorias com status de acordo com o filtro da empresa logada.
            int: Quantidade de categorias deletadas (para o tooltip da lixeira).

        Raise:
            ValueError: Se houver um erro de validação ao buscar categorias.
            Exception: Se ocorrer um erro inesperado durante a operação.
        """
        try:
            if not empresa_id:
                raise ValueError(
                    "ID da empresa logada não pode ser nulo ou vazio")

            categorias: list[ProdutoCategorias] = []
            quantify_deleted = 0
            query = None

            if status_deleted:
                # Somente os deletados da empresa_id
                query = self.collection.where(filter=FieldFilter("empresa_id", "==", empresa_id)).where(
                    filter=FieldFilter("status", "==", "DELETED"))
            else:
                # Obtem todos da empresa_id
                query = self.collection.where(
                    filter=FieldFilter("empresa_id", "==", empresa_id))

            docs = query.get()

            for doc in docs:
                categoria_data = doc.to_dict()
                categoria_data['id'] = doc.id  # type: ignore

                if categoria_data["status"] == "DELETED":  # type: ignore
                    quantify_deleted += 1
                if status_deleted or (categoria_data['status'] != "DELETED"): # type: ignore
                    categorias.append(ProdutoCategorias.from_dict(
                        categoria_data))  # type: ignore

            # Ordena pelo nome da categoria
            categorias.sort(key=lambda categoria: categoria.name)

            return categorias, quantify_deleted
        except exceptions.FirebaseError as e:
            if e.code == 'permission-denied':
                logger.warning(
                    f"Permissão negada ao consultar lista de categorias da empresa logada: {e}")
            elif e.code == 'unavailable':
                logger.error(
                    f"Serviço do Firestore indisponível ao consultar lista de categorias da empresa logada: {e}")
                raise Exception(
                    f"Serviço do Firestore temporariamente indisponível.")
            else:
                logger.error(
                    f"Erro do Firebase ao consultar lista de categorias da empresa logada: Código: {e.code}, Detalhes: {e}")
            raise  # Re-lançar a exceção para tratamento em camadas superiores
        except Exception as e:
            # Captura outros erros inesperados (problemas de rede, etc.)
            logger.error(
                f"Erro inesperado ao consultar lista de categorias da empresa logada: {e}")
            raise
