from enum import Enum


class DeliveryStatus(Enum):
    """Status de Entrega: Pendente[PENDING], Em trânsito[IN_TRANSIT], Entregue[DELIVERED] ou Cancelado[CANCELED]."""
    PENDING = "PENDENTE"
    IN_TRANSIT = "EM TRÂNSITO"
    DELIVERED = "ENTREGUE"
    CANCELED = "CANCELADO"

class OrderFilterType(Enum):
    """Tipo de Filtro de Pedidos: Todos[ALL], Ativos[ACTIVE], Inativos[INACTIVE], Entregues[DELIVERED], Cancelados[CANCELED]."""
    ALL = "all"
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    CANCELED = "canceled"
