from abc import ABC, abstractmethod

from src.domains.app_config.models.app_config_model import AppConfig


class AppConfigRepository(ABC):
    """Classe base abstrata que define o contrato para operações de repositório de configurações de aplicativo."""

    @abstractmethod
    async def get(self, config_id: str) -> AppConfig | None:
        """Retorna as configurações atuais do aplicativo."""
        raise NotImplementedError("Este método deve ser implementado pela subclasse")

    @abstractmethod
    async def save(self, config: AppConfig) -> str:
        """Salva as configurações do aplicativo."""
        raise NotImplementedError("Este método deve ser implementado pela subclasse")

    @abstractmethod
    def delete(self, id: str) -> bool:
        """Exclui as configurações do aplicativo."""
        raise NotImplementedError("Este método deve ser implementado pela subclasse")
