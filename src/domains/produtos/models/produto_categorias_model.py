from dataclasses import dataclass
from datetime import datetime

from src.domains.produtos.models.produtos_enum_subclass import ProdutoStatus


@dataclass
class ProdutoCategorias:
    """    Categorias de produtos    """
    name: str
    status: ProdutoStatus = ProdutoStatus.ACTIVE
    description: str | None = None
    image_url: str | None = None
    created_at: datetime | None = None
    created_by_id: str | None = None
    created_by_name: str | None = None
    updated_at: datetime | None = None
    updated_by_id: str | None = None
    updated_by_name: str | None = None
    deleted_at: datetime | None = None
    deleted_by_id: str | None = None
    deleted_by_name: str | None = None
