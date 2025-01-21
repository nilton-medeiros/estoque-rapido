# db/interfaces/user_repository.py
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
    @abstractmethod
    async def count(self) -> int:
        """
        Retorna o número total de usuários da empresa logada.

        Returns:
            int: Número total de usuários

        Raises:
            Exception: Em caso de erro na operação de banco de dados
        """
        raise NotImplementedError

    @abstractmethod
    async def delete(self, id: str) -> bool:
        """
        Remove um usuário do banco de dados.

        Args:
            id (str): ID do usuário a ser removido

        Returns:
            bool: True se o usuário foi removido, False se não existia

        Raises:
            Exception: Em caso de erro na operação de banco de dados
        """
        raise NotImplementedError

    @abstractmethod
    async def exists_by_email(self, email: str) -> bool:
        """
        Verifica se existe um usuário com o email especificado.

        Args:
            email (str): Email a ser verificado

        Returns:
            bool: True se existe um usuário com o email, False caso contrário

        Raises:
            Exception: Em caso de erro na operação de banco de dados
        """
        raise NotImplementedError

    @abstractmethod
    async def find_all(self, limit: int = 100, offset: int = 0) -> List[User]:
        """
        Retorna uma lista paginada de usuários.

        Args:
            limit (int): Número máximo de registros a retornar
            offset (int): Número de registros a pular

        Returns:
            List[User]: Lista de usuários encontrados

        Raises:
            Exception: Em caso de erro na operação de banco de dados
        """
        raise NotImplementedError

    @abstractmethod
    async def find_by_email(self, email: str) -> Optional[User]:
        """
        Busca um usuário pelo email.

        Args:
            email (str): Email do usuário

        Returns:
            Optional[User]: Usuário encontrado ou None se não existir

        Raises:
            Exception: Em caso de erro na operação de banco de dados
        """
        raise NotImplementedError

    @abstractmethod
    async def find_by_id(self, id: str) -> Optional[User]:
        """
        Busca um usuário pelo ID.

        Args:
            id (str): ID do usuário

        Returns:
            Optional[User]: Usuário encontrado ou None se não existir

        Raises:
            Exception: Em caso de erro na operação de banco de dados
        """
        raise NotImplementedError

    @abstractmethod
    async def find_by_name(self, name: str) -> List[User]:
        """
        Busca usuários da empresa logada que contenham o nome especificado
        (primeiro nome ou sobrenome).

        Args:
            name (str): Nome ou parte do nome a ser buscado

        Returns:
            List[User]: Lista de usuários que correspondem à busca

        Raises:
            Exception: Em caso de erro na operação de banco de dados
        """
        raise NotImplementedError

    @abstractmethod
    async def find_by_profile(self, profile: str) -> List[User]:
        """
        Busca usuários por perfil.

        Args:
            profile (str): Perfil a ser buscado

        Returns:
            List[User]: Lista de usuários com o perfil especificado

        Raises:
            Exception: Em caso de erro na operação de banco de dados
        """
        raise NotImplementedError

    @abstractmethod
    async def save(self, user: User) -> User:
        """
        Salva ou atualiza um usuário no banco de dados.

        Args:
            user (User): Objeto usuário a ser salvo

        Returns:
            User: Objeto usuário com ID atualizado (em caso de inserção)

        Raises:
            Exception: Em caso de erro na operação de banco de dados
        """
        raise NotImplementedError

    @abstractmethod
    async def update_profile(self, id: str, new_profile: str) -> Optional[User]:
        """
        Atualiza o perfil de um usuário.

        Args:
            id (str): ID do usuário
            new_profile (str): Novo perfil a ser atribuído

        Returns:
            Optional[User]: Usuário atualizado ou None se não existir

        Raises:
            Exception: Em caso de erro na operação de banco de dados
            ValueError: Se o novo perfil não for válido
        """
        raise NotImplementedError
