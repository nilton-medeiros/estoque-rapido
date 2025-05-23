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
    def get_all(self, empresa_id: str, status_deleted: bool = False) ->  tuple[list[Produto], int]:
        """
        Encontra todos os produtos de uma empresa no repositório.

        Filtro (status_deleted): Se True, somente as categorias inativas serão retornadas.
                Caso contrário, todas as categorias serão retornadas menos as inativas.
        """
        raise NotImplementedError(
        "Este método deve ser implementado pela subclasse")

    @abstractmethod
    def get_active_categorias_summary(self, empresa_id: str) -> list[dict[str, Any]]:
        """
        Obtém um resumo (ID, nome, descrição) de todas as categorias ativas
        de uma empresa, ordenadas por nome.

        Somente as categorias com status "ACTIVE" são incluídas.

        Args:
            empresa_id (str): O ID da empresa para buscar as categorias.

        Returns:
            list[dict[str, Any]]: Uma lista de dicionários, onde cada dicionário
                                  contém 'id', 'name', e 'description' da categoria.
                                  Retorna uma lista vazia se nenhuma categoria for encontrada.

        Raises:
            ValueError: Se empresa_id for nulo ou vazio.
            Exception: Para erros de Firebase ou outros erros inesperados (re-lançados).
        """
        raise NotImplementedError(
        "Este método deve ser implementado pela subclasse")
