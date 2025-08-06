import logging
from typing import Any, Tuple, List # Usar List explicitamente para type hints

# from google.cloud.firestore_v1.base_query import FieldFilter
from google.cloud.firestore_v1.base_query import FieldFilter
from google.api_core import exceptions as google_api_exceptions
from firebase_admin import exceptions, firestore

from src.domains.produtos.models import Produto
from src.domains.shared import RegistrationStatus
from src.domains.produtos.repositories import ProdutosRepository
from src.shared.utils import deepl_translator
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
        self.products_collection_ref = (self.db.collection('empresas')
                                        .document(company_id)
                                        .collection('produtos'))

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
            if data_to_save.get("status") == RegistrationStatus.ACTIVE.name and not data_to_save.get("activated_at"):
                data_to_save['activated_at'] = firestore.SERVER_TIMESTAMP # type: ignore [attr-defined]

            if data_to_save.get("status") == RegistrationStatus.DELETED.name and not data_to_save.get("deleted_at"):
                data_to_save['deleted_at'] = firestore.SERVER_TIMESTAMP # type: ignore [attr-defined]

            if data_to_save.get("status") == RegistrationStatus.INACTIVE.name and not data_to_save.get("inactivated_at"):
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
                if product_data_from_db: # Adicionada verificação para evitar erro se to_dict() retornar None
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
                else:
                    logger.warning(
                        f"Documento {produto.id} retornou dados vazios após o set para releitura dos timestamps."
                    )
                    return produto.id # O save ocorreu, mas a releitura para atualizar o objeto em memória falhou em obter dados.


            except Exception as e_read:
                logger.error(
                    f"Erro ao reler o documento {produto.id} para atualizar timestamps no objeto em memória: {str(e_read)}"
                )
                # A operação de save principal foi bem-sucedida, mas a releitura falhou.
                # O objeto 'produto' em memória não terá os timestamps reais, mas o registro no DB está correto.
                return produto.id # Ainda retorna o ID, pois o save no DB foi OK.

        except exceptions.FirebaseError as e:
            # Tratamento de erros específicos do Firebase
            if hasattr(e, 'code') and e.code == 'invalid-argument': # Adicionado hasattr para segurança
                logger.error(f"Argumento inválido fornecido: {e}")
            elif hasattr(e, 'code') and e.code == 'not-found':
                logger.error(f"Documento ou recurso não encontrado: {e}")
            elif hasattr(e, 'code') and e.code == 'permission-denied':
                logger.error(f"Permissão negada para realizar a operação: {e}")
            elif hasattr(e, 'code') and e.code == 'resource-exhausted':
                logger.error(f"Cota do Firebase excedida: {e}")
            else:
                logger.error(f"Erro desconhecido do Firebase: {getattr(e, 'code', 'N/A')} - {e}")

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
            logger.error(f"Erro do Firebase ao buscar produto por ID {produto_id}: Código: {getattr(e, 'code', 'N/A')}, Detalhes: {e}")
            raise # Re-lança para tratamento em camadas superiores
        except Exception as e:
            logger.error(f"Erro inesperado ao buscar produto por ID {produto_id}: {e}")
            raise

    def get_all(self, status_deleted: bool = False) ->  tuple[list[Produto], int]:
        """
        Obtém todos os produtos de uma empresa no repositório, ordenados por nome da categoria
        e depois por nome do produto, com opção de filtrar por status.

        Args:
            status_deleted (bool): Se True, apenas os produtos com status "DELETED" serão incluídos;
                                    caso contrário, todos os produtos, exceto os excluídos, serão retornados.

        Returns (tuple):
            list[Produto]: Lista dos produtos que correspondem ao critério de filtro, ordenados.
            int: Quantidade total de produtos marcados como "DELETED".

        Raises:
            ValueError: Se houver um erro de validação ao buscar produtos.
            Exception: Se ocorrer um erro inesperado durante a operação.
        """
        try:
            # Modificação 1: Adicionar ordenação à consulta do Firestore
            # Esta consulta buscará todos os produtos e os ordenará pelo nome da categoria
            # e, em seguida, pelo nome do produto.
            # Certifique-se de ter um índice composto (categoria_name ASC, name ASC) no Firestore.
            query = (self.products_collection_ref
                     .order_by("categoria_name")
                     .order_by("name"))
            query_snapshot = query.get() # Chamada síncrona

            produtos_result: List[Produto] = []
            quantity_deleted = 0

            for doc in query_snapshot:
                product_data = doc.to_dict()
                if product_data: # Garante que o documento não esteja vazio
                    product_data['id'] = doc.id
                    product_obj = Produto.from_dict(product_data)

                    # Modificação 4: Corrigir comparação de status
                    # Conta todos os produtos deletados, independentemente do filtro principal
                    if product_obj.status == RegistrationStatus.DELETED:
                        quantity_deleted += 1

                    # Adiciona o produto à lista de resultados com base no filtro 'status_deleted'
                    if status_deleted: # Se o filtro é para mostrar deletados
                        if product_obj.status == RegistrationStatus.DELETED:
                            produtos_result.append(product_obj)
                    else: # not status_deleted (mostrar não deletados)
                        if product_obj.status != RegistrationStatus.DELETED:
                            produtos_result.append(product_obj)

            # Modificação 2: Remover ordenação em memória, pois o Firestore já fez isso.
            # produtos_result.sort(key=lambda produto: produto.categoria_name) # REMOVIDO

            return produtos_result, quantity_deleted
        except google_api_exceptions.FailedPrecondition as e:
            # Esta é a exceção específica para erros de "índice ausente".
            # A mensagem de erro 'e' já contém o link para criar o índice.
            logger.error(
                f"Erro de pré-condição ao consultar produto (provavelmente índice ausente): {e}. "
                "O Firestore requer um índice para esta consulta. "
                f"A mensagem de erro original geralmente inclui um link para criá-lo: {str(e)}"
            )
            raise Exception(
                "Erro ao buscar produto: Um índice necessário não foi encontrado no banco de dados. "
                "Verifique os logs do servidor para uma mensagem de erro do Firestore que inclui um link para criar o índice automaticamente. "
                f"Detalhe original: {str(e)}"
            )
        except exceptions.FirebaseError as e:
            if hasattr(e, 'code') and e.code == 'permission-denied':
                logger.warning(
                    f"Permissão negada ao consultar lista de produto: {e}"
                )
                # Decide se quer re-lançar ou tratar aqui. Se re-lançar, a camada superior lida.
                # Por ora, vamos re-lançar para manter o comportamento anterior.
                raise
            elif hasattr(e, 'code') and e.code == 'unavailable':
                logger.error(
                    f"Serviço do Firestore indisponível ao consultar lista de produto: {e}"
                )
                raise Exception(
                    "Serviço do Firestore temporariamente indisponível."
                )
            else:
                # Outros erros FirebaseError
                logger.error(
                    f"Erro do Firebase ao consultar lista de produto: Código: {e.code}, Detalhes: {e}"
                )
            raise  # Re-lança o FirebaseError original ou a Exception customizada

        except Exception as e:  # Captura exceções que não são FirebaseError
            # Logar o tipo da exceção pode ajudar a diagnosticar por que não foi pega antes.
            logger.error(
                f"Erro inesperado (Tipo: {type(e)}) ao consultar lista de produto: {e}"
            )
            raise

    def get_low_stock_count(self) -> int:
        """
        Obtém a quantidade de produtos ativos que necessitam de reposição no estoque.
        Um produto necessita de reposição se 'quantity_on_hand' < 'minimum_stock_level'.
        """
        low_stock_count = 0
        try:
            # Filtra por produtos com status "ACTIVE" no nível do banco de dados
            query = (self.products_collection_ref
                    .where(filter=FieldFilter("status", "==", RegistrationStatus.ACTIVE.name)))
            documents = query.stream()  # Usa stream() para iterar sobre os resultados

            for doc in documents:
                product_data = doc.to_dict()
                if product_data:
                    quantity_on_hand = product_data.get('quantity_on_hand')
                    minimum_stock_level = product_data.get('minimum_stock_level')

                    # Verifica se ambos os campos existem e são números (int ou float)
                    if (quantity_on_hand is not None and minimum_stock_level is not None and
                            isinstance(quantity_on_hand, (int, float)) and isinstance(minimum_stock_level, (int, float))):
                        # Converte para int, garantindo que valores float como 2.0 sejam tratados como 2
                        quantity_on_hand = int(quantity_on_hand)
                        minimum_stock_level = int(minimum_stock_level)

                        if quantity_on_hand < minimum_stock_level:
                            low_stock_count += 1
                    else:
                        # Loga um aviso se campos importantes estiverem faltando ou com tipo inválido
                        logger.warning(
                            f"Produto ativo ID {doc.id} possui 'quantity_on_hand' ({quantity_on_hand}, tipo: {type(quantity_on_hand)}) ou "
                            f"'minimum_stock_level' ({minimum_stock_level}, tipo: {type(minimum_stock_level)}) ausente ou com tipo inválido. Ignorando para contagem."
                        )
            return low_stock_count

        except exceptions.FirebaseError as e:
            logger.error(f"Erro do Firebase ao contar produtos com baixo estoque: Código: {getattr(e, 'code', 'N/A')}, Detalhes: {e}")
            try:
                translated_error = deepl_translator(str(e))
                raise Exception(f"Erro ao contar produtos com baixo estoque: {translated_error}")
            except Exception as te:
                logger.error(f"Erro ao traduzir mensagem de erro do Firebase: {te}")
                raise Exception(f"Erro do Firebase ao contar produtos com baixo estoque: {e}")
        except Exception as e:
            logger.error(f"Erro inesperado ao contar produtos com baixo estoque: {e}")
            raise
    