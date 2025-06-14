from typing import Optional

from src.domains.shared.nome_pessoa import NomePessoa
from src.domains.shared.password import Password
from src.domains.usuarios.models.usuario_model import Usuario
from src.domains.usuarios.models.usuario_subclass import UsuarioStatus
from src.domains.usuarios.repositories.contracts.usuarios_repository import UsuariosRepository
from src.shared.utils import get_uuid


class UsuariosServices:
    '''
    Serviço de gerenciamento de usuários.

    Parâmetros:
        repository: (UsuariosRepository)

    Proriedades:
        self.repository: (repository) Repositório recebido pelo parâmetro

    Métodos:
        create: Cria novo usuário no banco usando repositório
            Parâmetros:
                usuario: (Usuario)
            Retorna: (Usuario) Novo usuário criado

        update: Atualiza usuário no banco usando repositório
            Parâmetros:
                    usuario: (Usuario)
                Retorna: (Usuario) Usuário atualizado
    '''

    def __init__(self, repository: UsuariosRepository):
        self.repository = repository

    def authentication(self, email: str, password: str):
        # Simplesmente delega para o repositório e deixa as exceções se propagarem
        # Adicione lógica de negócios aqui, se necessário
        return self.repository.authentication(email, password)

    def create(self, usuario: Usuario) -> str:
        """
        Envia dados do Usuário para o Repositório do database instânciado (repository) em usuarios_controller.

        :param usuario: Instância do Usuário a salvar
        :return: ID do documento do Usuário salvo
        """
        # Verifica se já existe um usuário com este email
        if not usuario.email:
            raise ValueError("Email é necessário para criar usuário")
        if not usuario.password:
            raise ValueError("Password é necessário para criar usuário")

        existing_usuario = self.repository.exists_by_email(usuario.email)
        print(f"Debug  ->  {existing_usuario}")
        if existing_usuario:
            raise ValueError("Já existe um usuário com este email")

        # Gera por padrão um uuid raw (sem os hífens) com prefixo 'usu_'
        usuario.id = 'usu_' + get_uuid()

        # Envia para o repositório selecionado em usuarios_controllrer salvar
        return self.repository.save(usuario)

    def update(self, usuario: Usuario) -> str:
        if usuario.id is None:
            raise ValueError("ID do usuário é necessário para atualização")
        return self.repository.save(usuario)

    def find_by_id(self, usuario_id: str) -> Optional[Usuario]:
        """
        Encontra um usuário pelo usuario_id usando o repositório.

        Parâmetros:
            usuario_id (str): ID do usuário a ser encontrado

        Retorna:
            Optional[Usuario]: Usuário encontrado ou None se não existir
        """
        return self.repository.find_by_id(usuario_id)

    def find_by_email(self, email: str) -> Optional[Usuario]:
        """
        Encontra um usuário pelo email usando o repositório.

        Parâmetros:
            email (str): Email do usuário a ser encontrado

        Retorna:
            Optional[Usuario]: Usuário encontrado ou None se não existir
        """
        return self.repository.find_by_email(email)

    def get_all(self, empresa_id: str, status_deleted: bool = False) -> tuple[list[Usuario], int]:
        """
        Encontra todos os usuários pelo ID da empresa loagado usando o repositório.

        Parâmetros:
            empresa_id (str): ID da empresa a ser encontrado
            status_deleted (bool): True para usuários ativos e inativos, False para somente usuários deletados

        Retorna:
            tuple[list[Usuario], int]: Lista de Usuario encontrado ou [] se não existir e quantidade de usuários deletados
        """
        return self.repository.find_all(empresa_id, status_deleted)

    def update_photo(self, usuario_id: str, photo_url: str) -> Usuario | None:
        """
        Atualiza a foto do usuário para o campo photo_url usando o repositório.

        Parâmetros:
            usuario_id (str): ID do usuário a ser alterado
            photo_url (str): Caminho e nome do arquivo (url) a ser atualizado

        Retorna:
            Optional[Usuario]: Usuário encontrado ou None se não existir
        """
        return self.repository.update_photo(usuario_id, photo_url)

    def update_colors(self, usuario_id: str, colors: dict[str, str]) -> bool:
        """
        Atualiza a cor favorita do usuário para o campo  usando o repositório.

        Parâmetros:
            usuario_id (str): ID do usuário a ser alterado
            colors (str): Cor favorita do usuário a ser atualizado

        Retorna:
            bool: True se a atualização for bem-sucedida, False caso contrário
        """
        return self.repository.update_colors(usuario_id, colors)

    def update_empresas(self, usuario_id: str, empresas: set[str], empresa_id: str|None = None) -> bool:
        """
        Atualiza a empresa selecionada e a lista de empresas do usuário para o campo  usando o repositório.

        Parâmetros:
            usuario_id (str): ID do usuário a ser alterado
            empresa_id (str): Empresa selecionada (ativa) do usuário a ser atualizado
            empresas (list): Lista de Empresas  do usuário a ser atualizado

        Retorna:
            bool: True se a atualização for bem-sucedida, False caso contrário
        """
        return self.repository.update_empresas(usuario_id=usuario_id, empresas=empresas, empresa_id=empresa_id)

    def delete(self, usuario_id: str) -> bool:
        """Deleta um usuário pelo usuario_id usando o repositório."""
        return self.repository.delete(usuario_id)

    def update_status(self, usuario: Usuario, logged_user: dict, status: UsuarioStatus) -> bool:
        """Atualiza o status de uma usuário existente"""
        user_name: NomePessoa = logged_user["name"]
        usuario.status = status

        match status:
            case UsuarioStatus.ACTIVE:
                usuario.activated_at = None # Remove o datetime, será atribuido pelo SDK do banco TIMESTAMP
                usuario.activated_by_id = logged_user["id"]
                usuario.activated_by_name = user_name.nome_completo  # Desnormalização p/ otimização de índices no db
            case UsuarioStatus.INACTIVE:
                usuario.inactivated_at = None # Remove o datetime, será atribuido pelo SDK do banco TIMESTAMP
                usuario.inactivated_by_id = logged_user["id"]
                usuario.inactivated_by_name = user_name.nome_completo  # Desnormalização p/ otimização de índices no db
            case UsuarioStatus.DELETED:
                usuario.deleted_at = None # Remove o datetime, será atribuido pelo SDK do banco TIMESTAMP
                usuario.deleted_by_id = logged_user["id"]
                usuario.deleted_by_name = user_name.nome_completo  # Desnormalização p/ otimização de índices no db

        id = self.repository.save(usuario)
        return id is not None

    def change_password(self, usuario_id: str, new_password: str) -> bool:
        """Atualiza a senha de uma usuário existente"""
        pwd_encrypted = Password(new_password)
        if pwd_encrypted.error:
            raise ValueError(pwd_encrypted.error_message)
        return self.repository.change_password(usuario_id, pwd_encrypted.value)
