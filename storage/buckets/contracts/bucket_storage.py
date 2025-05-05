from abc import ABC, abstractmethod


class BucketStorage(ABC):

    @abstractmethod
    async def upload(self, local_path: str, key: str) -> str:
        """Retorna a url completa do arquivo no bucket"""
        raise NotImplementedError("Este método deve ser implementado pela subclasse")

    @abstractmethod
    async def delete(self, key: str) -> str:
        """Retorna a url completa do arquivo no bucket"""
        raise NotImplementedError("Este método deve ser implementado pela subclasse")
