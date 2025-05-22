from typing import Optional

from src.domains.usuarios.models.usuario_model import Usuario
from src.domains.usuarios.repositories.contracts.usuarios_repository import UsuariosRepository
from src.shared import get_uuid


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

    def find_all(self, empresa_id: str) -> list[Usuario]:
        """
        Encontra todos os usuários pelo ID da empresa usando o repositório.

        Parâmetros:
            empresa_id (str): ID da empresa a ser encontrado

        Retorna:
            list[Usuario]: Lista de Usuario encontrado ou [] se não existir
        """
        return self.repository.find_all(empresa_id)

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
