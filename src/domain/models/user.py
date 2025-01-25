from typing import List, Optional
from dataclasses import dataclass, field

from src.domain.models.nome_pessoa import NomePessoa
from src.domain.models.phone_number import PhoneNumber


@dataclass
class User:
    """
    Representa os dados de um usuário.

    Esta classe encapsula as informações e responsabilidades principais de um usuário,
    incluindo dados de contato, perfil e associações com empresas.

    Attributes:
        email (str): Email do usuário.
        name (NomePessoa): Nome do usuário.
        phone_number (PhoneNumber): Número de telefone do usuário.
        profile (str): Perfil do usuário.
        id (Optional[str]): ID opcional do usuário.
        companies (Optional[List[str]]): Lista de IDs de empresas associadas ao usuário.

    Example:
        Exemplo de como instanciar e usar a classe:
        >>> from src.domain.models.nome_pessoa import NomePessoa
        >>> from src.domain.models.phone_number import PhoneNumber
        >>> name = NomePessoa("João", "Silva")
        >>> phone = PhoneNumber("+5511999999999")
        >>> user = User(email="joao.silva@example.com", name=name, phone_number=phone, profile="admin")
        >>> print(user)
    """

    email: str
    name: NomePessoa
    phone_number: PhoneNumber
    profile: str
    id: Optional[str] = field(default=None)
    companies: Optional[List[str]] = field(default_factory=list)

    # Lista de perfis permitidos
    ALLOWED_PROFILES = {"admin", "cobrança", "contabil", "financeiro", "pagamento", "vendas"}

    def __post_init__(self):
        """
        Método chamado automaticamente após a inicialização da instância da classe.

        Realiza validações adicionais dos campos 'name', 'email' e 'profile'.
        """
        # Validação do campo 'name'
        if not self.name.first_name:
            raise ValueError("O campo 'name' é obrigatório.")

        # Validação do campo 'email'
        self.email = self.email.strip()

        if not self.email or "@" not in self.email:
            raise ValueError("O campo 'email' deve ser válido.")

        # Validação do campo 'profile'
        if self.profile not in self.ALLOWED_PROFILES:
            raise ValueError(
                f"O perfil '{self.profile}' não é permitido. Perfis permitidos: {', '.join(self.ALLOWED_PROFILES)}.")

        # Verificação e atribuição de companies
        if self.companies is None:
            self.companies = []
