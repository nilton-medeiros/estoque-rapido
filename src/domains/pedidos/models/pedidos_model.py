from dataclasses import dataclass, field
from datetime import datetime, date, UTC
from typing import Any

from src.domains.pedidos.models.pedidos_subclass import DeliveryStatus
from src.domains.shared import Address
from src.domains.shared.models.registration_status import RegistrationStatus
from src.shared.utils.money_numpy import Money


def _get_money_from_dict(value: Any) -> Money:
    """Converte um valor (dict, int, float) para um objeto Money."""
    if isinstance(value, Money):
        return value
    if isinstance(value, dict):
        return Money.from_dict(value)
    if isinstance(value, int):
        # Assume que o valor inteiro está em centavos
        return Money.mint(str(value / 100))
    if isinstance(value, float):
        return Money.mint(str(value))
    return Money.mint("0.00")  # Fallback para outros tipos


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
        return cls(
            id=data.get("id"),
            product_id=data["product_id"],
            description=data["description"],
            quantity=data["quantity"],
            unit_of_measure=data["unit_of_measure"],
            unit_price=_get_money_from_dict(data["unit_price"]),
            total=_get_money_from_dict(data["total"]),
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
        """Executa validações e normalizações após a inicialização do objeto."""
        self._validate_required_fields()
        self._validate_delivery_status_consistency()
        self._validate_total_amount()
        self._normalize_client_data()
        self._set_initial_activation_audit()

    def _validate_required_fields(self):
        """Valida se os campos essenciais do pedido estão preenchidos."""
        if not self.empresa_id:
            raise ValueError("O ID da empresa é obrigatório para um pedido.")
        if not self.forma_pagamento_id:
            raise ValueError("O ID da forma de pagamento é obrigatório para um pedido.")
        if not isinstance(self.total_amount, Money):
            raise TypeError("total_amount deve ser uma instância de Money.")

    def _validate_delivery_status_consistency(self):
        """Valida a consistência dos dados para pedidos em trânsito ou entregues."""
        if self.delivery_status in [DeliveryStatus.IN_TRANSIT, DeliveryStatus.DELIVERED]:
            if not self.order_number:
                raise ValueError("O número do pedido é obrigatório para pedidos em trânsito ou entregues.")
            if not self.items:
                raise ValueError("Um pedido deve conter pelo menos um item para pedidos em trânsito ou entregues.")

    def _validate_total_amount(self):
        """Valida se o total do pedido corresponde à soma dos itens."""
        calculated_total = self.calcular_total()
        if self.total_amount != calculated_total:
            raise ValueError(f"O total do pedido ({self.total_amount}) não corresponde à soma dos itens ({calculated_total}).")

    def _normalize_client_data(self):
        """Normaliza os dados do cliente, como nome, telefone e CPF."""
        if self.client_name:
            self.client_name = self.client_name.strip().title()
        if self.client_phone:
            self.client_phone = self.client_phone.strip()
        if self.client_cpf:
            self.client_cpf = ''.join(filter(str.isdigit, self.client_cpf))

    def _set_initial_activation_audit(self):
        """Define os campos de auditoria de ativação se o pedido for criado como ativo."""
        if self.status == RegistrationStatus.ACTIVE and self.created_at and not self.activated_at:
            self.activated_at = self.created_at
            self.activated_by_id = self.created_by_id
            self.activated_by_name = self.created_by_name

    def to_dict(self, recalculate: bool = True) -> dict[str, Any]:
        """Converte o objeto Pedido para um dicionário, usado no gerenciamento de formulários."""
        if recalculate:
            self._recalculate_and_update_totals()
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
        }

    def to_dict_db(self) -> dict[str, Any]:
        """
        Converte o objeto Pedido para um dicionário para persistência no banco de dados.
        Filtra chaves com valor None.
        """
        # Garante que os totais estão corretos antes de salvar no DB
        self._recalculate_and_update_totals()
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
        """
        Cria uma instância de Pedido a partir de um dicionário (geralmente do Firestore).
        Utiliza desempacotamento de dicionário (**) para maior manutenibilidade.
        """
        processed_data = data.copy()

        # 1. Adiciona o ID do documento
        processed_data['id'] = doc_id or data.get("id")

        # 2. Converte campos que precisam de tratamento especial
        # Enums
        if 'status' in processed_data and isinstance(processed_data['status'], str):
            processed_data['status'] = RegistrationStatus[processed_data['status']]
        elif 'status' not in processed_data:
            processed_data['status'] = RegistrationStatus.ACTIVE

        if 'delivery_status' in processed_data and isinstance(processed_data['delivery_status'], str):
            processed_data['delivery_status'] = DeliveryStatus[processed_data['delivery_status']]
        elif 'delivery_status' not in processed_data:
            processed_data['delivery_status'] = DeliveryStatus.PENDING

        # Timestamps do Firestore para datetime
        for key in ['created_at', 'updated_at', 'activated_at', 'inactivated_at', 'deleted_at']:
            if key in processed_data and hasattr(processed_data[key], 'to_datetime'):
                processed_data[key] = processed_data[key].to_datetime()

        # Objetos aninhados
        if 'items' in processed_data:
            processed_data['items'] = [PedidoItem.from_dict(item) for item in processed_data.get('items', [])]

        if 'client_address' in processed_data and processed_data['client_address']:
            processed_data['client_address'] = Address(**processed_data['client_address'])

        if 'total_amount' in processed_data:
            processed_data['total_amount'] = _get_money_from_dict(processed_data['total_amount'])

        # O Firestore armazena 'date' como um 'datetime', então convertemos de volta.
        if 'client_birthday' in processed_data and isinstance(processed_data['client_birthday'], datetime):
            processed_data['client_birthday'] = processed_data['client_birthday'].date()

        # 3. Instancia a classe usando o dicionário processado
        # O dataclass irá ignorar chaves extras que não são campos definidos.
        return cls(**processed_data)

    def calcular_total(self) -> Money:
        """Calcula o total do pedido com base na soma dos itens."""
        # Usa o método factory `mint` para criar um valor 'zero' com a moeda correta.
        # É a forma preferencial e mais segura de instanciar Money.
        zero = Money.mint("0.00", currency_symbol=self.total_amount.currency_symbol)
        total = sum((item.total for item in self.items), zero)
        return total

    def _recalculate_and_update_totals(self) -> None:
        """
        Recalcula os totais (valor, quantidade de itens, quantidade de produtos)
        com base na lista de itens e atualiza os atributos da instância.
        Este método tem o efeito colateral de modificar o estado do objeto.
        """
        self.total_amount = self.calcular_total()
        self.total_items = len(self.items)
        self.total_products = sum(item.quantity for item in self.items)
