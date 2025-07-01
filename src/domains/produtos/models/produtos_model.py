from dataclasses import dataclass
from datetime import datetime, UTC
from typing import Any

# Supondo que RegistrationStatus esteja no mesmo local ou acessível
from src.domains.shared import RegistrationStatus
from src.shared.utils import Money


@dataclass
class Produto:
    """
    Representa um produto na subcoleção 'produtos' dentro de uma 'empresa'.
    """
    empresa_id: str  # ID da empresa pai
    name: str
    name_lowercase: str
    categoria_id: str  # ID da categoria (da coleção 'produto_categorias')
    categoria_name: str # Nome da categoria (desnormalizado para ordenação)
    ncm: dict

    # --- Campos Essenciais do Produto ---
    sale_price: Money  # Preço de venda
    cost_price: Money = Money.mint("0.00")    # Preço de custo, default 0
    # Nomenclatura Comum do Mercosul: Necessário para emissão de nota fiscal

    # --- Campos de Identificação e Códigos ---
    internal_code: str | None = None  # Código interno/SKU
    ean_code: str | None = None      # Código EAN (código de barras)

    # --- Campos Descritivos ---
    description: str | None = None
    image_url: str | None = None
    brand: str | None = None          # Marca do produto

    # --- Campos de Estoque ---
    quantity_on_hand: int = 0  # Quantidade disponível
    unit_of_measure: str | None = None  # Unidade de medida (ex: "un", "L", "kg", "pacote")
    minimum_stock_level: int = 0
    maximum_stock_level: int = 0

    # --- Campos de Status e Auditoria ---
    status: RegistrationStatus = RegistrationStatus.ACTIVE
    # ID do documento no Firestore (gerado automaticamente)
    id: str | None = None

    created_at: datetime | None = datetime.now(UTC)
    created_by_id: str | None = None
    created_by_name: str | None = None

    updated_at: datetime | None = None
    updated_by_id: str | None = None
    updated_by_name: str | None = None

    activated_at: datetime | None = None  # Se o status mudar para ACTIVE
    activated_by_id: str | None = None
    activated_by_name: str | None = None

    inactivated_at: datetime | None = None  # Se o status mudar para INACTIVE
    inactivated_by_id: str | None = None
    inactivated_by_name: str | None = None

    deleted_at: datetime | None = None  # Para soft delete
    deleted_by_id: str | None = None
    deleted_by_name: str | None = None

    def __post_init__(self):
        self.name = self.name.strip().capitalize()
        if self.name_lowercase:
            self.name_lowercase = self.name_lowercase.strip().lower()
        else:
            self.name_lowercase = self.name.lower()

        if self.description:
            self.description = self.description.strip()
        if self.image_url:
            self.image_url = self.image_url.strip()
        if self.internal_code:
            self.internal_code = self.internal_code.strip().upper()
        if self.ean_code:
            self.ean_code = self.ean_code.strip()
        if self.brand:
            self.brand = self.brand.strip().capitalize()
        if self.unit_of_measure:
            self.unit_of_measure = self.unit_of_measure.strip().upper()
        if self.categoria_name: # Normaliza o nome da categoria
            self.categoria_name = self.categoria_name.strip().capitalize()

        if not isinstance(self.sale_price, Money):
            self.sale_price = Money.mint("0.00")
        if not isinstance(self.cost_price, Money):
            self.cost_price = Money.mint("0.00")

        # Garantir que os níveis de estoque sejam inteiros, tratando None e possíveis strings
        try:
            self.quantity_on_hand = int(self.quantity_on_hand) if self.quantity_on_hand is not None else 0
        except (ValueError, TypeError):
            self.quantity_on_hand = 0 # Default to 0 if conversion fails
        try:
            self.minimum_stock_level = int(self.minimum_stock_level) if self.minimum_stock_level is not None else 0
        except (ValueError, TypeError):
            self.minimum_stock_level = 0 # Default to 0 if conversion fails
        try:
            self.maximum_stock_level = int(self.maximum_stock_level) if self.maximum_stock_level is not None else 0
        except (ValueError, TypeError):
            self.maximum_stock_level = 0 # Default to 0 if conversion fails

        if self.quantity_on_hand is None:
            self.quantity_on_hand = 0
        if self.minimum_stock_level is None:
            self.minimum_stock_level = 0
        if self.maximum_stock_level is None:
            self.maximum_stock_level = 0

        # Se o produto está sendo criado como ACTIVE e não tem activated_at, define-o
        if self.status == RegistrationStatus.ACTIVE and self.created_at and not self.activated_at:
            self.activated_at = self.created_at
            self.activated_by_id = self.created_by_id
            self.activated_by_name = self.created_by_name

        if not self.ncm or not isinstance(self.ncm, dict) or self.ncm.get("code") is None:
            self.ncm = {"code": None, "description": None, "full_description": None}

    def to_dict(self) -> dict[str, Any]:
        """Retorna um dicionário representando o objeto Produto."""
        # Converte Money para dicionário
        return {
            "id": self.id,
            "empresa_id": self.empresa_id,
            "name": self.name,
            "name_lowercase": self.name_lowercase,
            "categoria_id": self.categoria_id,
            "categoria_name": self.categoria_name,
            "description": self.description,
            "internal_code": self.internal_code,
            "ean_code": self.ean_code,
            "brand": self.brand,
            "sale_price": self.sale_price,  # Mantem como uma instância de Money
            "cost_price": self.cost_price,  # Mantem como uma instância de Money
            "quantity_on_hand": self.quantity_on_hand,
            "unit_of_measure": self.unit_of_measure,
            "minimum_stock_level": self.minimum_stock_level,
            "maximum_stock_level": self.maximum_stock_level,
            "ncm": self.ncm,  # Nomenclatura Comum do Mercosul
            "status": self.status,  # Armazena o nome do enum
            "image_url": self.image_url,
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
        Retorna um dicionário para ser salvo no database.
        O ID do produto não está presente; será o ID do documento.
        Filtra chaves com valor None antes de salvar.
        """
        # Converte Money para dicionário
        dict_db = {
            "empresa_id": self.empresa_id,
            "name": self.name,
            "name_lowercase": self.name_lowercase,
            "categoria_id": self.categoria_id,
            "categoria_name": self.categoria_name,
            "description": self.description,
            "internal_code": self.internal_code,
            "ean_code": self.ean_code,
            "brand": self.brand,
            "sale_price": self.sale_price.to_dict(),
            "cost_price": self.cost_price.to_dict(),
            "quantity_on_hand": self.quantity_on_hand,
            "unit_of_measure": self.unit_of_measure,
            "minimum_stock_level": self.minimum_stock_level,
            "maximum_stock_level": self.maximum_stock_level,
            "status": self.status.name,  # Salva o nome do enum no DB
            "ncm": self.ncm,  # Nomenclatura Comum do Mercosul
            "image_url": self.image_url,
            "created_at": self.created_at if self.created_at else datetime.now(UTC),
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
        # Filtra chaves com valor None
        return {k: v for k, v in dict_db.items() if v is not None}

    @classmethod
    def from_dict(cls, data: dict[str, Any], doc_id: str | None = None) -> "Produto":
        """Cria uma instância de Produto a partir de um dicionário (ex: do Firestore)."""
        # Converte enums
        status_data = data.get("status", RegistrationStatus.ACTIVE)
        status = status_data # Por padrão status é do tipo RegistrationStatus

        if not isinstance(status_data, RegistrationStatus):
            if isinstance(status_data, str) and status_data in RegistrationStatus.__members__:
                status = RegistrationStatus[status_data]
            else:
                status = RegistrationStatus.ACTIVE

        # Database retorna Timestamps, que precisam ser convertidos para datetime
        created_at = data.get("created_at")
        if created_at and not isinstance(created_at, datetime):
            created_at = created_at.to_datetime() if hasattr(
                # Compatibilidade com Timestamp do Database
                created_at, 'to_datetime') else None

        updated_at = data.get("updated_at")
        if updated_at and not isinstance(updated_at, datetime):
            updated_at = updated_at.to_datetime() if hasattr(
                updated_at, 'to_datetime') else None

        activated_at = data.get("activated_at")
        if activated_at and not isinstance(activated_at, datetime):
            activated_at = activated_at.to_datetime() if hasattr(
                activated_at, 'to_datetime') else None

        inactivated_at = data.get("inactivated_at")
        if inactivated_at and not isinstance(inactivated_at, datetime):
            inactivated_at = inactivated_at.to_datetime() if hasattr(
                inactivated_at, 'to_datetime') else None

        deleted_at = data.get("deleted_at")
        if deleted_at and not isinstance(deleted_at, datetime):
            deleted_at = deleted_at.to_datetime() if hasattr(
                deleted_at, 'to_datetime') else None

        sale_price_data: dict = data["sale_price"]
        cost_price_data: dict = data["cost_price"]

        # Preço de venda
        amount_cents: int = sale_price_data["amount_cents"]  # Valor monetário retornado do banco já vem armazenado como inteiro
        currency_symbol: str = sale_price_data["currency_symbol"]
        sale_price: Money = Money.from_dict({"amount_cents": amount_cents, "currency_symbol": currency_symbol})

        # Preço de custo
        amount_cents: int = cost_price_data["amount_cents"]  # Valor monetário retornado do banco já vem armazenado como inteiro
        currency_symbol: str = cost_price_data["currency_symbol"]
        cost_price: Money = Money.from_dict({"amount_cents": amount_cents, "currency_symbol": currency_symbol})

        return cls(
            # Usa doc_id se fornecido (ID do documento Firestore)
            id=doc_id or data.get("id"),
            empresa_id=data["empresa_id"],
            name=data["name"],
            name_lowercase=data.get("name_lowercase", data["name"]),
            categoria_id=data["categoria_id"],
            categoria_name=data["categoria_name"], # Adicionado
            description=data.get("description"),
            internal_code=data.get("internal_code"),
            ean_code=data.get("ean_code"),
            brand=data.get("brand"),
            sale_price=sale_price,
            cost_price=cost_price,
            quantity_on_hand=data.get("quantity_on_hand", 0),
            unit_of_measure=data.get("unit_of_measure"),
            minimum_stock_level=data.get("minimum_stock_level", 0),
            maximum_stock_level=data.get("maximum_stock_level", 0),
            ncm=data.get("ncm", {"code": None, "description": None, "full_description": None}),
            status=status,
            image_url=data.get("image_url"),
            created_at=created_at,
            created_by_id=data.get("created_by_id"),
            created_by_name=data.get("created_by_name"),
            updated_at=updated_at,
            updated_by_id=data.get("updated_by_id"),
            updated_by_name=data.get("updated_by_name"),
            activated_at=activated_at,
            activated_by_id=data.get("activated_by_id"),
            activated_by_name=data.get("activated_by_name"),
            inactivated_at=inactivated_at,
            inactivated_by_id=data.get("inactivated_by_id"),
            inactivated_by_name=data.get("inactivated_by_name"),
            deleted_at=deleted_at,
            deleted_by_id=data.get("deleted_by_id"),
            deleted_by_name=data.get("deleted_by_name"),
        )
