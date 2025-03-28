from abc import ABC, abstractmethod

from src.domain.models.app_config import AppConfig


class AppConfigRepository(ABC):
    """Classe base abstrata que define o contrato para operações de repositório de configurações de aplicativo."""

    @abstractmethod
    def get(self, id: str) -> AppConfig:
        """Retorna as configurações atuais do aplicativo."""
        raise NotImplementedError("Este método deve ser implementado pela subclasse")

    @abstractmethod
    def save(self, app_config: AppConfig):
        """Salva as configurações do aplicativo."""
        raise NotImplementedError("Este método deve ser implementado pela subclasse")

    @abstractmethod
    def delete(self, id: str) -> bool:
        """Exclui as configurações do aplicativo."""
        raise NotImplementedError("Este método deve ser implementado pela subclasse")
