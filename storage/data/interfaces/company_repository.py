from abc import ABC, abstractmethod
from typing import Optional

from models.cnpj import CNPJ
from models.company import Company


class CompanyRepository(ABC):
    """Classe base abstrata que define o contrato para operações de repositório de empresas."""

    @abstractmethod
    def count(self) -> int:
        """Contar o número total de empresas no repositório."""
        raise NotImplementedError("Este método deve ser implementado pela subclasse")

    @abstractmethod
    def delete(self, company_id: str) -> bool:
        """Excluir uma empresa por seu ID."""
        raise NotImplementedError("Este método deve ser implementado pela subclasse")

    @abstractmethod
    def exists_by_cnpj(self, cnpj: CNPJ) -> bool:
        """Verificar se uma empresa existe com o CNPJ fornecido."""
        raise NotImplementedError("Este método deve ser implementado pela subclasse")

    @abstractmethod
    def find_by_cnpj(self, cnpj: CNPJ) -> Optional[Company]:
        """Encontrar uma empresa por seu CNPJ."""
        raise NotImplementedError("Este método deve ser implementado pela subclasse")

    @abstractmethod
    def find_by_id(self, company_id: str) -> Optional[Company]:
        """Encontrar uma empresa por seu ID."""
        raise NotImplementedError("Este método deve ser implementado pela subclasse")

    @abstractmethod
    def save(self, company: Company) -> str:
        """Salvar uma empresa e retornar seu ID."""
        raise NotImplementedError("Este método deve ser implementado pela subclasse")
