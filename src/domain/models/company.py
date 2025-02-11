from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional

from src.domain.models.company_size import CompanySize
from src.domain.models.cnpj import CNPJ
from src.domain.models.phone_number import PhoneNumber
from src.services.payment_gateways.asaas_payment_gateway import AsaasPaymentGateway


@dataclass
class Address:
    street: str
    number: str
    city: str
    state: str
    postal_code: str
    complement: Optional[str] = None
    neighborhood: Optional[str] = None


@dataclass
class FiscalData:
    """
    Dados fiscais e de configuração do sistema.

    Código Regime tributário (CRT):
        1 – Simples Nacional;
        2 – Simples Nacional – Excesso de sublimite de receita bruta;
        3 - Regime Normal;
        4 - Simples Nacional - Microempreendedor Individual (MEI).
    """
    crt: Optional[int] = 3   # CRT - Código de Regime Tributário
    nfce_series: Optional[int] = None
    nfce_number: Optional[int] = None
    nfce_environment: Optional[str] = field(default='homologacao')  # Valores aceitos: homologacao, producao
    nfce_certificate: str = None  # Binário do certificado digital (.pfx ou .p12) codificado em base64
    nfce_certificate_password: str = None
    nfce_certificate_date: Optional[datetime] = None    # Data e hora de validade do certificado
    nfce_sefaz_id_csc: Optional[int] = None  # Número de identificação do CSC - Código de Segurança do Contribuínte.
    nfce_sefaz_csc: Optional[str] = None   # Código do CSC.


@dataclass
class Company:
    """
    Representa os dados de uma empresa.

    Esta classe encapsula as informações e responsabilidades principais de uma empresa, incluindo
    dados fiscais, de contato, endereço, porte e configurações específicas.

    Attributes:
        corporate_name (str): Razão Social da empresa.
        email: str: E-mail da empresa.
        store_name (Optional[str]): Nome da loja.
        id (Optional[str]): ID opcional da empresa.
        name (Optional[str]): Nome fantasia da empresa.
        cnpj (CNPJ): CNPJ da empresa.
        cpf (CPF): CPF do emitente da NFCe.
        ie (str): Inscrição Estadual da empresa.
        im (Optional[str]): Inscrição Municipal da empresa.
        phone (Optional[PhoneNumber]): Telefone da empresa.
        address (Optional[Address]): Endereço da empresa.
        size (Optional[CompanySize]): Porte da empresa.
        fiscal (Optional[FiscalData]): Dados fiscais da empresa.
        logo_path (Optional[str]): Caminho para o logo da empresa.
        payment_gateway (Optional[AsaasPaymentGateway]): Gateway de pagamento da empresa.
        ALLOWED_ENVIRONMENT (set): Ambientes permitidos para NFCe.

    Example:
        Exemplo de como instanciar e usar a classe:
        >>> from src.domain.models.cnpj import CNPJ
        >>> cnpj = CNPJ("00.000.000/0000-00")
        >>> company = Company(name="Minha Empresa", corporate_name="Minha Empresa Ltda", cnpj=cnpj,
        ...                   ie="123456789")
        >>> print(company)
    """
    corporate_name: str  # Razão Social ou Nome do Emitente qdo CPF
    email: str  # E-mail
    store_name: Optional[str] = 'Matriz'
    id: Optional[str] = field(default=None)
    name: Optional[str]  # Nome fantasia
    cnpj: Optional[CNPJ] = None  # CNPJ do emitente da NFCe
    cpf: Optional[str] = None  # CPF do responsável
    ie: Optional[str] = None  # Inscrição Estadual
    im: Optional[str] = None  # Inscrição Municipal
    phone: Optional[PhoneNumber] = None  # Telefone
    address: Optional[Address] = None
    size: Optional[CompanySize] = None  # Porte da empresa
    fiscal: Optional[FiscalData] = None

    # Metadados opcionais
    logo_path: Optional[str] = None

    # Gateway de pagamento | Troque aqui o gateway de pagamento conforme contratado: Default Asaas
    payment_gateway: Optional[AsaasPaymentGateway] = None

    # Lista de ambientes permitidos em NFCe
    ALLOWED_ENVIRONMENT = {"homologacao", "producao"}

    def __post_init__(self):
        """
        Método chamado automaticamente após a inicialização da instância da classe.

        Realiza validações adicionais e formatações necessárias.
        """
        self.name = self.name.upper()
        self.corporate_name = self.corporate_name.upper()

        # Validação do campo 'nfce_environment'
        if self.nfce_environment not in self.ALLOWED_ENVIRONMENT:
            raise ValueError(
                f"O ambiente '{self.nfce_environment}' não é permitido. Ambientes permitidos: {', '.join(self.ALLOWED_ENVIRONMENT)}.")

        if self.crt < 1 or self.crt > 4:
            raise ValueError(
                f"Código de Regime Tributário (CRT) '{self.crt}' não permitido. CRT permitidos: 1, 2, 3 ou 4")

    def is_nfce_enabled(self) -> bool:
        """
        Verifica se a emissão de NFC-e está configurada.

        Returns:
            bool: True se a emissão de NFC-e estiver configurada, False caso contrário.
        """
        return self.nfce_series is not None

    def get_complete_address(self) -> str:
        """
        Retorna o endereço completo formatado.

        Returns:
            str: Endereço completo formatado ou mensagem indicando que o endereço não está configurado.
        """
        if not self.address:
            return "Endereço não configurado"

        components = [
            f"{self.address.street}, {self.address.number}",
            self.address.complement or "",
            f"{self.address.neighborhood}" if self.address.neighborhood else "",
            f"{self.address.city} - {self.address.state}",
            f"CEP: {self.address.postal_code}"
        ]
        return ", ".join(filter(bool, components))

    def get_nfce_data(self) -> dict:
        """
        Retorna um dicionário com os dados necessários para emissão da NFC-e.

        Returns:
            dict: Dicionário com dados da NFC-e.
        """
        return {
            "ambiente": self.nfce_environment,
            "certificado": self.nfce_certificate,
            "certificado_date": self.nfce_certificate_date,
            "certificado_password": self.nfce_certificate_password,
            "crt": self.crt,
            "series": self.nfce_series,
            "sefaz_id_csc": self.nfce_sefaz_id_csc,
            "sefaz_csc": self.nfce_sefaz_csc
        }
