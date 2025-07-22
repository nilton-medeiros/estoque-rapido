import logging
from typing import Any

from src.domains.formas_pagamento.models.formas_pagamento_model import FormaPagamento
from src.domains.formas_pagamento.services.formas_pagamento_service import FormasPagamentoService

logger = logging.getLogger(__name__)


class FormasPagamentoController:
    def __init__(self, service: FormasPagamentoService):
        self.service = service

    def get_formas_pagamento(self, empresa_id: str, status_deleted: bool = False) -> tuple[list[FormaPagamento], int]:
        """
        Obtém todas as formas de pagamento para uma empresa, com tratamento de status.

        Args:
            empresa_id (str): ID da empresa.
            status_deleted (bool): Status para filtrar Ativos&Inativos ou apenas deletados.

        Returns:
            tuple[list[FormaPagamento], int]: Lista de formas de pagamento e a quantidade de deletados.
        """
        try:
            return self.service.get_all_formas_pagamento(empresa_id, status_deleted)
        except Exception as e:
            logger.error(f"Erro no controller ao obter formas de pagamento: {e}")
            raise  # Re-lança para ser tratado em uma camada superior (ex: API)

    def get_forma_pagamento(self, empresa_id: str, forma_pagamento_id: str) -> FormaPagamento | None:
        """
        Obtém uma forma de pagamento específica pelo ID.

        Args:
            empresa_id (str): ID da empresa.
            forma_pagamento_id (str): ID da forma de pagamento.

        Returns:
            FormaPagamento: A forma de pagamento encontrada ou uma excessão
        """
        try:
            return self.service.get_forma_pagamento_by_id(empresa_id, forma_pagamento_id)
        except Exception as e:
            logger.error(f"Erro no controller ao obter forma de pagamento por ID: {e}")
            raise

    def create_forma_pagamento(self, empresa_id: str, nome: str, tipo: str, desconto_percentual: float = 0.0, acrescimo_percentual: float = 0.0, ordem: int = 99) -> str:
        try:
            forma_pagamento_id = self.service.create_forma_pagamento(
                empresa_id=empresa_id,
                nome=nome,
                tipo=tipo,
                desconto_percentual=desconto_percentual,
                acrescimo_percentual=acrescimo_percentual,
                ordem=ordem
            )
            return forma_pagamento_id
        except ValueError as e:
            logger.error(f"Erro de validação ao criar forma de pagamento: {e}")
            raise
        except Exception as e:
            logger.error(f"Erro no controller ao criar forma de pagamento: {e}")
            raise
