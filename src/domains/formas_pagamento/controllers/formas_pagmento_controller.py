import logging
from typing import Any

from src.domains.formas_pagamento.services.formas_pagamento_service import FormasPagamentoService
from src.domains.shared import RegistrationStatus

logger = logging.getLogger(__name__)


class FormasPagamentoController:
    def __init__(self, service: FormasPagamentoService):
        self.service = service

    def get_formas_pagamento(self, empresa_id: str, status: str = "ACTIVE") -> list[dict[str, Any]]:
        """
        Obtém todas as formas de pagamento para uma empresa, com tratamento de status.

        Args:
            empresa_id (str): ID da empresa.
            status (str): Status para filtrar (opcional, padrão: "ACTIVE").

        Returns:
            list[dict[str, Any]]: Lista de formas de pagamento como dicionários.
        """
        try:
            status_enum = RegistrationStatus[status]
        except KeyError:
            logger.warning(f"Status inválido fornecido: {status}. Usando 'ACTIVE' como padrão.")
            status_enum = RegistrationStatus.ACTIVE

        try:
            formas_pagamento = self.service.get_all_formas_pagamento(empresa_id, status_enum)
            return [fp.to_dict_db() for fp in formas_pagamento]  # Converte para dicionários
        except Exception as e:
            logger.error(f"Erro no controller ao obter formas de pagamento: {e}")
            raise  # Re-lança para ser tratado em uma camada superior (ex: API)

    def get_forma_pagamento(self, empresa_id: str, forma_pagamento_id: str) -> dict[str, Any] | None:
        """
        Obtém uma forma de pagamento específica pelo ID.

        Args:
            empresa_id (str): ID da empresa.
            forma_pagamento_id (str): ID da forma de pagamento.

        Returns:
            dict[str, Any] | None: A forma de pagamento como dicionário ou None.
        """
        try:
            forma_pagamento = self.service.get_forma_pagamento_by_id(empresa_id, forma_pagamento_id)
            return forma_pagamento.to_dict_db() if forma_pagamento else None
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
