import logging
from typing import List

from google.cloud.firestore_v1.base_query import FieldFilter
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
            if not forma_pagamento.id:  # Novo documento
                data_to_save['created_at'] = firestore.SERVER_TIMESTAMP # type: ignore [attr-defined]
            data_to_save['updated_at'] = firestore.SERVER_TIMESTAMP # type: ignore [attr-defined]

            # O ID pode ser o nome normalizado (ex: 'pix') ou um UUID
            doc_ref = subcollection_ref.document(forma_pagamento.id)
            doc_ref.set(data_to_save, merge=True)

            # O ID do documento é sempre uma string após a criação/referência.
            saved_id = doc_ref.id
            forma_pagamento.id = saved_id  # Atualiza o objeto em memória
            return saved_id
        except exceptions.FirebaseError as e:
            logger.error(f"Erro do Firebase ao salvar forma de pagamento para empresa {forma_pagamento.empresa_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Erro inesperado ao salvar forma de pagamento para empresa {forma_pagamento.empresa_id}: {e}")
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
            doc_ref = self._get_subcollection_ref(empresa_id).document(forma_pagamento_id)
            doc = doc_ref.get()

            if not doc.exists:
                return None

            data = doc.to_dict()
            data['id'] = doc.id
            return FormaPagamento.from_dict(data)
        except Exception as e:
            logger.error(f"Erro ao buscar forma de pagamento {forma_pagamento_id} da empresa {empresa_id}: {e}")
            raise

    def get_all_by_empresa(self, empresa_id: str, status: RegistrationStatus = RegistrationStatus.ACTIVE) -> List[FormaPagamento]:
        """
        Busca todas as formas de pagamento de uma empresa, opcionalmente filtrando por status.

        Args:
            empresa_id (str): O ID da empresa.
            status (RegistrationStatus): Filtra pelo status (padrão: ACTIVE).

        Returns:
            List[FormaPagamento]: Uma lista com as formas de pagamento encontradas.
        """
        formas_pagamento = []
        try:
            query = (self._get_subcollection_ref(empresa_id)
                     .where(filter=FieldFilter("status", "==", status.name))
                     .order_by("ordem")
                     .order_by("nome"))

            docs = query.stream()
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                formas_pagamento.append(FormaPagamento.from_dict(data))

            return formas_pagamento
        except google_api_exceptions.FailedPrecondition as e:
            logger.error(f"Índice do Firestore ausente para a consulta de formas de pagamento: {e}")
            raise Exception("Erro de configuração no banco de dados. Um índice para formas de pagamento é necessário.")
        except Exception as e:
            logger.error(f"Erro ao buscar formas de pagamento da empresa {empresa_id}: {e}")
            raise
