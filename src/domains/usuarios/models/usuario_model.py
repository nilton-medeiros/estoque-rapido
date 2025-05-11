from typing import Set
from dataclasses import dataclass, field

from src.domains.shared import NomePessoa, PhoneNumber
from src.domains.shared.password import Password
from src.shared import get_app_colors


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
        profile (str): Perfil do usuário.
        id (str | None): ID opcional do usuário.
        empresa_id (str | None): ID da última empresa logada.
        empresas (Set[str]): Conjunto de IDs de empresas associadas ao usuário.
        photo_url (str | None): URL da foto de perfil do usuário.
        user_colors (dict | None): Cor preferencial do usuário.


    Example:
        Exemplo de como instanciar e usar a classe:
        >>> from src.domain.models.nome_pessoa import NomePessoa
        >>> from src.domain.models.phone_number import PhoneNumber
        >>> name = NomePessoa("João", "Silva")
        >>> phone = PhoneNumber("+5511999999999")
        >>> user = Usuario(email="joao.silva@example.com", name=name, phone_number=phone, profile="admin")
        >>> print(user)
    """

    email: str
    password: Password
    name: NomePessoa
    phone_number: PhoneNumber
    profile: str
    id: str | None = field(default=None)
    empresa_id: str | None = field(default=None)
    empresas: Set[str] = field(default_factory=set)
    photo_url: str | None = field(default=None)
    user_colors: dict | None = field(default_factory=dict)

    # Lista de perfis permitidos
    ALLOWED_PROFILES = {"admin", "cobrança",
                        "contabil", "financeiro", "pagamento", "vendas"}

    def __post_init__(self):
        """
        Método chamado automaticamente após a inicialização da instância da classe.
        Realiza validações adicionais dos campos 'name', 'email' e 'profile'.
        """
        # Validação do campo 'name'
        if not self.name.first_name:
            raise ValueError("O campo 'name' é obrigatório.")

        # Validação do campo 'email'
        self.email = self.email.lower().strip() if self.email else None
        if not self.email or "@" not in self.email:
            raise ValueError(
                "O campo 'email' é obrigatório e deve conter um endereço de e-mail válido.")

        # Validação do campo 'phone_number'
        if not self.phone_number:
            raise ValueError("O campo 'phone_number' é obrigatório.")

        # Validação do campo 'profile'
        if self.profile not in self.ALLOWED_PROFILES:
            raise ValueError(
                f"O perfil '{self.profile}' não é permitido. Perfis permitidos: {', '.join(self.ALLOWED_PROFILES)}.")

        # Garante que empresas seja sempre um conjunto
        if self.empresas is None:
            self.empresas = set()
        elif isinstance(self.empresas, list):
            self.empresas = set(self.empresas)

        self.photo_url = self.photo_url.strip() if self.photo_url else None

        if not isinstance(self.user_colors, dict) or not all(key in self.user_colors for key in ['base_color','primary', 'container', 'accent', 'appbar']):
            self.user_colors = get_app_colors('blue')

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
            "phone_number": self.phone_number,
            "profile": self.profile,
            "empresa_id": self.empresa_id,
            # Converte conjunto para lista ao salvar
            "empresas": self.empresas,
            "photo_url": self.photo_url,
            "user_colors": self.user_colors,
            "is_admin": self.is_admin(),
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
            "name": {
                "first_name": self.name.first_name,
                "last_name": self.name.last_name
            },
            "email": self.email,
            "password": self.password.value,
            "phone_number": self.phone_number.get_e164(),
            "profile": self.profile,
            "empresa_id": self.empresa_id,
            "empresas": list(self.empresas),  # Converte conjunto empresas para lista ao salvar
            "photo_url": self.photo_url,
            "user_colors": self.user_colors,
            "is_admin": self.is_admin(),
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
        # Converte as empresas de lista para conjunto
        empresas_set = set(data.get("empresas", []))

        # Assumindo que NomePessoa, PhoneNumber e Password têm métodos from_dict
        return cls(
            id=data.get("id"),
            email=data.get("email", ""),
            name=NomePessoa.from_dict(data.get("name")) if isinstance(
                data.get("name"), dict) else data.get("name"),
            password=Password.from_dict(data.get("password")) if isinstance(
                data.get("password"), bytes) else data.get("password"),
            phone_number=PhoneNumber.from_dict(data.get("phone_number")) if isinstance(
                data.get("phone_number"), str) else data.get("phone_number"),
            profile=data.get("profile", ""),
            empresa_id=data.get("empresa_id"),
            empresas=empresas_set,
            photo_url=data.get("photo_url"),
            user_colors=data.get("user_colors", {})
        )

    def is_admin(self):
        return self.profile == 'admin'
