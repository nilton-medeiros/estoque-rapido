from enum import Enum


class ProdutoStatus(Enum):
    ACTIVE = "Ativo"
    INACTIVE = "Descontinuado"
    DELETED = "Lixeira"
