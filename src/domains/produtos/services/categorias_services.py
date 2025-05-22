from src.domains.produtos.models import ProdutoCategorias, ProdutoStatus
from src.domains.produtos.repositories import CategoriasRepository
from src.domains.shared import NomePessoa
from src.shared import get_uuid


class CategoriasServices:
    """Serviço de gerenciamento de categorias de produtos."""

    def __init__(self, repository: CategoriasRepository):
        self.repository = repository


    async def create(self, categoria: ProdutoCategorias, usuario: dict) -> str:
        """Envia os dados da nova categoria para o repositório criar a categoria"""
        if not usuario.get("id"):
            raise ValueError("ID do usuário é necessário")

        # Gera por padrão um uuid raw (sem ons hífens) com prefixo 'cat_'
        categoria.id = "cat_" + get_uuid()

        # Atribuição de created_at, updated_at será feita pelo repositório do banco de dados com o tipo TIMESTAMP do db
        categoria.created_by_id = usuario["id"]
        user_name: NomePessoa = usuario["name"]
        categoria.created_by_name = user_name.nome_completo  # Desnormalização para otimizar indices no banco de dados

        # Envia para o repositório selecionado em empresas_controllrer salvar
        return await self.repository.save(categoria)


    async def update(self, categoria: ProdutoCategorias, usuario: dict) -> str:
        """Atualiza os dados de uma categoria existente"""
        if not categoria.id:
            raise ValueError("ID da categoria é necessário")
        if not usuario.get("id"):
            raise ValueError("ID do usuário é necessário")

        # Atribuição de created_at, updated_at será feita pelo repositório do banco de dados com o tipo TIMESTAMP do db
        categoria.updated_by_id = usuario["id"]
        user_name: NomePessoa = usuario["name"]
        categoria.updated_by_name = user_name.nome_completo  # Desnormalização para otimizar indices no banco de dados

        # Envia para o repositório selecionado em empresas_controllrer salvar
        return await self.repository.save(categoria)


    async def update_status(self, categoria: ProdutoCategorias, usuario: dict, status: ProdutoStatus) -> bool:
        """Atualiza o status de uma categoria existente"""
        user_name: NomePessoa = usuario["name"]
        categoria.status = status

        match status:
            case ProdutoStatus.ACTIVE:
                categoria.activated_at = None # Remove o datetime, será atribuido pelo SDK do banco TIMESTAMP
                categoria.activated_by_id = usuario["id"]
                categoria.activated_by_name = user_name.nome_completo  # Desnormalização p/ otimização de índices no db
            case ProdutoStatus.INACTIVE:
                categoria.inactivated_at = None# Remove o datetime, será atribuido pelo SDK do banco TIMESTAMP
                categoria.inactivated_by_id = usuario["id"]
                categoria.inactivated_by_name = user_name.nome_completo  # Desnormalização p/ otimização de índices no db
            case ProdutoStatus.DELETED:
                categoria.deleted_at = None # Remove o datetime, será atribuido pelo SDK do banco TIMESTAMP
                categoria.deleted_by_id = usuario["id"]
                categoria.deleted_by_name = user_name.nome_completo  # Desnormalização p/ otimização de índices no db

        id = await self.repository.save(categoria)
        return True if id else False


    async def get_by_id(self, categoria_id: str) -> ProdutoCategorias | None:
        """Busca uma categoria pelo ID"""
        return await self.repository.get_by_id(categoria_id=categoria_id)


    async def get_all(self, empresa_id: str, status_deleted: bool = False) -> tuple[list[ProdutoCategorias], int]:
        """Busca todas as categorias da empresa logada que sejam ativa ou não, dependendo do status_deleted True/False."""
        return await self.repository.get_all(empresa_id, status_deleted)
