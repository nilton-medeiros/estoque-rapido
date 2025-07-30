from typing import Callable, TYPE_CHECKING, Optional
import asyncio
import flet as ft
import logging
from src.domains.formas_pagamento.models.formas_pagamento_model import FormaPagamento
from src.domains.formas_pagamento.models.grid_model import FormasPagamentoGridState
from src.domains.formas_pagamento.repositories.implementations.firebase_formas_pagamento_repository import FirebaseFormasPagamentoRepository
from src.domains.formas_pagamento.services.formas_pagamento_service import FormasPagamentoService
from src.domains.shared.models.filter_type import FilterType
from src.domains.formas_pagamento.controllers.formas_pagamento_controller import FormasPagamentoController

if TYPE_CHECKING:
    from src.domains.formas_pagamento.views.formas_pagamento_grid_ui import FormasPagamentoGridUI

logger = logging.getLogger(__name__)

class FormaPagamentoGridController:
    """Controlador do grid de formas de pagamento"""

    def __init__(self, page: ft.Page, on_action: Callable):
        self.page = page
        self.state = FormasPagamentoGridState()
        self.on_action = on_action
        self.ui_components: Optional['FormasPagamentoGridUI'] = None
        self.service = FormasPagamentoService(FirebaseFormasPagamentoRepository())
        self.controller = FormasPagamentoController(self.service)



    def execute_action_async(self, action: str, forma_pagamento: FormaPagamento | None):
        """Executa a ação de forma assíncrona usando page.run_task."""
        if self.on_action: # self.on_action é o handle_action async
            self.page.run_task(self.on_action, action, forma_pagamento)

    def filter_formas_pagamento(self) -> list[FormaPagamento]:
        """Aplica todos os filtros nas formas de pagamento"""
        filtered = self.state.formas_pagamentos if self.state.formas_pagamentos else []

        # Filtro por status
        if self.state.filter_type == FilterType.ACTIVE:
            filtered = [p for p in filtered if p.status.name == 'ACTIVE']
        elif self.state.filter_type == FilterType.INACTIVE:
            filtered = [p for p in filtered if p.status.name == 'INACTIVE']

        return filtered

    async def load_formas_pagamento(self):
        """Carrega formas de pagamento do backend"""
        self.state.is_loading = True
        if self.ui_components:
            self.ui_components.update_loading_state(True)

        try:
            empresa_id = self.page.app_state.empresa['id'] # type: ignore [attr-defined]
            if not empresa_id:
                self.state.formas_pagamentos = []
                self.state.inactive_count = 0
                return

            formas_pagamentos, quantidade_deletados = await self._fetch_formas_pagamentos_async(empresa_id)

            self.state.formas_pagamentos = formas_pagamentos
            self.state.inactive_count = quantidade_deletados

        except Exception as e:
            self.state.formas_pagamentos = []
            self.state.inactive_count = 0
            logger.error(f"Erro ao carregar formas de pagamento: {e}", exc_info=True)
        finally:
            self.state.is_loading = False
            if self.ui_components:
                self.ui_components.update_loading_state(False)
                self.ui_components.render_grid(self.filter_formas_pagamento())

    async def _fetch_formas_pagamentos_async(self, empresa_id: str) -> tuple[list[FormaPagamento], int]:
        """Wrapper async para a chamada síncrona do controller"""
        return await asyncio.to_thread(
            self.controller.get_formas_pagamento,
            empresa_id=empresa_id
        )
