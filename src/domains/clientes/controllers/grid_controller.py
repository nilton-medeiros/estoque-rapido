# ==========================================
# src/domains/clientes/controllers/grid_controller.py
# ==========================================
from typing import Callable, TYPE_CHECKING, Optional
import asyncio
import flet as ft
from src.domains.shared.models.filter_type import FilterType
from src.domains.clientes.models.grid_model import ClieGridState
from src.domains.clientes.models.cliente_model import Cliente
from src.domains.clientes.controllers import clientes_controllers as client_controllers

if TYPE_CHECKING:
    from src.domains.clientes.views.clientes_grid_ui import ClienteGridUI

class ClienteGridController:
    """Controlador do grid de clientes"""

    def __init__(self, page: ft.Page, on_action: Callable):
        self.page = page
        self.state = ClieGridState()
        self.on_action = on_action
        self.ui_components: Optional['ClienteGridUI'] = None

    def execute_action_async(self, action: str, cliente: Optional[Cliente]):
        """Executa a ação de forma assíncrona usando page.run_task."""
        if self.on_action: # self.on_action é o handle_action async
            self.page.run_task(self.on_action, action, cliente)

    def filter_clientes(self) -> list[Cliente]:
        """Aplica todos os filtros aos clientes"""
        filtered = self.state.clientes if self.state.clientes else []

        # Filtro por status
        if self.state.filter_type == FilterType.ACTIVE:
            filtered = [c for c in filtered if c.status.name == 'ACTIVE']
        elif self.state.filter_type == FilterType.INACTIVE:
            filtered = [c for c in filtered if c.status.name == 'INACTIVE']

        # Filtro por texto de busca
        if self.state.search_text.strip():
            search_lower = self.state.search_text.strip().lower()
            filtered = [c for c in filtered if search_lower in c.name.nome_completo_minusculo]

        return filtered

    async def load_clientes(self):
        """Carrega clientes do backend"""
        self.state.is_loading = True
        if self.ui_components:
            self.ui_components.update_loading_state(True)

        try:
            empresa_id = self.page.app_state.empresa["id"]  # type: ignore [attr-defined]
            if not empresa_id:
                self.state.clientes = []
                self.state.inactive_count = 0
                return

            result = await self._fetch_clientes_async(empresa_id)

            if result["status"] == "error":
                raise Exception(result.get('message', 'Erro desconhecido'))

            self.state.clientes = result['data']["clientes"]
            self.state.inactive_count = result['data']["quantidade_deletados"]

        except Exception as e:
            self.state.clientes = []
            self.state.inactive_count = 0
            raise e
        finally:
            self.state.is_loading = False
            if self.ui_components:
                self.ui_components.update_loading_state(False)
                self.ui_components.render_grid(self.filter_clientes())

    async def _fetch_clientes_async(self, empresa_id: str) -> dict:
        """Wrapper async para a chamada síncrona do controller"""
        return await asyncio.to_thread(client_controllers.handle_get_all, empresa_id)
