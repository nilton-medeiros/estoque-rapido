from dataclasses import dataclass
from datetime import datetime
from typing import Any

from src.domains.produtos.models.produtos_subclass import ProductStatus


@dataclass
class ProdutoCategorias:
    """    Categorias de produtos    """
    name: str
    name_lowercase: str
    empresa_id: str
    status: ProductStatus = ProductStatus.ACTIVE
    id: str | None = None
    description: str | None = None
    image_url: str | None = None
    created_at: datetime | None = None
    created_by_id: str | None = None
    created_by_name: str | None = None
    activated_at: datetime | None = None
    activated_by_id: str | None = None
    activated_by_name: str | None = None
    updated_at: datetime | None = None
    updated_by_id: str | None = None
    updated_by_name: str | None = None
    inactivated_at: datetime | None = None
    inactivated_by_id: str | None = None
    inactivated_by_name: str | None = None
    deleted_at: datetime | None = None
    deleted_by_id: str | None = None
    deleted_by_name: str | None = None

    def __post_init__(self):
        self.name = self.name.strip().capitalize()
        self.name_lowercase = self.name_lowercase.strip().lower()  # Para buscas case insensitive
        self.description = self.description.strip() if self.description else None
        self.image_url = self.image_url.strip() if self.image_url else None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "empresa_id": self.empresa_id,
            "name": self.name,
            "name_lowercase": self.name_lowercase,
            "description": self.description,
            "status": self.status,
            "image_url": self.image_url,
            "created_at": self.created_at,
            "created_by_id": self.created_by_id,
            "created_by_name": self.created_by_name,
            "updated_at": self.updated_at,
            "updated_by_id": self.updated_by_id,
            "updated_by_name": self.updated_by_name,
            "deleted_at": self.deleted_at,
            "deleted_by_id": self.deleted_by_id,
            "deleted_by_name": self.deleted_by_name,
        }

    def to_dict_db(self) -> dict[str, Any]:
        """
        O ID da categoria não está presente no dicionário para o banco de dados;
        caso não exista, será criado pelo repositório do banco de dados."""
        dict_db: dict[str, Any] = {
            "empresa_id": self.empresa_id,
            "name": self.name,
            "name_lowercase": self.name_lowercase,
            "description": self.description,
            "status": self.status.name,
            "image_url": self.image_url,
            "created_at": self.created_at,
            "created_by_id": self.created_by_id,
            "created_by_name": self.created_by_name,
            "updated_at": self.updated_at,
            "updated_by_id": self.updated_by_id,
            "updated_by_name": self.updated_by_name,
            "deleted_at": self.deleted_at,
            "deleted_by_id": self.deleted_by_id,
            "deleted_by_name": self.deleted_by_name,
        }

        dict_db_filtered = {k: v for k, v in dict_db.items() if v is not None}

        return dict_db_filtered

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProdutoCategorias":
        status = ProductStatus.ACTIVE

        if status_data := data.get("status"):
            if isinstance(status_data, ProductStatus):
                status = status_data
            else:
                status = ProductStatus[status_data]

        return cls(
            id=data.get("id"),
            empresa_id=data["empresa_id"],
            name=data["name"],
            name_lowercase=data.get("name_lowercase", data["name"]),
            description=data.get("description"),
            status=status,
            image_url=data.get("image_url"),
            created_at=data.get("created_at"),
            created_by_id=data.get("created_by_id"),
            created_by_name=data.get("created_by_name"),
            updated_at=data.get("updated_at"),
            updated_by_id=data.get("updated_at"),
            updated_by_name=data.get("updated_by_name"),
            deleted_at=data.get("deleted_at"),
            deleted_by_id=data.get("deleted_by_id"),
            deleted_by_name=data.get("deleted_by_name"),
        )
