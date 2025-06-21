from abc import ABC, abstractmethod
from typing import Optional

# Importação direta para não ocorrer ciclo
from src.domains.empresas.models.cnpj import CNPJ
from src.domains.empresas.models.empresa_model import Empresa


class EmpresasRepository(ABC):
    """Classe base abstrata que define o contrato para operações de repositório de empresas."""

    @abstractmethod
    def save(self, empresa: Empresa) -> str:
        """Salvar uma empresa e retornar seu ID."""
        raise NotImplementedError(
            "Este método deve ser implementado pela subclasse")

    @abstractmethod
    def find_by_id(self, empresa_id: str) -> Optional[Empresa]:
        """Encontrar uma empresa por seu ID que é o próprio CNPJ."""
        raise NotImplementedError(
            "Este método deve ser implementado pela subclasse")

    @abstractmethod
    def find_by_cnpj(self, cnpj: CNPJ) -> Optional[Empresa]:
        """Encontrar uma empresa por seu ID que é o próprio CNPJ."""
        raise NotImplementedError(
            "Este método deve ser implementado pela subclasse")

    @abstractmethod
    def exists_by_cnpj(self, cnpj: CNPJ) -> bool:
        """Verificar se uma empresa existe com o CNPJ fornecido."""
        raise NotImplementedError(
            "Este método deve ser implementado pela subclasse")

    @abstractmethod
    def find_all(self, ids_empresas: set[str] | list[str], status_active: bool = True) -> list[Empresa]:
        """Lista as empresas do usuário logado"""
        raise NotImplementedError(
            "Este método deve ser implementado pela subclasse")

    @abstractmethod
    def count_inactivated(self, ids_empresas: set[str] | list[str]) -> int:
        """Conta as empresas inativas (deletadas ou arquivadas) dentro do conjunto ou lista de ids_empresas do usuário logado."""
        raise NotImplementedError(
            "Este método deve ser implementado pela subclasse")
