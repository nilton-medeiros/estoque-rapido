from datetime import datetime, UTC
from typing import Set
from dataclasses import dataclass, field

from src.domains.shared import NomePessoa, PhoneNumber
from src.domains.shared.models.password import Password
from src.domains.usuarios.models.usuarios_subclass import UserProfile
from src.domains.shared.models.registration_status import RegistrationStatus
from src.shared.config import get_app_colors


@dataclass
class Usuario:
    """
    Representa os dados de um usuário.

    Esta classe encapsula as informações e responsabilidades principais de um usuário,
    incluindo dados de contato, perfil e associações com empresas.

    Attributes:
        email (str): Email do usuário.
        password (Password): Objeto Senha.
        name (NomePessoa): Nome do usuário.
        phone_number (PhoneNumber): Número de telefone do usuário.
        id (str | None): ID opcional do usuário.
        empresa_id (str | None): ID da última empresa logada.
        temp_password (bool | None = False): Se a senha é temporária (para novos usuários).
        empresas (Set[str]): Conjunto de IDs de empresas associadas ao usuário.
        photo_url (str | None): URL da foto de perfil do usuário.
        user_colors (dict | None): Cor preferencial do usuário.
        profile (UserProfile): Perfil do usuário.
        status (RegistrationStatus = RegistrationStatus.ACTIVE): Status do usuário.
        # --- Campos de Auditoria
        created_at (datetime | None): Data e hora de criação.
        created_by_id (str | None): ID do usuário que criou.
        created_by_name (str | None): Nome do usuário que criou.
        updated_at (datetime | None): Data e hora da última atualização.
        updated_by_id (str | None): ID do usuário que atualizou.
        updated_by_name (str | None): Nome do usuário que atualizou.
        activated_at (datetime | None): Data e hora de ativação.
        activated_by_id (str | None): ID do usuário que ativou.
        activated_by_name (str | None): Nome do usuário que ativou.
        inactivated_at (datetime | None): Data e hora de inativação.
        inactivated_by_id (str | None): ID do usuário que inativou.
        inactivated_by_name (str | None): Nome do usuário que inativou.
        deleted_at (datetime | None): Data e hora de exclusão.
        deleted_by_id (str | None): ID do usuário que excluiu.
        deleted_by_name (str | None): Nome do usuário que excluiu.

    Example:
        Exemplo de como instanciar e usar a classe:
        >>> from src.domain.models.nome_pessoa import NomePessoa
        >>> from src.domain.models.phone_number import PhoneNumber
        >>> name = NomePessoa("João", "Silva")
        >>> phone = PhoneNumber("+5511999999999")
        >>> user = Usuario(email="joao.silva@example.com", name=name, phone_number=phone, profile=UserProfile.ADMIN)
        >>> print(user)
    """

    email: str
    password: Password
    name: NomePessoa
    phone_number: PhoneNumber
    id: str | None = None
    empresa_id: str | None = None
    temp_password: bool | None = False
    empresas: Set[str] = field(default_factory=set)
    photo_url: str | None = None
    user_colors: dict | None = field(default_factory=dict)
    profile: UserProfile = UserProfile.UNDEFINED

    # --- Campos de Status e Auditoria
    status: RegistrationStatus = RegistrationStatus.ACTIVE
    created_at: datetime | None = field(
        default_factory=lambda: datetime.now(UTC))
    created_by_id: str | None = None
    created_by_name: str | None = None

    updated_at: datetime | None = None
    updated_by_id: str | None = None
    updated_by_name: str | None = None

    activated_at: datetime | None = None  # Se o status mudar para ACTIVE
    activated_by_id: str | None = None
    activated_by_name: str | None = None

    inactivated_at: datetime | None = None  # Se o status mudar para INACTIVE
    inactivated_by_id: str | None = None
    inactivated_by_name: str | None = None

    deleted_at: datetime | None = None  # Para soft delete
    deleted_by_id: str | None = None
    deleted_by_name: str | None = None

    def __post_init__(self):
        """
        Método chamado automaticamente após a inicialização da instância da classe.
        Realiza validações adicionais dos campos 'name', 'email' e 'profile'.
        """
        # Validação do campo 'name'
        if not self.name.first_name:
            raise ValueError("O campo 'name' é obrigatório.")

        # Validação do campo 'email'
        self.email = self.email.lower().strip()
        if not self.email or "@" not in self.email:
            raise ValueError(
                "O campo 'email' é obrigatório e deve conter um endereço de e-mail válido.")

        # Validação do campo 'phone_number'
        if not self.phone_number:
            raise ValueError("O campo 'phone_number' é obrigatório.")

        # Garante que empresas seja sempre um conjunto
        if self.empresas is None:
            self.empresas = set()
        elif isinstance(self.empresas, list):
            self.empresas = set(self.empresas)

        self.photo_url = self.photo_url.strip() if self.photo_url else None

        if not isinstance(self.user_colors, dict) or not all(key in self.user_colors for key in ['base_color', 'primary', 'container', 'accent', 'appbar']):
            self.user_colors = get_app_colors('blue')

        # Se o usuário está sendo criado como ACTIVE e não tem activated_at, define-o
        if self.status == RegistrationStatus.ACTIVE and self.created_at and not self.activated_at:
            self.activated_at = self.created_at
            self.activated_by_id = self.created_by_id
            self.activated_by_name = self.created_by_name

        if not isinstance(self.temp_password, bool):
            self.temp_password = False

    def adicionar_empresa(self, empresa_id: str) -> None:
        """
        Adiciona o ID de uma empresa ao conjunto de empresas do usuário.

        Args:
            empresa_id (str): ID da empresa a ser adicionada.
        """
        if not empresa_id:
            return

        self.empresas.add(empresa_id)

    def remover_empresa(self, empresa_id: str) -> None:
        """
        Remove o ID de uma empresa do conjunto de empresas do usuário.

        Args:
            empresa_id (str): ID da empresa a ser removida.
        """
        self.empresas.discard(
            empresa_id)  # discard não gera erro se o item não existir

    def to_dict(self) -> dict:
        """
        Converte o objeto Usuario para um dicionário.

        Returns:
            dict: Representação do usuário como dicionário.
        """
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "password": self.password,
            "temp_password": self.temp_password,
            "phone_number": self.phone_number,
            "profile": self.profile.name,
            "empresa_id": self.empresa_id,
            # Converte conjunto para lista ao salvar
            "empresas": list(self.empresas),
            "photo_url": self.photo_url,
            "user_colors": self.user_colors,
            "status": self.status,
            "created_at": self.created_at,
            "created_by_id": self.created_by_id,
            "created_by_name": self.created_by_name,
            "updated_at": self.updated_at,
            "updated_by_id": self.updated_by_id,
            "updated_by_name": self.updated_by_name,
            "activated_at": self.activated_at,
            "activated_by_id": self.activated_by_id,
            "activated_by_name": self.activated_by_name,
            "inactivated_at": self.inactivated_at,
            "inactivated_by_id": self.inactivated_by_id,
            "inactivated_by_name": self.inactivated_by_name,
            "deleted_at": self.deleted_at,
            "deleted_by_id": self.deleted_by_id,
            "deleted_by_name": self.deleted_by_name,
        }

    def to_dict_db(self) -> dict:
        """
        Converte o objeto Usuario e todos os seus atributos para um dicionário.

        Returns:
            dict: Representação do usuário como dicionário para um database.
            O ID do usuário não faz parte dos campos a serem salvos/alterados.
            O repositório do database obtem o ID do objeto Usuario.
        """

        dict_db = {
            "name": self.name.to_dict(),
            "email": self.email,
            "password": self.password.value,
            "temp_password": self.temp_password,
            "phone_number": self.phone_number.get_e164(),
            "profile": self.profile.name,
            "empresa_id": self.empresa_id,
            # Converte conjunto empresas para lista ao salvar
            "empresas": list(self.empresas),
            "photo_url": self.photo_url,
            "user_colors": self.user_colors,
            "status": self.status.name,  # Salva o nome do enum no DB
            "created_at": self.created_at if self.created_at else datetime.now(UTC),
            "created_by_id": self.created_by_id,
            "created_by_name": self.created_by_name,
            "updated_at": self.updated_at,
            "updated_by_id": self.updated_by_id,
            "updated_by_name": self.updated_by_name,
            "activated_at": self.activated_at,
            "activated_by_id": self.activated_by_id,
            "activated_by_name": self.activated_by_name,
            "inactivated_at": self.inactivated_at,
            "inactivated_by_id": self.inactivated_by_id,
            "inactivated_by_name": self.inactivated_by_name,
            "deleted_at": self.deleted_at,
            "deleted_by_id": self.deleted_by_id,
            "deleted_by_name": self.deleted_by_name,
        }

        # Remove campos desnecessários para o banco de dados
        # (por exemplo, campos que não devem ser salvos ou são None)
        dict_db_filtered = {k: v for k,
                                 v in dict_db.items() if v is not None}

        return dict_db_filtered

    @classmethod
    def from_dict(cls, data: dict) -> 'Usuario':
        """
        Cria uma instância de Usuario a partir de um dicionário.

        Args:
            data (dict): Dicionário contendo os dados do usuário.

        Returns:
            Usuario: Nova instância de Usuario.

        Note:
            Este método assume que os objetos NomePessoa, PhoneNumber e Password
            também possuem métodos from_dict para sua criação.
        """
        # Converte enums
        status_data = data.get("status", RegistrationStatus.ACTIVE)
        status = status_data # Por padrão status é do tipo RegistrationStatus

        if not isinstance(status_data, RegistrationStatus):
            if isinstance(status_data, str) and status_data in RegistrationStatus.__members__:
                status = RegistrationStatus[status_data]
            else:
                status = RegistrationStatus.ACTIVE

        profile_data = data.get("profile")
        profile = UserProfile.UNDEFINED  # Padrão

        # Converte string para Enum UserProfile
        if profile_data:
            if isinstance(profile_data, UserProfile):
                profile = profile_data
            else:
                try:
                    profile = UserProfile[profile_data]
                except KeyError:
                    # Lidar com profile inválido, talvez logar um aviso ou usar um padrão
                    profile = UserProfile.UNDEFINED

        # Converte Timestamps do Firestore para datetime
        for key in ['created_at', 'updated_at', 'activated_at', 'inactivated_at', 'deleted_at']:
            if key in data and data.get(key) and hasattr(data[key], 'to_datetime'):
                data[key] = data[key].to_datetime()

        # --- Conversão de Objetos Aninhados ---
        name_data = data.get("name")
        if isinstance(name_data, dict):
            name_obj = NomePessoa.from_dict(name_data)
        elif isinstance(name_data, NomePessoa):
            name_obj = name_data
        else:
            raise ValueError("Dados de 'name' inválidos ou ausentes para criar Usuario.")

        phone_data = data.get("phone_number")
        if isinstance(phone_data, str):
            phone_obj = PhoneNumber.from_dict(phone_data)
        elif isinstance(phone_data, PhoneNumber):
            phone_obj = phone_data
        else:
            raise ValueError("Dados de 'phone_number' inválidos ou ausentes para criar Usuario.")

        password_data = data.get("password")
        if isinstance(password_data, (str, bytes)):
            password_obj = Password.from_dict(password_data)
        elif isinstance(password_data, Password):
            password_obj = password_data
        else:
            raise ValueError("Dados de 'password' inválidos ou ausentes para criar Usuario.")

        # Remove campos já tratados para evitar passar duas vezes no construtor
        for key in ["name", "phone_number", "password", "status", "profile"]:
            data.pop(key, None)

        # Converte a lista de empresas para um conjunto (set)
        if 'empresas' in data and isinstance(data['empresas'], list):
            data['empresas'] = set(data['empresas'])

        return cls(
            name=name_obj,
            phone_number=phone_obj,
            password=password_obj,
            status=status,
            profile=profile,
            **data
        )
