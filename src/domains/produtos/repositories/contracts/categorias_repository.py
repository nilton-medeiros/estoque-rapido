from abc import ABC, abstractmethod

from src.domains.produtos.models import ProdutoCategorias


class CategoriasRepository(ABC):
    """Classe base abstrata que define o contrato para operações de repositório de categorias de produtos"""

    @abstractmethod
    async def save(self, categoria: ProdutoCategorias) -> str:
        """Salva uma categoria de produto no repositório"""
        raise NotImplementedError(
        "Este método deve ser implementado pela subclasse")

    @abstractmethod
    async def get_by_id(self, categoria_id: str) -> ProdutoCategorias | None:
        """Encontra uma categoria de produto pelo ID no repositório"""
        raise NotImplementedError(
        "Este método deve ser implementado pela subclasse")

    @abstractmethod
    async def get_all(self, empresa_id: str, status_deleted: bool = False) ->  tuple[list[ProdutoCategorias], int]:
        """
        Encontra todas as categorias de produto de uma empresa no repositório.

        Filtro (status_deleted): Se True, somente as categorias inativas serão retornadas.
                Caso contrário, todas as categorias serão retornadas menos as inativas.
        """
        raise NotImplementedError(
        "Este método deve ser implementado pela subclasse")
