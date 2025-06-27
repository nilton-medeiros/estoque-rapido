from enum import Enum


class ProductStatus(Enum):
    ACTIVE = "Ativo"
    INACTIVE = "Descontinuado"
    DELETED = "Lixeira"
