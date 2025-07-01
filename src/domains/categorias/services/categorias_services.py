from typing import Any
from src.domains.shared import RegistrationStatus
from src.domains.categorias.models import ProdutoCategorias
from src.domains.categorias.repositories import CategoriasRepository
from src.domains.shared import NomePessoa
from src.shared.utils import get_uuid


class CategoriasServices:
    """Serviço de gerenciamento de categorias de produtos."""

    def __init__(self, repository: CategoriasRepository):
        self.repository = repository

    def create(self, categoria: ProdutoCategorias, usuario: dict) -> str:
        """Envia os dados da nova categoria para o repositório criar a categoria"""
        if not usuario.get("id"):
            raise ValueError("ID do usuário é necessário")

        # Gera por padrão um uuid raw (sem ons hífens) com prefixo 'cat_'
        categoria.id = "cat_" + get_uuid()

        # Atribuição de created_at, updated_at será feita pelo repositório do banco de dados com o tipo TIMESTAMP do db
        categoria.created_by_id = usuario["id"]
        user_name: NomePessoa = usuario["name"]
        # Desnormalização para otimizar indices no banco de dados
        categoria.created_by_name = user_name.nome_completo

        # Envia para o repositório selecionado em empresas_controllrer salvar
        return self.repository.save(categoria)

    def update(self, categoria: ProdutoCategorias, usuario: dict) -> str:
        """Atualiza os dados de uma categoria existente"""
        if not categoria.id:
            raise ValueError("ID da categoria é necessário")
        if not usuario.get("id"):
            raise ValueError("ID do usuário é necessário")

        # Atribuição de created_at, updated_at será feita pelo repositório do banco de dados com o tipo TIMESTAMP do db
        categoria.updated_by_id = usuario["id"]
        user_name: NomePessoa = usuario["name"]
        # Desnormalização para otimizar indices no banco de dados
        categoria.updated_by_name = user_name.nome_completo

        # Envia para o repositório selecionado em empresas_controllrer salvar
        return self.repository.save(categoria)

    def update_status(self, categoria: ProdutoCategorias, usuario: dict, status: RegistrationStatus) -> bool:
        """Atualiza o status de uma categoria existente"""
        user_name: NomePessoa = usuario["name"]
        categoria.status = status

        match status:
            case RegistrationStatus.ACTIVE:
                # Remove o datetime, será atribuido pelo SDK do banco TIMESTAMP
                categoria.activated_at = None
                categoria.activated_by_id = usuario["id"]
                # Desnormalização p/ otimização de índices no db
                categoria.activated_by_name = user_name.nome_completo
            case RegistrationStatus.INACTIVE:
                # Remove o datetime, será atribuido pelo SDK do banco TIMESTAMP
                categoria.inactivated_at = None
                categoria.inactivated_by_id = usuario["id"]
                # Desnormalização p/ otimização de índices no db
                categoria.inactivated_by_name = user_name.nome_completo
            case RegistrationStatus.DELETED:
                # Remove o datetime, será atribuido pelo SDK do banco TIMESTAMP
                categoria.deleted_at = None
                categoria.deleted_by_id = usuario["id"]
                # Desnormalização p/ otimização de índices no db
                categoria.deleted_by_name = user_name.nome_completo

        id = self.repository.save(categoria)
        return True if id else False

    def get_by_id(self, categoria_id: str) -> ProdutoCategorias | None:
        """Busca uma categoria pelo ID"""
        return self.repository.get_by_id(categoria_id=categoria_id)

    def get_all(self, empresa_id: str, status_deleted: bool = False) -> tuple[list[ProdutoCategorias], int]:
        """Busca todas as categorias da empresa logada que sejam ativa ou não, dependendo do status_deleted True/False."""
        return self.repository.get_all(empresa_id, status_deleted)

    def get_summary(self, empresa_id: str) -> list[dict[str, Any]]:
        """
        Obtém um resumo (ID, nome, descrição) de todas as categorias ativas
        de uma empresa, ordenadas por nome.

        Somente as categorias com status "ACTIVE" são incluídas.

        Args:
            empresa_id (str): O ID da empresa para buscar as categorias.

        Returns: list [dict[str, Any]]
             Uma lista de dicionários, onde cada dicionário
                                  contém 'id', 'name', e 'description' da categoria.
                                  Retorna uma lista vazia se nenhuma categoria for encontrada.

        Raises:
            ValueError: Se empresa_id for nulo ou vazio.
            Exception: Para erros de Firebase ou outros erros inesperados (re-lançados).
        """
        return self.repository.get_active_categorias_summary(empresa_id)

    def get_active_id(self, company_id: str, name: str) -> str | None:
        """Obtem o ID da categoria pelo nome da categoria"""
        name = name.strip().lower()
        return self.repository.get_active_id_by_name(company_id=company_id, name=name)
