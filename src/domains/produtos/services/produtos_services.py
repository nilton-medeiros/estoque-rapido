from src.domains.produtos.models import Produto, ProdutoStatus
from src.domains.produtos.repositories import ProdutosRepository
from src.domains.shared import NomePessoa
from src.shared.utils import get_uuid


class ProdutosServices:
    """Serviço de gerenciamento de produtos."""

    def __init__(self, repository: ProdutosRepository):
        self.repository = repository


    def create(self, produto: Produto, usuario: dict) -> str | None:
        """Envia os dados do novo produto para o repositório"""
        if not usuario.get("id"):
            raise ValueError("ID do usuário é necessário")

        # Gera por padrão um uuid raw (sem ons hífens) com prefixo 'pro_'
        produto.id = "pro_" + get_uuid()

        # Atribuição de created_at, updated_at será feita pelo repositório do banco de dados com o tipo TIMESTAMP do db
        produto.created_by_id = usuario["id"]
        user_name: NomePessoa = usuario["name"]
        produto.created_by_name = user_name.nome_completo  # Desnormalização para otimizar indices no banco de dados

        # Envia para o repositório selecionado em empresas_controllrer salvar
        return self.repository.save(produto)


    def update(self, produto: Produto, usuario: dict) -> str | None:
        """Atualiza os dados de uma produto existente"""
        if not produto.id:
            raise ValueError("ID da produto é necessário")
        if not usuario.get("id"):
            raise ValueError("ID do usuário é necessário")

        # Atribuição de created_at, updated_at será feita pelo repositório do banco de dados com o tipo TIMESTAMP do db
        produto.updated_by_id = usuario["id"]
        user_name: NomePessoa = usuario["name"]
        produto.updated_by_name = user_name.nome_completo  # Desnormalização para otimizar indices no banco de dados

        # Envia para o repositório selecionado em empresas_controllrer salvar
        return self.repository.save(produto)


    def update_status(self, produto: Produto, usuario: dict, status: ProdutoStatus) -> bool:
        """Atualiza o status de uma produto existente"""
        user_name: NomePessoa = usuario["name"]
        produto.status = status

        match status:
            case ProdutoStatus.ACTIVE:
                produto.activated_at = None # Remove o datetime, será atribuido pelo SDK do banco TIMESTAMP
                produto.activated_by_id = usuario["id"]
                produto.activated_by_name = user_name.nome_completo  # Desnormalização p/ otimização de índices no db
            case ProdutoStatus.INACTIVE:
                produto.inactivated_at = None# Remove o datetime, será atribuido pelo SDK do banco TIMESTAMP
                produto.inactivated_by_id = usuario["id"]
                produto.inactivated_by_name = user_name.nome_completo  # Desnormalização p/ otimização de índices no db
            case ProdutoStatus.DELETED:
                produto.deleted_at = None # Remove o datetime, será atribuido pelo SDK do banco TIMESTAMP
                produto.deleted_by_id = usuario["id"]
                produto.deleted_by_name = user_name.nome_completo  # Desnormalização p/ otimização de índices no db

        id = self.repository.save(produto)
        return id is not None


    def get_by_id(self, produto_id: str) -> Produto | None:
        """Busca uma produto pelo ID"""
        return self.repository.get_by_id(produto_id=produto_id)


    def get_all(self, status_deleted: bool = False) -> tuple[list[Produto], int]:
        """Busca todas as produtos da empresa logada que sejam ativa ou não, dependendo do status_deleted True/False."""
        return self.repository.get_all(status_deleted)
