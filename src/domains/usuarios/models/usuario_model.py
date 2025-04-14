from typing import Dict, List, Optional
from dataclasses import dataclass, field

from src.domains.shared import NomePessoa, PhoneNumber
from src.domains.shared.password import Password


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
        id (Optional[str]): ID opcional do usuário.
        empresa_id (Optional[str]): ID da última empresa logada.
        empresas (Optional[List[str]]): Lista de IDs de empresas associadas ao usuário.
        photo_url (Optional[str]): URL da foto de perfil do usuário.
        user_colors (Optional[dict]): Cor preferencial do usuário.


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
    id: Optional[str] = field(default=None)
    empresa_id: Optional[str] = field(default=None)
    empresas: Optional[List[str]] = field(default_factory=list)
    photo_url: Optional[str] = field(default=None)
    user_colors: Optional[Dict] = field(default_factory=dict)

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
            raise ValueError("O campo 'email' é obrigatório e deve conter um endereço de e-mail válido.")

        # Validação do campo 'phone_number'
        if not self.phone_number:
            raise ValueError("O campo 'phone_number' é obrigatório.")

        # Validação do campo 'profile'
        if self.profile not in self.ALLOWED_PROFILES:
            raise ValueError(
                f"O perfil '{self.profile}' não é permitido. Perfis permitidos: {', '.join(self.ALLOWED_PROFILES)}.")

        # Verificação e atribuição de empresas
        if self.empresas is None:
            self.empresas = []

        self.photo_url = self.photo_url.strip() if self.photo_url else None

        if not isinstance(self.user_colors, dict) or not all(key in self.user_colors for key in ['primary', 'primary_container']):
            self.user_colors = {'primary': 'blue',
                               'primary_container': 'blue_200'}

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "password": self.password,
            "phone_number": self.phone_number,
            "profile": self.profile,
            "empresa_id": self.empresa_id,
            "empresas": self.empresas,
            "photo_url": self.photo_url,
            "user_colors": self.user_colors,
            "is_admin": self.is_admin(),
        }

    def is_admin(self):
        return self.profile == 'admin'
