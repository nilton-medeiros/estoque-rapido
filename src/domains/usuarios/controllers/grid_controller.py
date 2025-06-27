# ==========================================
# src/domains/usuarios/controllers/grid_controller.py
# ==========================================
from typing import Callable, TYPE_CHECKING, Optional
import asyncio
import flet as ft
from src.domains.shared.models.filter_type import FilterType
from src.domains.usuarios.models.grid_model import UserGridState
from src.domains.usuarios.models.usuarios_model import Usuario
from src.domains.usuarios.controllers import usuarios_controllers as user_controllers

if TYPE_CHECKING:
    from src.domains.usuarios.views.usuarios_grid_ui import UsuarioGridUI

class UsuarioGridController:
    """Controlador do grid de usuarios"""

    def __init__(self, page: ft.Page, on_action: Callable):
        self.page = page
        self.state = UserGridState()
        self.on_action = on_action
        self.ui_components: Optional['UsuarioGridUI'] = None

    def execute_action_async(self, action: str, usuario: Optional[Usuario]):
        """Executa a ação de forma assíncrona usando page.run_task."""
        if self.on_action: # self.on_action é o handle_action async
            self.page.run_task(self.on_action, action, usuario)

    def filter_usuarios(self) -> list[Usuario]:
        """Aplica todos os filtros aos usuarios"""
        filtered = self.state.usuarios if self.state.usuarios else []

        # Filtro por status
        if self.state.filter_type == FilterType.ACTIVE:
            filtered = [u for u in filtered if u.status.name == 'ACTIVE']
        elif self.state.filter_type == FilterType.INACTIVE:
            filtered = [u for u in filtered if u.status.name == 'INACTIVE']

        # Filtro por texto de busca
        if self.state.search_text.strip():
            search_lower = self.state.search_text.strip().lower()
            filtered = [u for u in filtered if search_lower in u.name.nome_completo_minusculo]

        return filtered

    async def load_usuarios(self):
        """Carrega usuarios do backend"""
        self.state.is_loading = True
        if self.ui_components:
            self.ui_components.update_loading_state(True)

        try:
            empresa_id = self.page.app_state.empresa["id"]  # type: ignore [attr-defined]
            if not empresa_id:
                self.state.usuarios = []
                self.state.inactive_count = 0
                return

            result = await self._fetch_usuarios_async(empresa_id)

            if result["status"] == "error":
                raise Exception(result.get('message', 'Erro desconhecido'))

            self.state.usuarios = result['data']["usuarios"]
            self.state.inactive_count = result['data']["deleted"]

        except Exception as e:
            self.state.usuarios = []
            self.state.inactive_count = 0
            raise e
        finally:
            self.state.is_loading = False
            if self.ui_components:
                self.ui_components.update_loading_state(False)
                self.ui_components.render_grid(self.filter_usuarios())

    async def _fetch_usuarios_async(self, empresa_id: str) -> dict:
        """Wrapper async para a chamada síncrona do controller"""
        return await asyncio.to_thread(user_controllers.handle_get_all, empresa_id)
