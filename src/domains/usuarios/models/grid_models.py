from dataclasses import dataclass
from enum import Enum
from src.domains.usuarios.models.usuario_model import Usuario

class FilterType(Enum):
    ALL = "all"
    ACTIVE = "active"
    INACTIVE = "inactive"

@dataclass
class GridState:
    """Estado do grid de usuarios"""
    usuarios: list[Usuario] | None = None
    inactive_count: int = 0
    filter_type: FilterType = FilterType.ALL
    search_text: str = ""
    is_loading: bool = True

    def __post_init__(self):
        if self.usuarios is None:
            self.usuarios = []
