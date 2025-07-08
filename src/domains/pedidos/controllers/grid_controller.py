from typing import Callable, TYPE_CHECKING, Optional
import asyncio
import flet as ft
from src.domains.pedidos.models import OrdGridState, Pedido
from src.domains.pedidos.models.pedidos_subclass import DeliveryStatus, OrderFilterType
from src.domains.pedidos.controllers import pedidos_controllers as order_controllers
from src.domains.shared import RegistrationStatus


if TYPE_CHECKING:
    from src.domains.pedidos.views.pedidos_grid_ui import PedidoGridUI

class PedidoGridController:
    """Controlador do grid de pedidos"""

    def __init__(self, page: ft.Page, on_action: Callable):
        self.page = page
        self.state = OrdGridState()
        self.on_action = on_action
        self.ui_components: Optional['PedidoGridUI'] = None

    def execute_action_async(self, action: str, pedido: Pedido | None):
        """Executa a ação de forma assíncrona usando page.run_task."""
        if self.on_action: # self.on_action é o handle_action async
            self.page.run_task(self.on_action, action, pedido)

    def _search_in_pedido(self, pedido: Pedido, search_lower: str) -> bool:
        if pedido.order_number and search_lower in pedido.order_number:
            return True
        if pedido.client_name and search_lower in pedido.client_name:
            return True
        if pedido.client_phone and search_lower in pedido.client_phone:
            return True
        return False

    def filter_pedidos(self) -> list[Pedido]:
        """Aplica todos os filtros aos pedidos"""
        filtered = self.state.pedidos if self.state.pedidos else []

        # Filtro por status
        match self.state.filter_type:
            case OrderFilterType.ACTIVE:
                filtered = [p for p in filtered if p.status == RegistrationStatus.ACTIVE]
            case OrderFilterType.INACTIVE:
                filtered = [p for p in filtered if p.status == RegistrationStatus.INACTIVE]
            case OrderFilterType.PENDING:
                filtered = [p for p in filtered if p.delivery_status == DeliveryStatus.PENDING]
            case OrderFilterType.IN_TRANSIT:
                filtered = [p for p in filtered if p.delivery_status == DeliveryStatus.IN_TRANSIT]
            case OrderFilterType.DELIVERED:
                filtered = [p for p in filtered if p.delivery_status == DeliveryStatus.DELIVERED]
            case OrderFilterType.CANCELED:
                filtered = [p for p in filtered if p.delivery_status == DeliveryStatus.CANCELED]


        # Filtro por texto de busca
        if self.state.search_text.strip():
            search_lower = self.state.search_text.strip().lower()
            filtered = [p for p in filtered if self._search_in_pedido(p, search_lower)]

        return filtered

    async def load_pedidos(self):
        """Carrega pedidos do backend"""
        self.state.is_loading = True
        if self.ui_components:
            self.ui_components.update_loading_state(True)

        try:
            empresa_id = self.page.app_state.empresa['id'] # type: ignore [attr-defined]
            if not empresa_id:
                self.state.pedidos = []
                self.state.inactive_count = 0
                return

            result = await self._fetch_pedidos_async(empresa_id)

            if result["status"] == "error":
                raise Exception(result.get('message', 'Erro desconhecido'))

            self.state.pedidos = result['data']["pedidos"]
            self.state.inactive_count = result['data']["quantidade_deletados"]

        except Exception as e:
            self.state.pedidos = []
            self.state.inactive_count = 0
            raise e
        finally:
            self.state.is_loading = False
            if self.ui_components:
                self.ui_components.update_loading_state(False)
                self.ui_components.render_grid(self.filter_pedidos())

    async def _fetch_pedidos_async(self, empresa_id: str) -> dict:
        """Wrapper async para a chamada síncrona do controller"""
        return await asyncio.to_thread(
            order_controllers.handle_get_pedidos_by_empresa_id,
            empresa_id=empresa_id
        )
