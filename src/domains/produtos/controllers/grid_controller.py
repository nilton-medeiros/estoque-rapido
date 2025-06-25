# ==========================================
# src/domains/produtos/controllers/grid_controller.py
# ==========================================
from typing import Callable, TYPE_CHECKING, Optional
import asyncio
import flet as ft
from src.domains.produtos.models.grid_model import ProdGridState, StockLevel
from src.domains.produtos.models.produtos_model import Produto
from src.domains.produtos.controllers import produtos_controllers as product_controllers
from src.domains.shared.models.filter_type import FilterType

if TYPE_CHECKING:
    from src.domains.produtos.views.produtos_grid_ui import ProdutoGridUI

class ProdutoGridController:
    """Controlador do grid de produtos"""

    def __init__(self, page: ft.Page, on_action: Callable):
        self.page = page
        self.state = ProdGridState()
        self.on_action = on_action
        self.ui_components: Optional['ProdutoGridUI'] = None

    def execute_action_async(self, action: str, produto: Optional[Produto]):
        """Executa a ação de forma assíncrona usando page.run_task."""
        if self.on_action: # self.on_action é o handle_action async
            self.page.run_task(self.on_action, action, produto)

    def filter_produtos(self) -> list[Produto]:
        """Aplica todos os filtros aos produtos"""
        filtered = self.state.produtos if self.state.produtos else []

        # Filtro por status
        if self.state.filter_type == FilterType.ACTIVE:
            filtered = [p for p in filtered if p.status.name == 'ACTIVE']
        elif self.state.filter_type == FilterType.INACTIVE:
            filtered = [p for p in filtered if p.status.name == 'INACTIVE']

        # Filtro por texto de busca
        if self.state.search_text.strip():
            search_lower = self.state.search_text.lower()
            filtered = [p for p in filtered if search_lower in p.name.lower()]

        # Filtro por estoque
        filtered = [p for p in filtered if self._stock_matches(p)]

        return filtered

    def _stock_matches(self, produto: Produto) -> bool:
        """Verifica se o produto atende ao filtro de estoque"""
        if self.state.stock_filter == StockLevel.ALL:
            return True
        elif self.state.stock_filter == StockLevel.NORMAL:
            return produto.minimum_stock_level <= produto.quantity_on_hand < produto.maximum_stock_level
        elif self.state.stock_filter == StockLevel.EXCELLENT:
            return produto.maximum_stock_level <= produto.quantity_on_hand
        else:  # REPLACE
            return produto.quantity_on_hand < produto.minimum_stock_level

    async def load_produtos(self):
        """Carrega produtos do backend"""
        self.state.is_loading = True
        if self.ui_components:
            self.ui_components.update_loading_state(True)

        try:
            empresa_id = self.page.app_state.empresa['id'] # type: ignore [attr-defined]
            if not empresa_id:
                self.state.produtos = []
                self.state.inactive_count = 0
                return

            result = await self._fetch_produtos_async(empresa_id)

            if result["status"] == "error":
                raise Exception(result.get('message', 'Erro desconhecido'))

            self.state.produtos = result['data']["produtos"]
            self.state.inactive_count = result['data']["deleted"]

        except Exception as e:
            self.state.produtos = []
            self.state.inactive_count = 0
            raise e
        finally:
            self.state.is_loading = False
            if self.ui_components:
                self.ui_components.update_loading_state(False)
                self.ui_components.render_grid(self.filter_produtos())

    async def _fetch_produtos_async(self, empresa_id: str) -> dict:
        """Wrapper async para a chamada síncrona do controller"""
        return await asyncio.to_thread(
            product_controllers.handle_get_all,
            empresa_id=empresa_id
        )
