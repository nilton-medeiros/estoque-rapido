import logging

from src.domains.formas_pagamento.models.formas_pagamento_model import FormaPagamento, TipoPagamento
from src.domains.formas_pagamento.repositories.implementations.firebase_formas_pagamento_repository import FirebaseFormasPagamentoRepository
from src.domains.shared import RegistrationStatus
from src.shared.utils import get_uuid

logger = logging.getLogger(__name__)


class FormasPagamentoService:
    def __init__(self, repository: FirebaseFormasPagamentoRepository):
        self.repository = repository

    def get_all_formas_pagamento(self, empresa_id: str, status_deleted: bool = False) -> tuple[list[FormaPagamento], int]:
        """
        Obtém todas as formas de pagamento para uma determinada empresa.

        Args:
            empresa_id (str): ID da empresa.
            status (RegistrationStatus): Status para filtrar as formas de pagamento (opcional).

        Returns:
            tuple[list[FormaPagamento], int]: Lista de formas de pagamento e a quantidade de deletados.
        """
        try:
            return self.repository.get_all_by_empresa(empresa_id, status_deleted)
        except Exception as e:
            logger.error(f"Erro ao obter formas de pagamento para empresa {empresa_id}: {e}")
            raise

    def get_forma_pagamento_by_id(self, empresa_id: str, forma_pagamento_id: str) -> FormaPagamento | None:
        """
        Obtém uma forma de pagamento específica pelo ID.

        Args:
            empresa_id (str): ID da empresa.
            forma_pagamento_id (str): ID da forma de pagamento.

        Returns:
            FormaPagamento | None: A forma de pagamento encontrada ou None.
        """
        try:
            forma_pagamento = self.repository.get_by_id(empresa_id, forma_pagamento_id)
            return forma_pagamento
        except Exception as e:
            logger.error(f"Erro ao obter forma de pagamento {forma_pagamento_id} para empresa {empresa_id}: {e}")
            raise

    def create_forma_pagamento(self, empresa_id: str, nome: str, tipo: str, desconto_percentual: float = 0.0, acrescimo_percentual: float = 0.0, ordem: int = 99) -> str:
        """
        Cria uma nova forma de pagamento.

        Args:
            empresa_id (str): ID da empresa.
            nome (str): Nome da forma de pagamento.
            tipo (str): Tipo da forma de pagamento (deve ser um valor do enum TipoPagamento).
            desconto_percentual (float): Percentual de desconto (opcional).
            acrescimo_percentual (float): Percentual de acréscimo (opcional).
            ordem (int): Ordem de exibição (opcional).

        Returns:
            str: ID da forma de pagamento criada.
        """
        try:
            tipo_pagamento = TipoPagamento[tipo]
        except KeyError:
            raise ValueError(f"Tipo de pagamento inválido: {tipo}")

        forma_pagamento_id = "fpg_" + get_uuid()
        forma_pagamento = FormaPagamento(
            id=forma_pagamento_id,
            empresa_id=empresa_id,
            nome=nome,
            tipo=tipo_pagamento,
            desconto_percentual=desconto_percentual,
            acrescimo_percentual=acrescimo_percentual,
        )
        return self.repository.save(forma_pagamento)
