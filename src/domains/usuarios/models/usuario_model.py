from typing import List, Optional
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
        user_color (Optional[str]): Cor preferencial do usuário.


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
    user_color: Optional[str] = field(default='blue')

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

        # Validação do campo 'phone_number'
        if not self.phone_number:
            raise ValueError("O campo 'phone_number' é obrigatório.")

        # Validação do campo 'email'
        self.email = self.email.strip()

        if not self.email or "@" not in self.email:
            raise ValueError("O campo 'email' deve ser válido.")

        # Validação do campo 'profile'
        if self.profile not in self.ALLOWED_PROFILES:
            raise ValueError(
                f"O perfil '{self.profile}' não é permitido. Perfis permitidos: {', '.join(self.ALLOWED_PROFILES)}.")

        # Verificação e atribuição de empresas
        if self.empresas is None:
            self.empresas = []

        if self.photo_url == '':
            self.photo_url = None

        if self.user_color == '':
            self.user_color = 'blue'

    def to_dict(self):
        user_dict = {
            "id": self.id,
            "password": self.password,
            "name": self.name,
            "email": self.email,
            "phone_number": self.phone_number,
            "profile": self.profile,
            "empresa_id": self.empresa_id,
            "empresas": self.empresas,
            "photo_url": self.photo_url,
            "user_color": self.user_color,
        }
        return user_dict
