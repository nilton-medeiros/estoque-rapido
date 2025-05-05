import logging
from enum import Enum  # Certifique-se de importar o módulo 'Enum'

from typing import Optional

# from google.cloud.firestore import Query
from google.cloud.firestore_v1.base_query import FieldFilter
from firebase_admin import firestore
from firebase_admin import exceptions

from src.domains.empresas.models.cnpj import CNPJ  # Importação direta
from src.domains.empresas.models.empresa_model import Empresa  # Importação direta
from src.domains.empresas.models.empresa_subclass import Status
from src.domains.empresas.repositories.contracts.empresas_repository import EmpresasRepository
from src.shared import deepl_translator
from storage.data.firebase.firebase_initialize import get_firebase_app

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

    async def save(self, empresa: Empresa) -> str:
        """
        Salvar uma empresa no banco de dados Firestore.

        O ID (empresa_id) é o próprio CNPJ, o Firestore Insere se não existir ou atualiza se existir.
        Garante a unicidade do CNPJ no banco de dados.

        Args:
            empresa (Empresa): A instância da empresa a ser salva.

        Retorna:
            str: O ID do documento da empresa salva.
        """
        try:
            # Insere ou atualiza o documento na coleção 'empresas'
            await self.collection.document(empresa.id).set(
                empresa.to_dict_db(), merge=True)
            return empresa.id  # Garante que o ID retornado seja o ID real do documento
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

    async def find_by_id(self, id: str) -> Optional[Empresa]:
        """
        Encontrar uma empresa pelo seu identificador único.
        O fato do sistema estar de posse do ID, significa que não precisa filtrar empresa por status ativo

        Args:
            id (str): O identificador único da empresa.

        Retorna:
            Optional[Empresa]: Uma instância da empresa se encontrada, None caso contrário.
        """
        try:
            doc = await self.collection.document(id).get()
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

    async def find_by_cnpj(self, cnpj: CNPJ) -> Optional[Empresa]:
        """
        Encontrar uma empresa pelo seu CNPJ.
        O módulo que solicitou a empresa pelo CNPJ deve tratar o status da empresa. (ATIVO, ARQUIVADO E DELETADO)

        Args:
            cnpj (CNPJ): O CNPJ da empresa a ser encontrada.

        Retorna:
            Optional[Empresa]: Uma instância da empresa se encontrada, None caso contrário.

        Levanta:
            Exception: Se ocorrer um erro no Firebase ou outro erro inesperado durante a busca.
        """
        try:
            query = self.collection.where(filter=FieldFilter(
                "cnpj", "==", cnpj.raw_cnpj)).limit(1)
            docs_snapshot = await query.get()

            if docs_snapshot.docs:
                doc = docs_snapshot.docs[0]  # Obtem o primeiro DocumentSnapshot
                empresa_data = doc.to_dict()
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

    async def exists_by_cnpj(self, cnpj: CNPJ) -> bool:
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
            docs_snapshot = await query.get()
            return len(docs_snapshot.docs) > 0
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

    async def find_all(self, ids_empresas: set[str] | list[str], status_active: bool = True) -> list[Empresa]:
        """
        Faz uma busca de todas as empresas que estão na lista de ids_empresas e pelo seu status.

        Args:
            ids_empresas (set[str]): Lista dos IDs de documentos das empresas do usuário logado.
            status_active (bool): Status requerido (ACTIVE, ARCHIVED ou DELETED)

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
            for empresa_id in ids_empresas_list:
                doc_ref = self.collection.document(empresa_id)
                doc = await doc_ref.get()
                if doc.exists:
                    # Filtra somente as empresas ativas ou somente as empresas não ativas (arquivadas ou deletadas)
                    empresa_data = doc.to_dict()
                    if (status_active and empresa_data.get('status') == 'ACTIVE') or (not status_active and empresa_data.get('status') != 'ACTIVE'):
                        # Adicionar o ID do documento ao dicionário antes de converter para objeto Empresa
                        empresa_data['id'] = doc.id
                        empresas.append(Empresa.from_dict(empresa_data))
                else:
                    logger.warning(
                        f"Documento com ID {empresa_id} não encontrado")

            # Ordenar a lista de empresas por corporate_name
            empresas.sort(key=lambda empresa: empresa.corporate_name)

            return empresas
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

    async def update_status(self, empresa_id: str, status: Status) -> bool:
        """
        Altera o status de uma empresa pelo seu identificador único para DELETED.
        Esta aplicação não exclui efetivamente o registro, apenas altera seu status.
        A exclusão definitiva ocorrerá após 90 dias da mudança para Status.DELETED,
        realizada periodicamente por uma Cloud Function.

        Args:
            empresa_id (str): O identificador único da empresa.
            status (Status): O novo status da empresa.

        Retorna:
            bool: True se alteração for bem-sucedida, False caso contrário.

        Levanta:
            Exception: Se ocorrer um erro no Firebase ou outro erro inesperado durante a exclusão.
        """
        try:
            # self.collection.document(empresa_id).delete()
            if status == Status.DELETED:
                fields = {'status': status.name,
                          "deleted_at": firestore.SERVER_TIMESTAMP}
            elif status == Status.ARCHIVED:
                fields = {'status': status.name,
                          "archived_at": firestore.SERVER_TIMESTAMP}
            elif status == Status.ACTIVE:
                fields = {'status': status.name,
                          "archived_at": None, "deleted_at": None}

            await self.collection.document(empresa_id).update(fields)

            return True
        # ToDo: Corrigir respostas adequadas
        except exceptions.FirebaseError as e:
            if e.code == 'not-found':
                logger.info(
                    f"Empresa com id '{empresa_id}' não encontrada para exclusão.")
                # Retorna True pois o estado desejado (não existir) já foi atingido
                return True
            elif e.code == 'permission-denied':
                logger.error(
                    f"Permissão negada ao excluir empresa com id '{empresa_id}': {e}")
                translated_error = deepl_translator(str(e))
                raise Exception(
                    f"Erro de permissão ao excluir empresa: {translated_error}")
            elif e.code == 'unavailable':
                logger.error(
                    f"Serviço do Firestore indisponível ao excluir empresa com id '{empresa_id}': {e}")
                translated_error = deepl_translator(str(e))
                raise Exception(
                    f"Serviço do Firestore temporariamente indisponível.")
            else:
                logger.error(
                    f"Erro do Firebase ao excluir empresa com id '{empresa_id}': Código: {e.code}, Detalhes: {e}")
                translated_error = deepl_translator(str(e))
                raise Exception(f"Erro ao excluir empresa: {translated_error}")
        except Exception as e:
            logger.error(
                f"Erro inesperado ao excluir empresa com id '{empresa_id}': {str(e)}")
            translated_error = deepl_translator(str(e))
            raise Exception(
                f"Erro inesperado ao excluir empresa: {translated_error}")

    async def count_inactivated(self, ids_empresas: set[str] | list[str]) -> int:
        """Conta as empresas inativas (deletadas ou arquivadas) dentro do conjunto ou lista de ids_empresas do usuário logado."""
        try:
            # Se o argumento ids_empresas for um conjunto (set), converte para lista
            ids_empresas_list = list(ids_empresas)

            # Buscar documentos diretamente pelos IDs
            query = self.collection.where(filter=FieldFilter(
                "id", "in", ids_empresas_list)).where(filter=FieldFilter("status" "<>", "ACTIVE"))
            # A construção da query é sincrona, mas o get() é assincrono, precisa do await
            docs_snapshot = await query.get()
            return len(docs_snapshot.docs)

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
