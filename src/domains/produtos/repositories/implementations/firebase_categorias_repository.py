import logging
from datetime import datetime, UTC
from typing import Any

from google.cloud.firestore_v1.base_query import FieldFilter
from firebase_admin import firestore
from firebase_admin import exceptions

from src.domains.produtos.models import ProdutoCategorias, ProdutoStatus
from src.domains.produtos.repositories import CategoriasRepository
from src.shared import deepl_translator
from storage.data import get_firebase_app

logger = logging.getLogger(__name__)

# O FirebaseCategoriasRepository immplementa a classe abstrata CategoriasRepository
# Nota: Para "não igual a", o Firestore usa "!=" com FieldFilter.

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
                query = self.collection.where(
                    filter=FieldFilter("empresa_id", "==", empresa_id)).where(
                    filter=FieldFilter("status", "==", ProdutoStatus.DELETED.name)).order_by("name")
            else:
                # Obtem todos da empresa_id
                query = self.collection.where(
                    filter=FieldFilter("empresa_id", "==", empresa_id)).order_by("name")

            docs = query.get()

            for doc in docs:
                categoria_data_dict = doc.to_dict()

                if categoria_data_dict is None:
                    logger.warning(
                        f"Documento {doc.id} em 'produto_categorias' retornou None ao ser convertido para dicionário e será ignorado."
                    )
                    continue

                # Adiciona o ID do documento ao dicionário
                categoria_data_dict['id'] = doc.id

                # Acessa o status de forma segura
                status_value = categoria_data_dict.get("status")
                if status_value is None:
                    logger.warning(
                        f"Documento {doc.id} (nome: {categoria_data_dict.get('name', '[sem nome]')}) "
                        f"não possui a chave 'status' ou o valor é None. Categoria ignorada."
                    )
                    continue

                if status_value == ProdutoStatus.DELETED.name:
                    quantify_deleted += 1
                if status_deleted or (status_value != ProdutoStatus.DELETED.name):
                    categorias.append(ProdutoCategorias.from_dict(categoria_data_dict))

            return categorias, quantify_deleted
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
                    f"Erro de pré-condição ao consultar categorias de produtos (provavelmente índice ausente): {e}. "
                    "O Firestore requer um índice para esta consulta. "
                    f"A mensagem de erro original geralmente inclui um link para criá-lo: {str(e)}"
                )
                # A mensagem 'e' já deve conter o link.
                # Re-lançar com uma mensagem mais amigável, mas instruindo a verificar os logs para o link.
                raise Exception(
                    "Erro ao buscar categorias de produtos: Um índice necessário não foi encontrado no banco de dados. "
                    "Verifique os logs do servidor para uma mensagem de erro do Firestore que inclui um link para criar o índice automaticamente. "
                    f"Detalhe original: {str(e)}"
                )
            elif hasattr(e, 'code') and e.code == 'permission-denied':
                logger.warning(
                    f"Permissão negada ao consultar lista de categorias de produtos da empresa logada: {e}"
                )
                # Decide se quer re-lançar ou tratar aqui. Se re-lançar, a camada superior lida.
                # Por ora, vamos re-lançar para manter o comportamento anterior.
                raise
            elif hasattr(e, 'code') and e.code == 'unavailable':
                logger.error(
                    f"Serviço do Firestore indisponível ao consultar lista de categorias de produtos da empresa logada: {e}"
                )
                raise Exception(
                    "Serviço do Firestore temporariamente indisponível."
                )
            else:
                # Outros erros FirebaseError
                logger.error(
                    f"Erro do Firebase ao consultar lista de categorias de produtos da empresa logada: Código: {e.code}, Detalhes: {e}"
                )
            raise # Re-lança o FirebaseError original ou a Exception customizada

        except Exception as e: # Captura exceções que não são FirebaseError
            # Logar o tipo da exceção pode ajudar a diagnosticar por que não foi pega antes.
            logger.error(
                f"Erro inesperado (Tipo: {type(e)}) ao consultar lista de categorias de produtos da empresa logada: {e}"
            )
            # Mesmo aqui, vamos verificar se, por algum motivo, um erro de índice passou batido
            error_message_lower = str(e).lower()
            if "query requires an index" in error_message_lower and "create it here" in error_message_lower:
                 logger.error(
                    f"Atenção: Um erro que parece ser de índice ausente foi capturado pelo bloco 'except Exception': {e}. "
                    "Isso é inesperado se a exceção for do tipo FirebaseError ou google.api_core.exceptions.FailedPrecondition."
                )
                # Ainda assim, levanta uma exceção que o usuário possa entender
                 raise Exception(
                    "Erro crítico ao buscar categorias de produtos: Um índice pode ser necessário (detectado em exceção genérica). "
                    "Verifique os logs do servidor para a mensagem de erro completa do Firestore. "
                    f"Detalhe original: {str(e)}"
                )
            raise


    def get_active_categorias_summary(self, empresa_id: str) -> list[dict[str, Any]]: 
        """
        Obtém um resumo (ID, nome, descrição) de todas as categorias ativas
        de uma empresa, ordenadas por nome.

        Somente as categorias com status "ACTIVE" são incluídas.

        Args:
            empresa_id (str): O ID da empresa para buscar as categorias.

        Returns:
            list[dict[str, Any]]: Uma lista de dicionários, onde cada dicionário
                                  contém 'id', 'name', e 'description' da categoria.
                                  Retorna uma lista vazia se nenhuma categoria for encontrada.

        Raises:
            ValueError: Se empresa_id for nulo ou vazio.
            Exception: Para erros de Firebase ou outros erros inesperados (re-lançados).
        """
        if not empresa_id:
            logger.error("ID da empresa não pode ser nulo ou vazio ao buscar resumo de categorias.")
            raise ValueError("ID da empresa não pode ser nulo ou vazio")

        try:
            query = self.collection.where(
                filter=FieldFilter("empresa_id", "==", empresa_id)
            ).where(
                filter=FieldFilter("status", "==", ProdutoStatus.ACTIVE.name)
            ).select(
                ("name", "description") # Campos a serem selecionados
            ).order_by("name")

            docs = query.get() # Alterado para .get()

            categorias_summary_list: list[dict[str, Any]] = [] # Alterado para list nativo
            for doc in docs:
                data = doc.to_dict()
                if data: # Boa prática verificar se data não é None
                    categorias_summary_list.append({
                        "id": doc.id,
                        "name": data.get("name"),
                        "description": data.get("description")
                    })

            return categorias_summary_list

        except exceptions.FirebaseError as e:
            logger.error(f"Erro do Firebase ao buscar resumo de categorias ativas para empresa {empresa_id}: {getattr(e, 'code', 'N/A')} - {e}")
            # Considere traduzir e re-lançar se essa for a sua política de tratamento de erros
            # translated_error = deepl_translator(str(e))
            # raise Exception(f"Erro do Firebase ao buscar resumo de categorias: {translated_error}")
            raise # Re-lança a exceção original do Firebase para ser tratada em uma camada superior
        except ValueError as ve: # Captura o ValueError levantado explicitamente
            raise ve
        except Exception as e:
            logger.error(f"Erro inesperado ao buscar resumo de categorias ativas para empresa {empresa_id}: {e}")
            raise
