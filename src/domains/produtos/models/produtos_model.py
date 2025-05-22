from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

# Supondo que ProdutoStatus esteja no mesmo local ou acessível
from src.domains.produtos.models.produtos_subclass import ProdutoStatus
from src.shared import Money


@dataclass
class Produto:
    """
    Representa um produto na subcoleção 'produtos' dentro de uma 'empresa'.
    """
    empresa_id: str  # ID da empresa pai
    name: str
    categoria_id: str  # ID da categoria (da coleção 'produto_categorias')

    # --- Campos Essenciais do Produto ---
    sale_price: Money  # Preço de venda
    cost_price: Money = Money.mint("0.00")    # Preço de custo, default 0

    # --- Campos de Identificação e Códigos ---
    internal_code: str | None = None  # Código interno/SKU
    ean_code: str | None = None      # Código EAN (código de barras)

    # --- Campos Descritivos ---
    description: str | None = None
    image_url: str | None = None
    brand: str | None = None          # Marca do produto

    # --- Campos de Estoque ---
    quantity_on_hand: int = 0
    # Unidade de medida (ex: "un", "L", "kg", "pacote")
    unit_of_measure: str | None = None
    minimum_stock_level: int | None = None
    maximum_stock_level: int | None = None

    # --- Campos de Status e Auditoria ---
    status: ProdutoStatus = ProdutoStatus.ACTIVE
    # ID do documento no Firestore (gerado automaticamente)
    id: str | None = None

    created_at: datetime | None = field(default_factory=datetime.utcnow)
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
            self.unit_of_measure = self.unit_of_measure.strip().lower()
        if not isinstance(self.cost_price, Money):
            self.cost_price = Money.mint("0.00")

        # Se o produto está sendo criado como ACTIVE e não tem activated_at, define-o
        if self.status == ProdutoStatus.ACTIVE and self.created_at and not self.activated_at:
            self.activated_at = self.created_at
            self.activated_by_id = self.created_by_id
            self.activated_by_name = self.created_by_name

    def to_dict(self) -> dict[str, Any]:
        """Retorna um dicionário representando o objeto Produto."""
        # Converte Money para dicionário
        return {
            "id": self.id,
            "empresa_id": self.empresa_id,
            "name": self.name,
            "categoria_id": self.categoria_id,
            "description": self.description,
            "internal_code": self.internal_code,
            "ean_code": self.ean_code,
            "brand": self.brand,
            "sale_price": self.sale_price,  # Converte Money para dicionário
            "cost_price": self.cost_price,
            "quantity_on_hand": self.quantity_on_hand,
            "unit_of_measure": self.unit_of_measure,
            "minimum_stock_level": self.minimum_stock_level,
            "maximum_stock_level": self.maximum_stock_level,
            "status": self.status.name,  # Armazena o nome do enum
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
            "categoria_id": self.categoria_id,
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
            "image_url": self.image_url,
            "created_at": self.created_at if self.created_at else datetime.utcnow(),
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
        status_data = data.get("status")
        status = ProdutoStatus.ACTIVE  # Padrão
        if status_data:
            if isinstance(status_data, ProdutoStatus):
                status = status_data
            else:
                try:
                    status = ProdutoStatus[status_data]
                except KeyError:
                    # Lidar com status inválido, talvez logar um aviso ou usar um padrão
                    status = ProdutoStatus.INACTIVE

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

        sale_price_data = data.get("sale_price")
        cost_price_data = data.get("cost_price")

        sale_price = Money.from_dict(
            sale_price_data) if sale_price_data else Money.mint("0.00")
        cost_price = Money.from_dict(
            cost_price_data) if cost_price_data else Money.mint("0.00")

        return cls(
            # Usa doc_id se fornecido (ID do documento Firestore)
            id=doc_id or data.get("id"),
            empresa_id=data["empresa_id"],
            name=data["name"],
            categoria_id=data["categoria_id"],
            description=data.get("description"),
            internal_code=data.get("internal_code"),
            ean_code=data.get("ean_code"),
            brand=data.get("brand"),
            sale_price=sale_price,
            cost_price=cost_price,
            quantity_on_hand=data.get("quantity_on_hand", 0),
            unit_of_measure=data.get("unit_of_measure"),
            minimum_stock_level=data.get("minimum_stock_level"),
            maximum_stock_level=data.get("maximum_stock_level"),
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
