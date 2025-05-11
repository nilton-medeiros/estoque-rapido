from datetime import datetime
from typing import Optional

from src.domains.empresas.models.cnpj import CNPJ
from src.domains.empresas.models.empresa_model import Empresa
from src.domains.empresas.models.empresa_subclass import Status
from src.domains.empresas.repositories.contracts.empresas_repository import EmpresasRepository
from src.shared import get_uuid

"""
Essa estrutura garante uma separação clara de responsabilidades, onde a EmpresasServices atua como intermediária,
organizando e validando os dados antes de delegar a execução das operações ao repositório de dados.
Isso promove uma arquitetura mais limpa e modular, facilitando manutenção e escalabilidade do sistema.
"""

class EmpresasServices:
    """Seriço de gerenciamento de empresas.

    A classe EmpresasServices é um serviço dedicado ao gerenciamento de empresas,
    facilitando a interação entre a aplicação e o banco de dados.
    Ela possui métodos específicos para criação, atualização e busca de empresas,
    delegando essas operações ao repositório de dados.

    Args: repository (EmpresasRepository): Repositório Empresas do database selecionado em empresas_controller.

    Attributes:
        repository (EmpresasRepository): Repositório Empresa.

    Example:
        Exemplo de como instanciar e usar a classe:
        >>> repository = FirebaseUserRepository(password)
        >>> empresas_services = EmpresasServices(repository)
    """

    def __init__(self, repository: EmpresasRepository):
        self.repository = repository

    async def create(self, empresa: Empresa, user: dict):
        """Envia os dados da nova empresa para o repositório criar.

        Este método é responsável por enviar os dados da nova empresa para o repositório,
        que, por sua vez, cria uma nova entrada na entidade empresas do banco de dados.

        Args:
            empresa (Empresa): Instância da Empresa a ser criada.

        Returns:
            ID do documento da Empresa criada

        Raises:
            ValueError: Descrição da exceção que pode ser lançada, se aplicável.

        Exemplo:
            >>> repository = FirebaseUserRepository(password)
            >>> empresas_services = EmpresasServices(repository)
            >>> empresa_id = await empresas_services.create_empresa(empresa)
        """

        # Se CNPJ foi informado, verifica se exite para evitar duplicidade com o mesmo CNPJ
        if empresa.cnpj:
            existing_empresa = await self.repository.find_by_cnpj(empresa.cnpj)
            if existing_empresa:
                raise ValueError("Já existe uma empresa com este CNPJ")
        if not user.get("id"):
            raise ValueError("ID do usuário é necessário")

        # Gera por padrão um uuid raw (sem os hífens) com prefixo 'emp_'
        empresa.id = 'emp_' + get_uuid()
        # A atribuição de created_at e updated_at será feita pelo repositório do banco de dados
        # usando SERVER_TIMESTAMP do banco de dados.
        empresa.created_by_id = user.get("id")
        user_name = user.get("name")
        empresa.created_by_name = user_name.nome_completo()  # Desnormalização para otimizar indices no banco de dados

        # Envia para o repositório selecionado em empresas_controllrer salvar
        return await self.repository.save(empresa)

    async def update(self, empresa: Empresa, usuario: dict) -> Empresa:
        """Atualiza os dados de uma empresa existente.

        Este método atualiza os dados de uma empresa existente. Ele envia as informações
        atualizadas para o repositório, que localiza a empresa pelo ID na entidade empresas e
        realiza as modificações necessárias.

        Args:
            empresa (Empresa): Instância da Empresa a ser criada.

        Returns:
            ID do documento da Empresa alterada

        Raises:
            ValueError: Descrição da exceção que pode ser lançada, se aplicável.

        Exemplo:
            >>> repository = FirebaseUserRepository(password)
            >>> empresas_services = EmpresasServices(repository)
            >>> empresa_id = await empresas_services.update_empresa(empresa)
        """

        if not empresa.id:
            raise ValueError("ID da empresa é necessário para atualização")
        if not usuario.get("id"):
            raise ValueError("ID do usuário é necessário")

        # A atribuição de updated_at será feita pelo repositório
        # usando SERVER_TIMESTAMP do banco de dados.
        empresa.updated_by_id = usuario.get("id")
        user_name = usuario.get("name")
        empresa.updated_by_name = user_name.nome_completo()  # Desnormalização para otimizar indices no banco de dados

        return await self.repository.save(empresa)

    async def update_status(self, empresa: Empresa, usuario: dict, status: Status) -> bool:
        """Altera o status de uma empresa no banco de dados."""
        user_name = usuario.get("name")

        if status.name == "ACTIVE":
            empresa.status = Status.ACTIVE
            empresa.activated_at = None  # Será atribuido pelo SDK do banco TIMESTAMP
            empresa.activated_by_id = usuario.get("id")
            empresa.activated_by_name = user_name.nome_completo()
        elif status.name == "DELETED":
            empresa.status = Status.DELETED
            empresa.deleted_at = None  # Será atribuido pelo SDK do banco TIMESTAMP
            empresa.deleted_by_id = usuario.get("id")
            empresa.deleted_by_name = user_name.nome_completo()
        elif status.name == "ARCHIVED":
            empresa.status = Status.ARCHIVED
            empresa.archived_at = None  # Será atribuido pelo SDK do banco TIMESTAMP
            empresa.archived_by_id = usuario.get("id")
            empresa.archived_by_name = user_name.nome_completo()

        id = await self.repository.save(empresa)
        if id:
            return True
        return False

    async def find_by_cnpj(self, cnpj: CNPJ) -> Optional[Empresa]:
        """Busca uma empresa no banco de dados utilizando o CNPJ.

        Este método busca uma empresa no banco de dados utilizando o CNPJ fornecido.
        Ele solicita ao repositório que encontre a empresa correspondente na entidade empresas.

        Args:
            cnpj (CNPJ): Objeto da classe CNPJ da empresa a ser encontrada

        Returns:
            Optional[Empresa]: Empresa encontrada ou None se não existir
        """
        return await self.repository.find_by_cnpj(cnpj)

    async def find_by_id(self, empresa_id: str) -> Optional[Empresa]:
        """Busca uma empresa no banco de dados utilizando o ID.

        Este método busca uma empresa no banco de dados utilizando o ID fornecido.
        Ele solicita ao repositório que encontre a empresa correspondente na entidade empresas.

        Args:
            empresa_id (str): ID da empresa a ser encontrada

        Returns:
            Optional[Empresa]: Empresa encontrada ou None se não existir
        """
        return await self.repository.find_by_id(empresa_id)

    async def find_all(self, ids_empresas: set[str]|list[str], status_active: bool = True) -> list[Empresa]:
        """Busca todas as empresas do usuário logado."""
        return await self.repository.find_all(ids_empresas=ids_empresas, status_active=status_active)
