import logging
from datetime import datetime, UTC
from typing import Any

from google.cloud.firestore_v1.base_query import FieldFilter
from google.api_core import exceptions as google_api_exceptions
from firebase_admin import exceptions, firestore

from src.domains.shared import RegistrationStatus
from src.domains.categorias.models import ProdutoCategorias
from src.domains.categorias.repositories import CategoriasRepository
from src.shared.utils import deepl_translator
from src.domains.shared.repositories.utils import set_audit_timestamps
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

            # Centraliza a lógica de timestamps de auditoria
            data_to_save = set_audit_timestamps(data_to_save)

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
            quantidade_deletados = 0
            query = None

            if status_deleted:
                # Somente os deletados da empresa_id
                query = (self.collection
                         .where(filter=FieldFilter("empresa_id", "==", empresa_id))
                         .where(filter=FieldFilter("status", "==", RegistrationStatus.DELETED.name))
                         .order_by("name"))
            else:
                # Obtem todos da empresa_id
                query = (self.collection
                         .where(filter=FieldFilter("empresa_id", "==", empresa_id))
                         .order_by("name"))

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

                if status_value == RegistrationStatus.DELETED.name:
                    quantidade_deletados += 1
                if status_deleted or (status_value != RegistrationStatus.DELETED.name):
                    categorias.append(ProdutoCategorias.from_dict(categoria_data_dict))

            return categorias, quantidade_deletados
        except google_api_exceptions.FailedPrecondition as e:
            # Esta é a exceção específica para erros de "índice ausente".
            # A mensagem de erro 'e' já contém o link para criar o índice.
            logger.error(
                f"Erro de pré-condição ao consultar categoria (provavelmente índice ausente): {e}. "
                "O Firestore requer um índice para esta consulta. "
                f"A mensagem de erro original geralmente inclui um link para criá-lo: {str(e)}"
            )
            raise Exception(
                "Erro ao buscar categoria: Um índice necessário não foi encontrado no banco de dados. "
                "Verifique os logs do servidor para uma mensagem de erro do Firestore que inclui um link para criar o índice automaticamente. "
                f"Detalhe original: {str(e)}"
            )
        except exceptions.FirebaseError as e:
            if hasattr(e, 'code') and e.code == 'permission-denied':
                logger.warning(
                    f"Permissão negada ao consultar lista de categoria: {e}"
                )
                # Decide se quer re-lançar ou tratar aqui. Se re-lançar, a camada superior lida.
                # Por ora, vamos re-lançar para manter o comportamento anterior.
                raise
            elif hasattr(e, 'code') and e.code == 'unavailable':
                logger.error(
                    f"Serviço do Firestore indisponível ao consultar lista de categoria: {e}"
                )
                raise Exception(
                    "Serviço do Firestore temporariamente indisponível."
                )
            else:
                # Outros erros FirebaseError
                logger.error(
                    f"Erro do Firebase ao consultar lista de categoria: Código: {e.code}, Detalhes: {e}"
                )
            raise  # Re-lança o FirebaseError original ou a Exception customizada

        except Exception as e:  # Captura exceções que não são FirebaseError
            # Logar o tipo da exceção pode ajudar a diagnosticar por que não foi pega antes.
            logger.error(
                f"Erro inesperado (Tipo: {type(e)}) ao consultar lista de categoria: {e}"
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
            query = (self.collection
                     .where(filter=FieldFilter("empresa_id", "==", empresa_id))
                     .where(filter=FieldFilter("status", "==", RegistrationStatus.ACTIVE.name))
                     .select(("name", "description")) # Campos a serem selecionados
                     .order_by("name"))

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
        except google_api_exceptions.FailedPrecondition as e:
            # Esta é a exceção específica para erros de "índice ausente".
            # A mensagem de erro 'e' já contém o link para criar o índice.
            logger.error(
                f"Erro de pré-condição ao consultar categoria (provavelmente índice ausente): {e}. "
                "O Firestore requer um índice para esta consulta. "
                f"A mensagem de erro original geralmente inclui um link para criá-lo: {str(e)}"
            )
            raise Exception(
                "Erro ao buscar categoria: Um índice necessário não foi encontrado no banco de dados. "
                "Verifique os logs do servidor para uma mensagem de erro do Firestore que inclui um link para criar o índice automaticamente. "
                f"Detalhe original: {str(e)}"
            )
        except exceptions.FirebaseError as e:
            if hasattr(e, 'code') and e.code == 'permission-denied':
                logger.warning(
                    f"Permissão negada ao consultar lista de categoria: {e}"
                )
                # Decide se quer re-lançar ou tratar aqui. Se re-lançar, a camada superior lida.
                # Por ora, vamos re-lançar para manter o comportamento anterior.
                raise
            elif hasattr(e, 'code') and e.code == 'unavailable':
                logger.error(
                    f"Serviço do Firestore indisponível ao consultar lista de categoria: {e}"
                )
                raise Exception(
                    "Serviço do Firestore temporariamente indisponível."
                )
            else:
                # Outros erros FirebaseError
                logger.error(
                    f"Erro do Firebase ao consultar lista de categoria: Código: {e.code}, Detalhes: {e}"
                )
            raise  # Re-lança o FirebaseError original ou a Exception customizada

        except Exception as e:  # Captura exceções que não são FirebaseError
            # Logar o tipo da exceção pode ajudar a diagnosticar por que não foi pega antes.
            logger.error(
                f"Erro inesperado (Tipo: {type(e)}) ao consultar lista de categoria: {e}"
            )
            raise

    def get_active_id_by_name(self, company_id: str, name: str) -> str | None:
        """
        Obtém o ID de uma categoria ativa com base em seu nome (case-insensitive), de uma empresa.

        Somente as categorias com status "ACTIVE" são incluídas.

        Args:
            company_id (str): O ID da empresa para buscar as categorias.
            name (str): O nome da categoria (já em minúsculas) a ser encontrada.

        Returns:
            str | None: O ID da categoria ativa encontrada, ou None se não for encontrada.

        Raises:
            ValueError: Se company_id ou name forem nulos ou vazios.
            Exception: Para erros de Firebase ou outros erros inesperados (re-lançados).
        """
        if not company_id:
            logger.error("ID da empresa não pode ser nulo ou vazio ao buscar ID da categoria por nome.")
            raise ValueError("ID da empresa não pode ser nulo ou vazio")
        if not name:
            logger.error("Nome da categoria não pode ser nulo ou vazio ao buscar ID da categoria.")
            raise ValueError("Nome da categoria não pode ser nulo ou vazio")

        try:
            query = (self.collection
                     .where(filter=FieldFilter("empresa_id", "==", company_id))
                     .where(filter=FieldFilter("name_lowercase", "==", name))
                     .where(filter=FieldFilter("status", "==", RegistrationStatus.ACTIVE.name))
                     .limit(1)) # Garante que pegamos apenas um, caso haja duplicidade (o que não deveria ocorrer)

            docs = query.get() # Retorna uma lista de DocumentSnapshot

            if docs: # Verifica se a lista não está vazia
                doc_snapshot = docs[0] # Pega o primeiro (e único, devido ao limit(1)) documento
                return doc_snapshot.id # Retorna o ID do documento
            else:
                logger.info(f"Nenhuma categoria ativa encontrada com o nome '{name}' para a empresa ID '{company_id}'.")
                return None

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
                    f"Erro de pré-condição ao buscar ID da categoria por nome (provavelmente índice ausente): {e}. "
                    "O Firestore requer um índice para esta consulta. "
                    f"A mensagem de erro original geralmente inclui um link para criá-lo: {str(e)}"
                )
                raise Exception(
                    "Erro ao buscar ID da categoria: Um índice necessário não foi encontrado no banco de dados. "
                    "Verifique os logs do servidor para uma mensagem de erro do Firestore que inclui um link para criar o índice automaticamente. "
                    f"Detalhe original: {str(e)}"
                )
            elif hasattr(e, 'code') and e.code == 'permission-denied':
                logger.warning(
                    f"Permissão negada ao buscar ID da categoria por nome para empresa {company_id}: {e}"
                )
                raise
            elif hasattr(e, 'code') and e.code == 'unavailable':
                logger.error(
                    f"Serviço do Firestore indisponível ao buscar ID da categoria por nome para empresa {company_id}: {e}"
                )
                raise Exception(
                    "Serviço do Firestore temporariamente indisponível."
                )
            else:
                logger.error(
                    f"Erro do Firebase ao buscar ID da categoria por nome para empresa {company_id}: Código: {e.code if hasattr(e, 'code') else 'N/A'}, Detalhes: {e}"
                )
            raise

        except Exception as e: # Captura exceções que não são FirebaseError
            logger.error(
                f"Erro inesperado (Tipo: {type(e)}) ao buscar ID da categoria por nome para empresa {company_id} e nome '{name}': {e}"
            )
            error_message_lower = str(e).lower()
            if "query requires an index" in error_message_lower and "create it here" in error_message_lower:
                 logger.error(
                    f"Atenção: Um erro que parece ser de índice ausente foi capturado pelo bloco 'except Exception' ao buscar ID da categoria: {e}. "
                )
                 raise Exception(
                    "Erro crítico ao buscar ID da categoria: Um índice pode ser necessário (detectado em exceção genérica). "
                    "Verifique os logs do servidor para a mensagem de erro completa do Firestore. "
                    f"Detalhe original: {str(e)}"
                )
            raise
