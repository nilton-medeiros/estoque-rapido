from src.domains.produtos.models import ProdutoCategorias
from src.domains.produtos.repositories import CategoriasRepository


class CategoriasServices:
    """Serviço de gerenciamento de categorias de produtos."""

    def __init__(self, repository: CategoriasRepository):
        self.repository = repository


    async def create(self, categoria: ProdutoCategorias, usuario: dict) -> str:
        return ''


    async def update(self, categoria: ProdutoCategorias, usuario: dict) -> str:
        return ''


    async def get_by_id(self, categoria_id: str) -> ProdutoCategorias | None:
        return None


    async def get_all(self, empresa_id: str, status_deleted: bool = False) -> tuple[list[ProdutoCategorias], int]:
        """Busca todas as categorias da empresa logada que sejam ativa ou não, dependendo do status_deleted True/False."""
        return await self.repository.get_all(empresa_id, status_deleted)
