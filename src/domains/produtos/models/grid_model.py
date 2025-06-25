from dataclasses import dataclass
from enum import Enum
from src.domains.produtos.models.produtos_model import Produto
from src.domains.shared.models.filter_type import FilterType

class StockLevel(Enum):
    ALL = "all"
    NORMAL = "normal"
    EXCELLENT = "excellent"
    REPLACE = "replace"

@dataclass
class ProdGridState:
    """Estado do grid de produtos"""
    produtos: list[Produto] | None = None
    inactive_count: int = 0
    filter_type: FilterType = FilterType.ALL
    search_text: str = ""
    stock_filter: StockLevel = StockLevel.ALL
    is_loading: bool = True

    def __post_init__(self):
        if self.produtos is None:
            self.produtos = []
