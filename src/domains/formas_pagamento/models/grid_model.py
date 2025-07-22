from dataclasses import dataclass
from src.domains.formas_pagamento.models import FormaPagamento
from src.domains.shared.models.filter_type import FilterType

@dataclass
class FormasPagamentoGridState:
    """Estado do grid de pedidos"""
    formas_pagamentos: list[FormaPagamento] | None = None
    inactive_count: int = 0
    filter_type: FilterType = FilterType.ALL
    search_text: str = ""
    is_loading: bool = True

    def __post_init__(self):
        if self.formas_pagamentos is None:
            self.formas_pagamentos = []
