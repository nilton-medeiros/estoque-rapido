from typing import Optional
from models.cnpj import CNPJ
from models.company import Company
from storage.data.interfaces.company_repository import CompanyRepository

"""
Essa estrutura garante uma separação clara de responsabilidades, onde a CompanyService atua como intermediária,
organizando e validando os dados antes de delegar a execução das operações ao repositório de dados.
Isso promove uma arquitetura mais limpa e modular, facilitando manutenção e escalabilidade do sistema.
"""

class CompanyService:
    """Seriço de gerenciamento de empresas.

    A classe CompanyService é um serviço dedicado ao gerenciamento de empresas,
    facilitando a interação entre a aplicação e o banco de dados.
    Ela possui métodos específicos para criação, atualização e busca de empresas,
    delegando essas operações ao repositório de dados.

    Args: repository (CompanyRepository): Repositório Empresa do database selecionado em company_controller.

    Attributes:
        repository (CompanyRepository): Repositório Empresa.

    Example:
        Exemplo de como instanciar e usar a classe:
        >>> repository = FirebaseUserRepository(password)
        >>> company_service = CompanyService(repository)
    """

    def __init__(self, repository: CompanyRepository):
        self.repository = repository

    async def create_company(self, company: Company):
        """Envia os dados da nova empresa para o repositório criar.

        Este método é responsável por enviar os dados da nova empresa para o repositório,
        que, por sua vez, cria uma nova entrada na entidade empresas do banco de dados.

        Args:
            company (Company): Instância da Empresa a ser criada.

        Returns:
            ID do documento da Empresa criada

        Raises:
            ValueError: Descrição da exceção que pode ser lançada, se aplicável.

        Exemplo:
            >>> repository = FirebaseUserRepository(password)
            >>> company_service = CompanyService(repository)
            >>> company_id = await company_service.create_company(company)
        """

        existing_company = await self.repository.find_by_cnpj(company.cnpj)

        if existing_company:
            raise ValueError("Já existe uma empresa com este CNPJ")

        # Envia para o repositório selecionado em company_controllrer salvar
        return await self.repository.save(company)

    async def update_company(self, company: Company) -> Company:
        """Atualiza os dados de uma empresa existente.

        Este método atualiza os dados de uma empresa existente. Ele envia as informações
        atualizadas para o repositório, que localiza a empresa pelo ID na entidade empresas e
        realiza as modificações necessárias.

        Args:
            company (Company): Instância da Empresa a ser criada.

        Returns:
            ID do documento da Empresa alterada

        Raises:
            ValueError: Descrição da exceção que pode ser lançada, se aplicável.

        Exemplo:
            >>> repository = FirebaseUserRepository(password)
            >>> company_service = CompanyService(repository)
            >>> company_id = await company_service.update_company(company)
        """

        if not company.id:
            raise ValueError("ID da empresa é necessário para atualização")
        return await self.repository.save(company)

    async def find_user_by_cnpj(self, cnpj: CNPJ) -> Optional[Company]:
        """Busca uma empresa no banco de dados utilizando o CNPJ.

        Este método busca uma empresa no banco de dados utilizando o CNPJ fornecido.
        Ele solicita ao repositório que encontre a empresa correspondente na entidade empresas.

        Args:
            cnpj (CNPJ): Objeto da classe CNPJ da empresa a ser encontrada

        Returns:
            Optional[Company]: Empresa encontrada ou None se não existir
        """
        return await self.repository.find_by_cnpj(cnpj)
