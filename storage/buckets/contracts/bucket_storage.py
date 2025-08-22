from abc import ABC, abstractmethod


class BucketStorage(ABC):

    @abstractmethod
    def upload(self, local_path: str, key: str) -> str:
        """Retorna a url completa do arquivo no bucket"""
        raise NotImplementedError("Este método deve ser implementado pela subclasse")

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Retorna True se sucesso ao deletar, False caso contrário"""
        raise NotImplementedError("Este método deve ser implementado pela subclasse")
