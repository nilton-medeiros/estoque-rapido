from dataclasses import dataclass
from src.domains.clientes.models import Cliente
from src.domains.shared.models.filter_type import FilterType

@dataclass
class ClieGridState:
    """Estado do grid de clientes"""
    clientes: list[Cliente] | None = None
    inactive_count: int = 0
    filter_type: FilterType = FilterType.ALL
    search_text: str = ""
    is_loading: bool = True

    def __post_init__(self):
        if self.clientes is None:
            self.clientes = []
