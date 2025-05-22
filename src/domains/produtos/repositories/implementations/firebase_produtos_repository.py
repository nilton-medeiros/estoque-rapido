import logging
from typing import Tuple, List # Usar List explicitamente para type hints

from firebase_admin import firestore
from firebase_admin import exceptions

from src.domains.produtos.models import Produto
from src.domains.produtos.repositories import ProdutosRepository
from src.shared import deepl_translator
from storage.data import get_firebase_app

logger = logging.getLogger(__name__)

class FirebaseProdutosRepository(ProdutosRepository):
    def __init__(self, company_id: str):
        """
        Inicializa o cliente do Firebase Firestore e define a coleção 'produtos'
        para uma empresa específica.

        Args:
            company_id (str): O ID do documento da empresa pai na coleção 'empresas'.
        """
        get_firebase_app() # Garante que o aplicativo Firebase esteja inicializado
        self.db = firestore.client()
        self.products_collection_ref = self.db.collection('empresas').document(company_id).collection('produtos')

    def save(self, produto: Produto) -> str | None:
        """
        Salva um produto no banco de dados Firestore.

        Esta operação pode ser uma criação ou atualização, dependendo se o produto.id
        já existe no Firestore. Campos de timestamp como 'created_at' e 'updated_at'
        são gerenciados pelo servidor Firestore.

        Args:
            produto (Produto): A instância do produto a ser salva.

        Returns:
            str: O ID do documento do produto salvo, ou None se a operação de salvamento
                 ou a subsequente releitura dos timestamps falhar.
        """
        try:
            data_to_save = produto.to_dict_db()

            # Define created_at apenas na criação inicial
            if not data_to_save.get("created_at"):
                data_to_save['created_at'] = firestore.SERVER_TIMESTAMP # type: ignore [attr-defined]

            # updated_at é sempre definido/atualizado com o timestamp do servidor
            data_to_save['updated_at'] = firestore.SERVER_TIMESTAMP # type: ignore [attr-defined]

            # Gerencia os timestamps de status (ACTIVE, DELETED, INACTIVE)
            if data_to_save.get("status") == 'ACTIVE' and not data_to_save.get("activated_at"):
                data_to_save['activated_at'] = firestore.SERVER_TIMESTAMP # type: ignore [attr-defined]

            if data_to_save.get("status") == 'DELETED' and not data_to_save.get("deleted_at"):
                data_to_save['deleted_at'] = firestore.SERVER_TIMESTAMP # type: ignore [attr-defined]

            if data_to_save.get("status") == 'INACTIVE' and not data_to_save.get("inactivated_at"):
                data_to_save['inactivated_at'] = firestore.SERVER_TIMESTAMP # type: ignore [attr-defined]

            doc_ref = self.products_collection_ref.document(produto.id)
            doc_ref.set(data_to_save, merge=True) # Chamada síncrona

            # Após salvar, lê o documento de volta para obter os timestamps resolvidos
            try:
                doc_snapshot = doc_ref.get() # Chamada síncrona

                if not doc_snapshot.exists:
                    logger.warning(
                        f"Documento {produto.id} não encontrado imediatamente após o set para releitura dos timestamps."
                    )
                    return None # Retorna None, pois o produto não foi confirmado ou não pôde ser relido.

                # Re-hidrata o objeto 'produto' em memória com os dados do DB (que incluem os timestamps reais)
                product_data_from_db = doc_snapshot.to_dict()

                # Garante que o ID esteja presente no dicionário antes de passar para from_dict
                product_data_from_db['id'] = doc_snapshot.id

                # Cria um novo objeto Produto a partir dos dados do DB
                # e transfere os timestamps reais para o objeto 'produto' original
                # que foi passado para o método 'save'.
                updated_produto_obj = Produto.from_dict(product_data_from_db)

                produto.created_at = updated_produto_obj.created_at
                produto.updated_at = updated_produto_obj.updated_at
                produto.activated_at = updated_produto_obj.activated_at
                produto.deleted_at = updated_produto_obj.deleted_at
                produto.inactivated_at = updated_produto_obj.inactivated_at

            except Exception as e_read:
                logger.error(
                    f"Erro ao reler o documento {produto.id} para atualizar timestamps no objeto em memória: {str(e_read)}"
                )
                # A operação de save principal foi bem-sucedida, mas a releitura falhou.
                # O objeto 'produto' em memória não terá os timestamps reais, mas o registro no DB está correto.
                return produto.id # Ainda retorna o ID, pois o save no DB foi OK.

        except exceptions.FirebaseError as e:
            # Tratamento de erros específicos do Firebase
            if e.code == 'invalid-argument':
                logger.error(f"Argumento inválido fornecido: {e}")
            elif e.code == 'not-found':
                logger.error(f"Documento ou recurso não encontrado: {e}")
            elif e.code == 'permission-denied':
                logger.error(f"Permissão negada para realizar a operação: {e}")
            elif e.code == 'resource-exhausted':
                logger.error(f"Cota do Firebase excedida: {e}")
            else:
                logger.error(f"Erro desconhecido do Firebase: {e.code} - {e}")

            # Traduz e re-lança a exceção para que a camada de aplicação possa lidar com ela
            translated_error = deepl_translator(str(e))
            raise Exception(f"Erro ao salvar produto: {translated_error}")
        except Exception as e:
            # Captura outros erros inesperados
            logger.error(f"Erro inesperado ao salvar produto: {e}")
            raise

        return produto.id

    def get_by_id(self, produto_id: str) -> Produto | None:
        """
        Encontra um produto pelo ID no repositório.

        Args:
            produto_id (str): O ID do produto a ser buscado.

        Returns:
            Produto: A instância do Produto encontrada, ou None se não existir.

        Raises:
            Exception: Se ocorrer um erro inesperado durante a operação.
        """
        try:
            doc_ref = self.products_collection_ref.document(produto_id)
            doc_snapshot = doc_ref.get() # Chamada síncrona

            if not doc_snapshot.exists:
                logger.info(f"Produto com ID {produto_id} não encontrado.")
                return None

            product_data = doc_snapshot.to_dict()
            if not product_data: # Verifica se o documento não está vazio
                logger.warning(f"Documento {produto_id} existe mas está vazio.")
                return None

            product_data['id'] = doc_snapshot.id # Inclui o ID no dicionário

            return Produto.from_dict(product_data)

        except exceptions.FirebaseError as e:
            logger.error(f"Erro do Firebase ao buscar produto por ID {produto_id}: Código: {e.code}, Detalhes: {e}")
            raise # Re-lança para tratamento em camadas superiores
        except Exception as e:
            logger.error(f"Erro inesperado ao buscar produto por ID {produto_id}: {e}")
            raise

    def get_all(self, status_deleted: bool = False) -> Tuple[List[Produto], int]:
        """
        Obtém todos os produtos de uma empresa no repositório, com opção de filtrar por status.

        Args:
            status_deleted (bool): Se True, apenas os produtos com status "DELETED" serão incluídos;
                                    caso contrário, todos os produtos, exceto os excluídos, serão retornados.

        Returns (tuple):
            list[Produto]: Lista dos produtos que correspondem ao critério de filtro.
            int: Quantidade total de produtos marcados como "DELETED" (para o tooltip da lixeira).

        Raises:
            ValueError: Se houver um erro de validação ao buscar produtos.
            Exception: Se ocorrer um erro inesperado durante a operação.
        """
        try:
            # Obtém todos os documentos para permitir a contagem de deletados de forma eficiente
            # e o filtro subsequente.
            query_snapshot = self.products_collection_ref.get() # Chamada síncrona

            produtos_result: List[Produto] = []
            quantify_deleted = 0

            for doc in query_snapshot:
                product_data = doc.to_dict()
                if product_data: # Garante que o documento não esteja vazio
                    product_data['id'] = doc.id

                    product_obj = Produto.from_dict(product_data)

                    # Conta todos os produtos deletados, independentemente do filtro principal
                    if product_obj.status == "DELETED":
                        quantify_deleted += 1

                    # Adiciona o produto à lista de resultados com base no filtro 'status_deleted'
                    if status_deleted and product_obj.status == "DELETED":
                        produtos_result.append(product_obj)
                    elif not status_deleted and product_obj.status != "DELETED":
                        produtos_result.append(product_obj)

            return produtos_result, quantify_deleted

        except exceptions.FirebaseError as e:
            if e.code == 'permission-denied':
                logger.warning(
                    f"Permissão negada ao consultar lista de produtos da empresa logada: {e}"
                )
            elif e.code == 'unavailable':
                logger.error(
                    f"Serviço do Firestore indisponível ao consultar lista de produtos da empresa logada: {e}"
                )
                raise Exception(
                    f"Serviço do Firestore temporariamente indisponível."
                )
            else:
                logger.error(
                    f"Erro do Firebase ao consultar lista de produtos da empresa logada: Código: {e.code}, Detalhes: {e}"
                )
            raise # Re-lança para tratamento em camadas superiores
        except Exception as e:
            logger.error(
                f"Erro inesperado ao consultar lista de produtos da empresa logada: {e}"
            )
            raise
