from enum import Enum


class ProdutoStatus(Enum):
    ACTIVE = "Ativo"
    INACTIVE = "Obsoleto"
    DELETED = "Lixeira"
