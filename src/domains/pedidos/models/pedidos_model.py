from dataclasses import dataclass, field
from datetime import datetime, date, UTC
# from turtle import st
from typing import Any

from src.domains.formas_pagamento.models.formas_pagamento_model import TipoPagamento
from src.domains.pedidos.models.pedidos_subclass import DeliveryStatus
from src.domains.shared import Address
from src.domains.shared.models.registration_status import RegistrationStatus
from src.shared.utils.money_numpy import Money


@dataclass
class PedidoItem:
    """
    Representa um item individual dentro de um Pedido.
    """
    product_id: str
    description: str # Desnormalizado
    quantity: int
    unit_price: Money
    total: Money
    unit_of_measure: str = "UN"
    id: str | None = None # ID do item na sub-coleção

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "product_id": self.product_id,
            "description": self.description,
            "quantity": self.quantity,
            "unit_of_measure": self.unit_of_measure,
            "unit_price": self.unit_price.to_dict(),
            "total": self.total.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PedidoItem":
        def get_money(value: Any) -> Money:
            if isinstance(value, Money):
                return value
            elif isinstance(value, dict):
                return Money.from_dict(value)
            elif isinstance(value, int):
                # Assume que o valor inteiro está em centavos
                return Money.mint(str(value / 100))
            elif isinstance(value, float):
                return Money.mint(str(value))
            return Money.mint("0.00")  # Fallback para outros tipos

        price = data["unit_price"]
        total = data["total"]

        return cls(
            id=data.get("id"),
            product_id=data["product_id"],
            description=data["description"],
            quantity=data["quantity"],
            unit_of_measure=data["unit_of_measure"],
            unit_price=get_money(price),
            total=get_money(total),
        )

@dataclass
class Pedido:
    """
    Representa um Pedido no sistema.
    """
    empresa_id: str
    forma_pagamento_id: str
    total_amount: Money # Novo campo para o total do pedido
    items: list[PedidoItem] = field(default_factory=list)
    total_items: int = 0
    total_products: int = 0
    stock_reduction: bool = False

    # Dados do Cliente (desnormalizados e opcionais)
    client_id: str | None = None
    client_name: str | None = None
    client_phone: str | None = None
    client_is_whatsapp: bool = False
    client_cpf: str | None = None
    client_birthday: date | None = None
    client_address: Address | None = None

    # Status do pedido e entrega
    status: RegistrationStatus = RegistrationStatus.ACTIVE # Ex: ACTIVE, INACTIVE, DELETED
    delivery_status: DeliveryStatus = DeliveryStatus.PENDING # Ex: CANCELED, PENDING, IN_TRANSIT, DELIVERED

    id: str | None = None
    order_number: str | None = None # Número sequencial do pedido (ex: "001023") criado pelo database ao salvar

    # --- Campos de Auditoria
    created_at: datetime | None = datetime.now(UTC)
    created_by_id: str | None = None
    created_by_name: str | None = None

    updated_at: datetime | None = None
    updated_by_id: str | None = None
    updated_by_name: str | None = None

    activated_at: datetime | None = None
    activated_by_id: str | None = None
    activated_by_name: str | None = None

    inactivated_at: datetime | None = None
    inactivated_by_id: str | None = None
    inactivated_by_name: str | None = None

    deleted_at: datetime | None = None
    deleted_by_id: str | None = None
    deleted_by_name: str | None = None


    def __post_init__(self):
        # Validações e normalizações
        if not self.empresa_id:
            raise ValueError("O ID da empresa é obrigatório para um pedido.")
        if not self.forma_pagamento_id:
            raise ValueError("O ID da forma de pagamento é obrigatório para um pedido.")
        if self.delivery_status == DeliveryStatus.IN_TRANSIT or self.delivery_status == DeliveryStatus.DELIVERED:
            if not self.order_number:
                raise ValueError("O número do pedido é obrigatório para pedidos em trânsito ou entregues.")
            if not self.items:
                raise ValueError("Um pedido deve conter pelo menos um item para pedidos em trânsito ou entregues.")
        if not isinstance(self.total_amount, Money):
            raise TypeError("total_amount deve ser uma instância de Money.")

        # Validação de consistência: o total do pedido deve ser igual à soma dos itens.
        # Isso garante a integridade dos dados no momento da criação do objeto.
        calculated_total = self.calcular_total()
        if self.total_amount != calculated_total:
            raise ValueError(f"O total do pedido ({self.total_amount}) não corresponde à soma dos itens ({calculated_total}).")

        # Normaliza dados do cliente se existirem
        if self.client_name:
            self.client_name = self.client_name.strip().title()
        if self.client_phone:
            self.client_phone = self.client_phone.strip()
        if self.client_cpf:
            # Remove formatação e mantém apenas dígitos
            self.client_cpf = ''.join(filter(str.isdigit, self.client_cpf))

        # Se o pedido está sendo criado como ACTIVE e não tem activated_at, define-o
        if self.status == RegistrationStatus.ACTIVE and self.created_at and not self.activated_at:
            self.activated_at = self.created_at
            self.activated_by_id = self.created_by_id
            self.activated_by_name = self.created_by_name

    def to_dict(self) -> dict[str, Any]:
        """Converte o objeto Pedido para um dicionário, usado no gerenciamento de formulários."""
        return {
            "id": self.id,
            "empresa_id": self.empresa_id,
            "forma_pagamento_id": self.forma_pagamento_id,
            "order_number": self.order_number,
            "total_amount": self.total_amount,
            "items": [item.to_dict() for item in self.items],
            "total_items": self.total_items,
            "total_products": self.total_products,
            "stock_reduction": self.stock_reduction,
            "client_id": self.client_id,
            "client_name": self.client_name,
            "client_phone": self.client_phone,
            "client_is_whatsapp": self.client_is_whatsapp,
            "client_cpf": self.client_cpf,
            "client_birthday": self.client_birthday,
            "client_address": self.client_address.__dict__ if self.client_address else None,
            "status": self.status,
            "delivery_status": self.delivery_status,
            "created_at": self.created_at,
            "created_by_id": self.created_by_id,
            "created_by_name": self.created_by_name,
            "updated_at": self.updated_at,
            "updated_by_id": self.updated_by_id,
            "updated_by_name": self.updated_by_name,
            "activated_at": self.activated_at,
            "activated_by_id": self.activated_by_id,
            "activated_by_name": self.activated_by_name,
            "inactivated_at": self.inactivated_at,
            "inactivated_by_id": self.inactivated_by_id,
            "inactivated_by_name": self.inactivated_by_name,
            "deleted_at": self.deleted_at,
            "deleted_by_id": self.deleted_by_id,
            "deleted_by_name": self.deleted_by_name,
            **self.get_totais(),
        }

    def to_dict_db(self) -> dict[str, Any]:
        """
        Converte o objeto Pedido para um dicionário para persistência no banco de dados.
        Filtra chaves com valor None.
        """
        dict_db: dict[str, Any] = {
            "empresa_id": self.empresa_id,
            "forma_pagamento_id": self.forma_pagamento_id,
            "order_number": self.order_number,
            "total_amount": self.total_amount.to_dict(),
            "items": [item.to_dict() for item in self.items],
            "total_items": self.total_items,
            "total_products": self.total_products,
            "stock_reduction": self.stock_reduction,
            "client_id": self.client_id,
            "client_name": self.client_name,
            "client_phone": self.client_phone,
            "client_is_whatsapp": self.client_is_whatsapp,
            "client_cpf": self.client_cpf,
            "client_birthday": self.client_birthday,
            "client_address": self.client_address.__dict__ if self.client_address else None,
            "status": self.status.name,
            "delivery_status": self.delivery_status.name,
            "created_at": self.created_at,
            "created_by_id": self.created_by_id,
            "created_by_name": self.created_by_name,
            "updated_at": self.updated_at,
            "updated_by_id": self.updated_by_id,
            "updated_by_name": self.updated_by_name,
            "activated_at": self.activated_at,
            "activated_by_id": self.activated_by_id,
            "activated_by_name": self.activated_by_name,
            "inactivated_at": self.inactivated_at,
            "inactivated_by_id": self.inactivated_by_id,
            "inactivated_by_name": self.inactivated_by_name,
            "deleted_at": self.deleted_at,
            "deleted_by_id": self.deleted_by_id,
            "deleted_by_name": self.deleted_by_name,
        }
        return {k: v for k, v in dict_db.items() if v is not None}

    @classmethod
    def from_dict(cls, data: dict[str, Any], doc_id: str | None = None) -> "Pedido":
        """Cria uma instância de Pedido a partir de um dicionário."""
        # Converte enums Order Status
        status_data = data.get("status", RegistrationStatus.ACTIVE)
        status = status_data # Por padrão status_data é do tipo RegistrationStatus

        if not isinstance(status_data, RegistrationStatus):
            if isinstance(status_data, str) and status_data in RegistrationStatus.__members__:
                status = RegistrationStatus[status_data]
            else:
                status = RegistrationStatus.ACTIVE

        # Converte enums Delivery Status
        status_data = data.get("delivery_status", DeliveryStatus.PENDING)
        delivery_status = status_data # Por padrão delivery_status é do tipo DeliveryStatus

        if not isinstance(status_data, DeliveryStatus):
            if isinstance(status_data, str) and status_data in DeliveryStatus.__members__:
                delivery_status = DeliveryStatus[status_data]
            else:
                delivery_status = DeliveryStatus.PENDING

        # Converte Timestamps do Firestore para datetime
        for key in ['created_at', 'updated_at', 'activated_at', 'inactivated_at', 'deleted_at']:
            if key in data and data.get(key) and hasattr(data[key], 'to_datetime'):
                data[key] = data[key].to_datetime()

        items_data = data.get("items", [])
        items = [PedidoItem.from_dict(item_data) for item_data in items_data]

        client_address_obj = None
        if address_data := data.get("client_address"):
            client_address_obj = Address(**address_data) # Assumindo que Address pode ser instanciado diretamente de um dict

        def get_money(value: Any) -> Money:
            if isinstance(value, Money):
                return value
            elif isinstance(value, dict):
                return Money.from_dict(value)
            elif isinstance(value, int):
                # Assume que o valor inteiro está em centavos
                return Money.mint(str(value / 100))
            elif isinstance(value, float):
                return Money.mint(str(value))
            return Money.mint("0.00")  # Fallback para outros tipos

        total = data["total_amount"]

        return cls(
            id=doc_id or data.get("id"),
            empresa_id=data["empresa_id"],
            forma_pagamento_id=data["forma_pagamento_id"],
            order_number=data.get("order_number"),
            total_amount=get_money(total),
            items=items,
            total_items=data.get("total_items", 0),
            total_products=data.get("total_products", 0),
            stock_reduction=data.get("stock_reduction", False),
            client_id=data.get("client_id"),
            client_name=data.get("client_name"),
            client_phone=data.get("client_phone"),
            client_is_whatsapp=data.get("client_is_whatsapp", False),
            client_cpf=data.get("client_cpf"),
            client_birthday=data.get("client_birthday"),
            client_address=client_address_obj,
            status=status,
            delivery_status=delivery_status,
            created_at=data.get("created_at"),
            created_by_id=data.get("created_by_id"),
            created_by_name=data.get("created_by_name"),
            updated_at=data.get("updated_at"),
            updated_by_id=data.get("updated_by_id"),
            updated_by_name=data.get("updated_by_name"),
            activated_at=data.get("activated_at"),
            activated_by_id=data.get("activated_by_id"),
            activated_by_name=data.get("activated_by_name"),
            inactivated_at=data.get("inactivated_at"),
            inactivated_by_id=data.get("inactivated_by_id"),
            inactivated_by_name=data.get("inactivated_by_name"),
            deleted_at=data.get("deleted_at"),
            deleted_by_id=data.get("deleted_by_id"),
            deleted_by_name=data.get("deleted_by_name"),
        )

    def calcular_total(self) -> Money:
        """Calcula o total do pedido com base na soma dos itens."""
        # Usa o método factory `mint` para criar um valor 'zero' com a moeda correta.
        # É a forma preferencial e mais segura de instanciar Money.
        zero = Money.mint("0.00", currency_symbol=self.total_amount.currency_symbol)
        total = sum((item.total for item in self.items), zero)
        return total

    def get_totais(self) -> dict[str, Any]:
        # Garante uma atualização nos totais em caso de alteração de algum item
        self.total_amount = self.calcular_total()
        self.total_items = len(self.items)
        self.total_products = sum(item.quantity for item in self.items)
        return {
            "total_amount": self.total_amount,
            "total_items": self.total_items,
            "total_products": self.total_products,
        }
