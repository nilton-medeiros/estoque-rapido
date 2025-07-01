from dataclasses import dataclass
from enum import Enum
from src.domains.pedidos.models import Pedido
from src.domains.pedidos.models.pedidos_subclass import OrderFilterType

@dataclass
class OrdGridState:
    """Estado do grid de pedidos"""
    pedidos: list[Pedido] | None = None
    inactive_count: int = 0
    filter_type: OrderFilterType = OrderFilterType.ALL
    search_text: str = ""
    is_loading: bool = True

    def __post_init__(self):
        if self.pedidos is None:
            self.pedidos = []
