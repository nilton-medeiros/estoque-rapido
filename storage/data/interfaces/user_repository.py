from abc import ABC, abstractmethod
from typing import List, Optional

from src.domain.models.user import User


'''
Sobre o porque da interface UserRepository (Classe abstrata)
Esta interface define os métodos necessários para manipular e buscar usuários em um banco de dados.
Qualquer classe que herdar de UserRepository DEVE ter os métodos de UserRepository que recebe um User e retorna um User
1. Garante que todas as implementações (Firebase, MySQL, MariaDB, PostgreSQL) tenham os mesmos métodos
2. Permite trocar implementações (database) facilmente (porque todas seguem o mesmo contrato)
3. Ajuda na organização do código
O UserRepository em si nunca é usado diretamente - ele só serve como modelo para outras classes.
Por isso não precisamos implementar os métodos nele.
'''


class UserRepository(ABC):
    """Classe base abstrata que define o contrato para operações de repositório de usuários."""

    @abstractmethod
    async def count(self) -> int:
        """Retorna o número total de usuários da empresa logada."""
        raise NotImplementedError("Este método deve ser implementado pela subclasse")

    @abstractmethod
    async def delete(self, id: str) -> bool:
        """Remove um usuário do banco de dados."""
        raise NotImplementedError("Este método deve ser implementado pela subclasse")

    @abstractmethod
    async def exists_by_email(self, email: str) -> bool:
        """Verifica se existe um usuário com o email especificado."""
        raise NotImplementedError("Este método deve ser implementado pela subclasse")

    @abstractmethod
    async def find_all(self, limit: int = 100, offset: int = 0) -> List[User]:
        """Retorna uma lista paginada de usuários."""
        raise NotImplementedError("Este método deve ser implementado pela subclasse")

    @abstractmethod
    async def find_by_email(self, email: str) -> Optional[User]:
        """Busca um usuário pelo email."""
        raise NotImplementedError("Este método deve ser implementado pela subclasse")

    @abstractmethod
    async def find_by_id(self, id: str) -> Optional[User]:
        """Busca um usuário pelo ID."""
        raise NotImplementedError("Este método deve ser implementado pela subclasse")

    @abstractmethod
    async def find_by_name(self, name: str) -> List[User]:
        """
        Busca usuários da empresa logada que contenham o nome especificado
        (primeiro nome ou sobrenome).
        """
        raise NotImplementedError("Este método deve ser implementado pela subclasse")

    @abstractmethod
    async def find_by_profile(self, profile: str) -> List[User]:
        """Busca usuários por perfil."""
        raise NotImplementedError("Este método deve ser implementado pela subclasse")

    @abstractmethod
    async def save(self, user: User) -> User:
        """Salva ou atualiza um usuário no banco de dados."""
        raise NotImplementedError("Este método deve ser implementado pela subclasse")

    @abstractmethod
    async def update_profile(self, id: str, new_profile: str) -> Optional[User]:
        """Atualiza o perfil de um usuário."""
        raise NotImplementedError("Este método deve ser implementado pela subclasse")

    @abstractmethod
    async def update_photo(self, id: str, new_photo: str) -> Optional[User]:
        """Atualiza a foto de um usuário."""
        raise NotImplementedError("Este método deve ser implementado pela subclasse")
