from abc import ABC, abstractmethod
from typing import Any

from src.domains.produtos.models import Produto


class ProdutosRepository(ABC):
    """Classe base abstrata que define o contrato para operações de repositório de produtos"""

    @abstractmethod
    def save(self, produto: Produto) -> str | None:
        """Salva um produto no repositório"""
        raise NotImplementedError(
        "Este método deve ser implementado pela subclasse")

    @abstractmethod
    def get_by_id(self, produto_id: str) -> Produto | None:
        """Encontra um produto pelo ID no repositório"""
        raise NotImplementedError(
        "Este método deve ser implementado pela subclasse")

    @abstractmethod
    def get_all(self, status_deleted: bool = False) ->  tuple[list[Produto], int]:
        """
        Encontra todos os produtos de uma empresa no repositório.

        Filtro (status_deleted): Se True, somente as categorias inativas serão retornadas.
                Caso contrário, todas as categorias serão retornadas menos as inativas.
        """
        raise NotImplementedError(
        "Este método deve ser implementado pela subclasse")
