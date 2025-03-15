from abc import ABC, abstractmethod
from typing import Optional

from src.domains.empresas.models.cnpj import CNPJ  # Importação direta para não ocorrer ciclo
from src.domains.empresas.models.empresa_model import Empresa  # Importação direta

class EmpresasRepository(ABC):
    """Classe base abstrata que define o contrato para operações de repositório de empresas."""

    @abstractmethod
    def count(self) -> int:
        """Contar o número total de empresas no repositório."""
        raise NotImplementedError("Este método deve ser implementado pela subclasse")

    @abstractmethod
    def delete(self, empresa_id: str) -> bool:
        """Excluir uma empresa por seu ID."""
        raise NotImplementedError("Este método deve ser implementado pela subclasse")

    @abstractmethod
    def exists_by_cnpj(self, cnpj: CNPJ) -> bool:
        """Verificar se uma empresa existe com o CNPJ fornecido."""
        raise NotImplementedError("Este método deve ser implementado pela subclasse")

    @abstractmethod
    def find_by_cnpj(self, cnpj: CNPJ) -> Optional[Empresa]:
        """Encontrar uma empresa por seu CNPJ."""
        raise NotImplementedError("Este método deve ser implementado pela subclasse")

    @abstractmethod
    def find_by_id(self, empresa_id: str) -> Optional[Empresa]:
        """Encontrar uma empresa por seu ID."""
        raise NotImplementedError("Este método deve ser implementado pela subclasse")

    @abstractmethod
    def save(self, empresa: Empresa) -> str:
        """Salvar uma empresa e retornar seu ID."""
        raise NotImplementedError("Este método deve ser implementado pela subclasse")

    @abstractmethod
    def _empresa_to_dict(self, empresa: Empresa) -> dict:
        """Converter uma instância de empresa em um dicionário para armazenamento no Firestore."""
        raise NotImplementedError("Este método deve ser implementado pela subclasse")

    @abstractmethod
    def _doc_to_empresa(self, doc_data: dict) -> Empresa:
        """Converter os dados de um documento do Firestore em uma instância de empresa."""
        raise NotImplementedError("Este método deve ser implementado pela subclasse")
