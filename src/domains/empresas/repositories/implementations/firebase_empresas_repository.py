import logging
from datetime import datetime, UTC # Adicionado para isinstance

# from google.cloud.firestore import Query
from google.cloud.firestore_v1.base_query import FieldFilter
from firebase_admin import firestore
from firebase_admin import exceptions

from src.domains.empresas.models.cnpj import CNPJ  # Importação direta
from src.domains.empresas.models.empresas_model import Empresa  # Importação direta
from src.domains.empresas.repositories.contracts.empresas_repository import EmpresasRepository
from src.shared.utils import deepl_translator
from storage.data import get_firebase_app

logger = logging.getLogger(__name__)


class FirebaseEmpresasRepository(EmpresasRepository):
    """
    Um repositório para gerenciar empresas utilizando o Firebase Firestore.

    Esta classe fornece métodos para realizar operações de CRUD em dados de empresas
    armazenados em um banco de dados Firestore.
    """

    def __init__(self):
        """
        Inicializa o cliente do Firebase Firestore e conecta-se à coleção 'empresas'.

        Garante que o aplicativo Firebase seja inicializado antes de criar o cliente Firestore.
        """
        # fb_app = get_firebase_app()
        get_firebase_app()

        self.db = firestore.client()
        # self.transaction = self.db.transaction()
        self.collection = self.db.collection('empresas')

    def save(self, empresa: Empresa) -> str|None:
        """
        Salvar uma empresa no banco de dados Firestore.

        Args:
            empresa (Empresa): A instância da empresa a ser salva.

        Retorna:
            str: O ID do documento da empresa salva.
        """
        try:
            data_to_save = empresa.to_dict_db()

            # Atenção: É responsabilidade do método .to_dict_db() da classe Empresa que remova todos os atributos None e retorna um dicionário limpo.

            # Se data_to_save.get("created_at") for None, significa que é uma nova entidade
            # e o serviço não definiu um valor, então usamos SERVER_TIMESTAMP.
            # Isso pressupõe que, para atualizações, empresa.created_at já estará
            # preenchido com seu valor existente do banco de dados.
            if not data_to_save.get("created_at"):
                # Se não existe o campo created_at ou é None, atribui TIMESTAMP
                data_to_save['created_at'] = firestore.SERVER_TIMESTAMP # type: ignore
                empresa.created_at = datetime.now(UTC)  # placeholders

            # updated_at é sempre definido/atualizado com o timestamp do servidor.
            data_to_save['updated_at'] = firestore.SERVER_TIMESTAMP # type: ignore
            empresa.updated_at = datetime.now(UTC)  # placeholders

            # Se data_to_save.get("status") for 'ACTIVE' e data_to_save.get("activated_at") for None, significa que é uma entidade marcada como ACTIVE
            if data_to_save.get("status") == 'ACTIVE' and not data_to_save.get("activated_at"):
                data_to_save['activated_at'] = firestore.SERVER_TIMESTAMP # type: ignore
                empresa.activated_at = datetime.now(UTC)  # placeholders

            # SOFT DELETE: Marca a entidade como DELETADA.
            # Se data_to_save.get("status") for 'DELETED' e data_to_save.get("deleted_at") for None, significa que é uma entidade marcada como DELETED
            if data_to_save.get("status") == 'DELETED' and not data_to_save.get("deleted_at"):
                data_to_save['deleted_at'] = firestore.SERVER_TIMESTAMP # type: ignore
                empresa.deleted_at = datetime.now(UTC)  # placeholders

            # Se data_to_save.get("status") for 'ARCHIVED' e data_to_save.get("archived_at") for None, significa que é uma entidade marcada como ARCHIVED
            if data_to_save.get("status") == 'ARCHIVED' and not data_to_save.get("archived_at"):
                data_to_save['archived_at'] = firestore.SERVER_TIMESTAMP # type: ignore
                empresa.archived_at = datetime.now(UTC)  # placeholders

            doc_ref = self.collection.document(empresa.id)
            # Insere ou atualiza o documento na coleção 'empresas'
            doc_ref.set( # Chamada síncrona
                data_to_save, merge=True)

            # Após salvar, lê o documento de volta para obter os timestamps resolvidos
            # e atualizar o objeto 'empresa' em memória.
            try:
                doc_snapshot = doc_ref.get() # Chamada síncrona
                if doc_snapshot.exists:
                    empresa_data_from_db = doc_snapshot.to_dict()

                    # O SDK do Firestore converte timestamps para objetos datetime do Python ao ler.
                    created_at_from_db = empresa_data_from_db.get('created_at')
                    updated_at_from_db = empresa_data_from_db.get('updated_at')
                    activated_at_from_db = empresa_data_from_db.get('activated_at')
                    deleted_at_from_db = empresa_data_from_db.get('deleted_at')
                    archived_at_from_db = empresa_data_from_db.get('archived_at')

                    # Atribui de fato o valor que veio do firestore convertido
                    if isinstance(created_at_from_db, datetime):
                        empresa.created_at = created_at_from_db

                    if isinstance(updated_at_from_db, datetime):
                        empresa.updated_at = updated_at_from_db

                    if isinstance(activated_at_from_db, datetime):
                        empresa.activated_at = activated_at_from_db

                    if isinstance(deleted_at_from_db, datetime):
                        empresa.deleted_at = deleted_at_from_db

                    if isinstance(archived_at_from_db, datetime):
                        empresa.archived_at = archived_at_from_db
                else:
                    logger.warning(f"Documento {empresa.id} não encontrado imediatamente após o set para releitura dos timestamps.")
            except Exception as e_read:
                logger.error(f"Erro ao reler o documento {empresa.id} para atualizar timestamps no objeto em memória: {str(e_read)}")
                # A operação de save principal foi bem-sucedida.
                # O objeto 'empresa' em memória ainda terá os SERVER_TIMESTAMPs como placeholders nos campos de data.

            return empresa.id
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
            raise Exception(f"Erro ao salvar empresa: {translated_error}")
        except Exception as e:
            # Captura erros inesperados
            logger.error(f"Erro inesperado ao salvar empresa: {str(e)}")
            translated_error = deepl_translator(str(e))
            raise Exception(
                f"Erro inesperado ao salvar empresa: {translated_error}")

    def find_by_id(self, id: str) -> Empresa | None:
        """
        Encontrar uma empresa pelo seu identificador único.
        O fato do sistema estar de posse do ID, significa que não precisa filtrar empresa por status ativo

        Args:
            id (str): O identificador único da empresa.

        Retorna:
            Empresa | None: Uma instância da empresa se encontrada, None caso contrário.
        """
        try:
            doc = self.collection.document(id).get()
            if doc.exists:
                empresa_data = doc.to_dict()
                empresa_data['id'] = doc.id
                # Cria uma estância de Empresa
                return Empresa.from_dict(empresa_data)
            return None  # Retorna None se o documento não existir
        except exceptions.FirebaseError as e:
            if e.code == 'permission-denied':
                logger.warning(
                    f"Permissão negada ao consultar empresa com id '{id}': {e}")
            elif e.code == 'unavailable':
                logger.error(
                    f"Serviço do Firestore indisponível ao consultar empresa com id '{id}': {e}")
                # Pode considerar re-lançar uma exceção específica para tratamento de disponibilidade
                raise Exception(
                    f"Serviço do Firestore temporariamente indisponível.")
            else:
                logger.error(
                    f"Erro do Firebase ao consultar empresa com id '{id}': Código: {e.code}, Detalhes: {e}")
            raise  # Re-lançar a exceção para tratamento em camadas superiores
        except Exception as e:
            # Captura outros erros inesperados (problemas de rede, etc.)
            logger.error(
                f"Erro inesperado ao consultar empresa com id '{id}': {e}")
            raise

    def find_by_cnpj(self, cnpj: CNPJ) -> Empresa | None:
        """
        Encontrar uma empresa pelo seu CNPJ.
        O módulo que solicitou a empresa pelo CNPJ deve tratar o status da empresa. (ATIVO, ARQUIVADO E DELETADO)

        Args:
            cnpj (CNPJ): O CNPJ da empresa a ser encontrada.

        Retorna:
            Empresa | None: Uma instância da empresa se encontrada, None caso contrário.

        Levanta:
            Exception: Se ocorrer um erro no Firebase ou outro erro inesperado durante a busca.
        """
        try:
            query = self.collection.where(filter=FieldFilter(
                "cnpj", "==", cnpj.raw_cnpj)).limit(1)
            docs = query.get()

            if docs:
                doc = docs[0]  # Obtem o primeiro DocumentSnapshot
                empresa_data = doc.to_dict()
                if empresa_data:
                    empresa_data['id'] = doc.id
                    # Cria uma estância de Empresa
                    return Empresa.from_dict(empresa_data)
            return None
        except exceptions.FirebaseError as e:
            if e.code == 'permission-denied':
                logger.warning(
                    f"Permissão negada ao consultar empresa com CNPJ '{str(cnpj)}': {e}")
            elif e.code == 'unavailable':
                logger.error(
                    f"Serviço do Firestore indisponível ao consultar empresa com CNPJ '{str(cnpj)}': {e}")
                # Pode considerar re-lançar uma exceção específica para tratamento de disponibilidade
                raise Exception(
                    f"Serviço do Firestore temporariamente indisponível.")
            else:
                logger.error(
                    f"Erro do Firebase ao consultar empresa com CNPJ '{str(cnpj)}': Código: {e.code}, Detalhes: {e}")
            raise  # Re-lançar a exceção para tratamento em camadas superiores
        except Exception as e:
            # Captura outros erros inesperados (problemas de rede, etc.)
            logger.error(
                f"Erro inesperado ao consultar empresa com CNPJ '{str(cnpj)}': {e}")
            raise

    def exists_by_cnpj(self, cnpj: CNPJ) -> bool:
        """
        Verificar se uma empresa existe com o CNPJ fornecido independente do status da empresa.

        Args:
            cnpj (CNPJ): O CNPJ da empresa a ser verificado.

        Retorna:
            bool: True se a empresa existir, False caso contrário.
        """
        try:
            query = self.collection.where(filter=FieldFilter(
                "cnpj", "==", cnpj.raw_cnpj)).limit(1)
            docs = query.get()
            return len(docs) > 0
        except exceptions.FirebaseError as e:
            if e.code == 'permission-denied':
                logger.warning(
                    f"Permissão negada ao consultar empresa com CNPJ '{str(cnpj)}': {e}")
            elif e.code == 'unavailable':
                logger.error(
                    f"Serviço do Firestore indisponível ao consultar empresa com CNPJ '{str(cnpj)}': {e}")
                # Pode considerar re-lançar uma exceção específica para tratamento de disponibilidade
                raise Exception(
                    f"Serviço do Firestore temporariamente indisponível.")
            else:
                logger.error(
                    f"Erro do Firebase ao consultar empresa com CNPJ '{str(cnpj)}': Código: {e.code}, Detalhes: {e}")
            raise  # Re-lançar a exceção para tratamento em camadas superiores
        except Exception as e:
            # Captura outros erros inesperados (problemas de rede, etc.)
            logger.error(
                f"Erro inesperado ao consultar empresa com CNPJ '{str(cnpj)}': {e}")
            raise

    def find_all(self, ids_empresas: set[str] | list[str], status_active: bool = True) -> tuple[list[Empresa], int]:
        """
        Faz uma busca de todas as empresas que estão na lista de ids_empresas e pelo seu status.

        Args:
            ids_empresas (set[str]): Lista dos IDs de documentos das empresas do usuário logado.
            status_active (bool): CompanyStatus requerido (ACTIVE, ARCHIVED ou DELETED)

        Return:
            list[Empresa]: Lista de empresas encontradas ou vazio se não encontrar
        Raise:
            Exception: Se ocorrer erro no Firebase ou outro erro inesperado durante a busca.
        """
        try:
            # Se o argumento ids_empresas for um conjunto (set), converte para lista
            ids_empresas_list = list(ids_empresas)

            # Buscar documentos diretamente pelos IDs
            empresas = []
            quantify_inactivated = 0

            for empresa_id in ids_empresas_list:
                doc_ref = self.collection.document(empresa_id)
                doc = doc_ref.get()
                if doc.exists:
                    empresa_data = doc.to_dict()
                    if empresa_data.get('status') != 'ACTIVE':
                        # Registra a quantidade de empresas inativadas ('ARCHIVED' ou 'DELETED')
                        quantify_inactivated += 1
                    # Filtra somente as empresas ativas ou somente as empresas não ativas (arquivadas ou deletadas)
                    if (status_active and empresa_data.get('status') == 'ACTIVE') or (not status_active and empresa_data.get('status') != 'ACTIVE'):
                        # Adicionar o ID do documento ao dicionário antes de converter para objeto Empresa
                        empresa_data['id'] = doc.id
                        empresas.append(Empresa.from_dict(empresa_data))
                else:
                    logger.warning(
                        f"Documento com ID {empresa_id} não encontrado")

            # Ordenar a lista de empresas por corporate_name
            empresas.sort(key=lambda empresa: empresa.corporate_name)

            return empresas, quantify_inactivated
        except exceptions.FirebaseError as e:
            if e.code == 'permission-denied':
                logger.warning(
                    f"Permissão negada ao consultar lista de empresas do usuário logado: {e}")
            elif e.code == 'unavailable':
                logger.error(
                    f"Serviço do Firestore indisponível ao consultar lista de empresas do usuário logado: {e}")
                raise Exception(
                    f"Serviço do Firestore temporariamente indisponível.")
            else:
                logger.error(
                    f"Erro do Firebase ao consultar lista de empresas do usuário logado: Código: {e.code}, Detalhes: {e}")
            raise  # Re-lançar a exceção para tratamento em camadas superiores
        except Exception as e:
            # Captura outros erros inesperados (problemas de rede, etc.)
            logger.error(
                f"Erro inesperado ao consultar lista de empresas do usuário logado: {e}")
            raise

    def count_inactivated(self, ids_empresas: set[str] | list[str]) -> int:
        """Conta as empresas inativas (deletadas ou arquivadas) dentro do conjunto ou lista de ids_empresas do usuário logado."""
        try:
            # Se o argumento ids_empresas for um conjunto (set), converte para lista
            ids_empresas_list = list(ids_empresas)

            # Buscar documentos diretamente pelos IDs
            query = self.collection.where(filter=FieldFilter(
                "id", "in", ids_empresas_list)).where(filter=FieldFilter("status" "<>", "ACTIVE"))
            # A construção da query é sincrona, mas o get() é assincrono, precisa do await
            docs = query.get()
            return len(docs)

        except exceptions.FirebaseError as e:
            if e.code == 'permission-denied':
                logger.warning(
                    f"Permissão negada ao consultar empresas inativas do usuário logado: {e}")
            elif e.code == 'unavailable':
                logger.error(
                    f"Serviço do Firestore indisponível ao consultar empresas inativas do usuário logado: {e}")
            elif e.code == 'invalid-argument':
                logger.error("Argumento inválido fornecido para a consulta.")
            elif e.code == 'not-found':
                logger.error("Recurso ou coleção não encontrado.")
            elif e.code == 'resource-exhausted':
                logger.error("Cota do Firebase excedida.")
            elif e.code == 'deadline-exceeded':
                logger.error("Tempo limite para a operação excedido.")
            else:
                logger.error(
                    f"Erro do Firebase ao consultar lista de empresas do usuário logado: Código: {e.code}, Detalhes: {e}")
            translated_error = deepl_translator(str(e))
            raise Exception(
                f"Erro do Firebase ao contar empresas: {translated_error}")

        except Exception as e:
            # Captura outros erros inesperados (problemas de rede, etc.)
            logger.error(
                f"Erro inesperado ao consultar empresas inativas do usuário logado: {e}")
            raise e
