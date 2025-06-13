from abc import ABC, abstractmethod
from typing import Optional
from src.domains.usuarios.models.usuario_model import Usuario


'''
Sobre o porque da interface UsuariosRepository (Classe abstrata)
Esta interface define os métodos necessários para manipular e buscar usuários em um banco de dados.
Qualquer classe que herdar de UsuariosRepository DEVE ter os métodos de UsuariosRepository que recebe um Usuario e retorna um Usuario
1. Garante que todas as implementações (Firebase, MySQL, MariaDB, PostgreSQL) tenham os mesmos métodos
2. Permite trocar implementações (database) facilmente (porque todas seguem o mesmo contrato)
3. Ajuda na organização do código
O UsuariosRepository em si nunca é usado diretamente - ele só serve como modelo para outras classes.
Por isso não precisamos implementar os métodos nele.
'''


class UsuariosRepository(ABC):
    """Classe base abstrata que define o contrato para operações de repositório de usuários."""

    @abstractmethod
    def authentication(self, email, password) -> Usuario | None:
        """Retorna o usuário logado."""
        raise NotImplementedError("Este método deve ser implementado pela subclasse")

    @abstractmethod
    def save(self, usuario: Usuario) -> str:
        """Salva ou atualiza um usuário no banco de dados."""
        raise NotImplementedError("Este método deve ser implementado pela subclasse")

    @abstractmethod
    def count(self, empresa_id: str) -> int:
        """Retorna o número total de usuários da empresa logada."""
        raise NotImplementedError("Este método deve ser implementado pela subclasse")

    @abstractmethod
    def find_by_id(self, id: str) -> Usuario | None:
        """Busca um usuário pelo ID."""
        raise NotImplementedError("Este método deve ser implementado pela subclasse")

    @abstractmethod
    def exists_by_email(self, email: str) -> bool:
        """Verifica se existe um usuário com o email especificado."""
        raise NotImplementedError("Este método deve ser implementado pela subclasse")

    @abstractmethod
    def find_all(self, empresa_id: str, status_deleted: bool = False) -> tuple[list[Usuario], int]:
        """Retorna uma lista paginada de usuários."""
        raise NotImplementedError("Este método deve ser implementado pela subclasse")

    @abstractmethod
    def find_by_email(self, email: str) -> Usuario | None:
        """Busca um usuário pelo email."""
        raise NotImplementedError("Este método deve ser implementado pela subclasse")

    @abstractmethod
    def find_by_name(self, empresa_id, name: str) -> list[Usuario]:
        """
        Busca usuários da empresa logada que contenham o nome especificado
        (primeiro nome ou sobrenome).
        """
        raise NotImplementedError("Este método deve ser implementado pela subclasse")

    @abstractmethod
    def find_by_profile(self, empresa_id: str, profile: str) -> list[Usuario]:
        """Busca usuários por perfil."""
        raise NotImplementedError("Este método deve ser implementado pela subclasse")

    @abstractmethod
    def delete(self, usuario_id: str) -> bool:
        """Remove um usuário do banco de dados."""
        raise NotImplementedError("Este método deve ser implementado pela subclasse")

    @abstractmethod
    def update_profile(self, id: str, new_profile: str) -> Usuario | None:
        """Atualiza o perfil de um usuário."""
        raise NotImplementedError("Este método deve ser implementado pela subclasse")

    @abstractmethod
    def update_photo(self, id: str, new_photo: str) -> Usuario | None:
        """Atualiza a foto de um usuário."""
        raise NotImplementedError("Este método deve ser implementado pela subclasse")

    @abstractmethod
    def update_colors(self, id: str, new_colors: dict[str, str]) -> bool:
        """Atualiza a cor preferida do um usuário."""
        raise NotImplementedError("Este método deve ser implementado pela subclasse")

    @abstractmethod
    def update_empresas(self, usuario_id: str, empresas: set, empresa_id: str|None = None) -> bool:
        """Atualiza empresas do um usuário."""
        raise NotImplementedError("Este método deve ser implementado pela subclasse")
