from enum import Enum


class OrderStatus(Enum):
    ACTIVE = "Ativo"
    CANCELED = "Cancelado"
    INACTIVE = "Inativo"
    DELIVERED = "Entregue"
    DELETED = "Lixeira"
