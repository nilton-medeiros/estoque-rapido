import logging

from firebase_admin import firestore, exceptions
from google.api_core import exceptions as google_api_exceptions

from src.domains.formas_pagamento.models.formas_pagamento_model import FormaPagamento
from src.domains.shared import RegistrationStatus
from storage.data import get_firebase_app

logger = logging.getLogger(__name__)


class FirebaseFormasPagamentoRepository:
    """
    Repositório para gerenciar as formas de pagamento de uma empresa,
    armazenadas em uma subcoleção do Firestore.

    Args: Nenhum argumento é necessário.
    """

    def __init__(self):
        get_firebase_app()
        self.db = firestore.client()
        self.empresas_collection = self.db.collection('empresas')

    def _get_subcollection_ref(self, empresa_id: str):
        """Retorna a referência para a subcoleção 'formas_pagamento' de uma empresa."""
        return self.empresas_collection.document(empresa_id).collection('formas_pagamento')

    def save(self, forma_pagamento: FormaPagamento) -> str:
        """
        Salva (cria ou atualiza) uma forma de pagamento na subcoleção da empresa.

        Args:
            forma_pagamento (FormaPagamento): O objeto da forma de pagamento a ser salvo.

        Returns:
            str: O ID do documento salvo.
        """
        try:
            subcollection_ref = self._get_subcollection_ref(forma_pagamento.empresa_id)
            data_to_save = forma_pagamento.to_dict_db()

            # Define timestamps do servidor para criação e atualização
            if not data_to_save.get('created_at'):  # Novo documento
                data_to_save['created_at'] = firestore.SERVER_TIMESTAMP # type: ignore [attr-defined]
            data_to_save['updated_at'] = firestore.SERVER_TIMESTAMP # type: ignore [attr-defined]

            # SOFT DELETE: Marca a entidade como DELETADA.
            # Se data_to_save.get("status") for 'DELETED' e data_to_save.get("deleted_at") for None, significa que é uma entidade marcada como DELETED
            if data_to_save.get("status") == RegistrationStatus.DELETED.name and not data_to_save.get("deleted_at"):
                data_to_save['deleted_at'] = firestore.SERVER_TIMESTAMP # type: ignore [attr-defined]

            # O ID pode ser o nome normalizado (ex: 'pix') ou um UUID
            doc_ref = subcollection_ref.document(forma_pagamento.id)
            doc_ref.set(data_to_save, merge=True)

            try:
                saved_id = doc_ref.id
                # Após salvar, lê o documento de volta para obter os timestamps resolvidos.
                doc_snapshot = doc_ref.get()
                if not doc_snapshot.exists:
                    # Esta é uma condição de erro inesperada. A escrita foi confirmada, mas a leitura imediata falhou.
                    logger.error(
                        f"Falha de consistência: Documento {saved_id} não encontrado imediatamente após a escrita.")
                    raise Exception(
                        f"Não foi possível confirmar o salvamento da forma de pagamento {saved_id}.")
                else:
                    data_from_db = doc_snapshot.to_dict()
                    if data_from_db:
                        # Garante que o ID está no dict
                        data_from_db['id'] = doc_snapshot.id
                        # Cria um objeto temporário para obter os timestamps resolvidos.
                        temp_fp = FormaPagamento.from_dict(data_from_db)
                        # Atualiza o objeto original com os timestamps do servidor.
                        forma_pagamento.created_at = temp_fp.created_at
                        forma_pagamento.updated_at = temp_fp.updated_at
                        forma_pagamento.deleted_at = temp_fp.deleted_at

            except Exception as e_read:
                logger.error(
                    f"Erro ao reler documento {forma_pagamento.id}: {str(e_read)}")
                raise
            # Retorna o ID que é garantidamente uma string, resolvendo o alerta do Pylance.
            return saved_id
        except exceptions.FirebaseError as e:
            logger.error(
                f"Erro do Firebase ao salvar forma de pagamento para empresa {forma_pagamento.empresa_id}: {e}")
            raise
        except Exception as e:
            logger.error(
                f"Erro inesperado ao salvar forma de pagamento para empresa {forma_pagamento.empresa_id}: {e}")
            raise

    def get_by_id(self, empresa_id: str, forma_pagamento_id: str) -> FormaPagamento | None:
        """
        Busca uma forma de pagamento específica pelo seu ID.

        Args:
            empresa_id (str): O ID da empresa proprietária.
            forma_pagamento_id (str): O ID da forma de pagamento.

        Returns:
            FormaPagamento | None: O objeto encontrado ou None.
        """
        try:
            doc_ref = self._get_subcollection_ref(
                empresa_id).document(forma_pagamento_id)
            doc = doc_ref.get()

            if not doc.exists:
                return None

            data = doc.to_dict()
            data['id'] = doc.id
            return FormaPagamento.from_dict(data)
        except Exception as e:
            logger.error(
                f"Erro ao buscar forma de pagamento {forma_pagamento_id} da empresa {empresa_id}: {e}")
            raise

    def get_all_by_empresa(self, empresa_id: str, status_deleted: bool = False) -> tuple[list[FormaPagamento], int]:
        """
        Busca todas as formas de pagamento de uma empresa, opcionalmente filtrando por status.

        Args:
            empresa_id (str): O ID da empresa.
            status (RegistrationStatus): Filtra pelo status (padrão: ACTIVE).

        Returns:
            tuple (list[FormaPagamento], int): Lista de formas de pagamento e a quantidade de deletados.
        """
        formas_pagamentos: list[FormaPagamento] = []
        quantity_deleted: int = 0

        try:
            query = self._get_subcollection_ref(empresa_id).order_by("order").order_by("name_lower")

            docs = query.get()

            for doc in docs:
                data = doc.to_dict()
                if not data:
                    continue

                data['id'] = doc.id
                fp = FormaPagamento.from_dict(data)

                if fp.status == RegistrationStatus.DELETED:
                    # Registro marcado como deletado
                    quantity_deleted += 1
                    if status_deleted:
                        # Filtro: Somente deletados
                        formas_pagamentos.append(fp)
                elif not status_deleted:
                    # Filtro: Não deletados [Ativos&Inativos] (padrão)
                    formas_pagamentos.append(fp)

            return formas_pagamentos, quantity_deleted
        except google_api_exceptions.FailedPrecondition as e:
            logger.error(
                f"Índice do Firestore ausente para a consulta de formas de pagamento: {e}")
            raise Exception(
                "Erro de configuração no banco de dados. Um índice para formas de pagamento é necessário.")
        except Exception as e:
            logger.error(
                f"Erro ao buscar formas de pagamento da empresa {empresa_id}: {e}")
            raise
