import re
from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional
from enum import Enum

from src.domain.models.cnpj import CNPJ
from src.domain.models.phone_number import PhoneNumber
from src.services.payment_gateways.asaas_payment_gateway import AsaasPaymentGateway


class CompanySize(Enum):
    MICRO = "Microempresa"
    SMALL = "Pequena Empresa"
    MEDIUM = "Média Empresa"
    LARGE = "Grande Empresa"


@dataclass
class ContactInfo:
    email: str
    phone: PhoneNumber
    website: Optional[str] = None


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

    Regime tributário (tax_regime):
        1 – Simples Nacional;
        2 – Simples Nacional – Excesso de sublimite de receita bruta;
        3 - Regime Normal;
        4 - Simples Nacional - Microempreendedor Individual (MEI).
    """
    tax_regime: Optional[int] = 3
    nfce_series: Optional[str] = None
    nfce_environment: Optional[str] = field(default='homologacao')  # Valores aceitos: homologacao, producao
    nfce_certificate: str = None  # Binário do certificado digital (.pfx ou .p12) codificado em base64
    nfce_certificate_password: str = None
    nfce_certificate_date: Optional[date] = None
    nfce_sefaz_id_csc: Optional[int] = None  # Número de identificação do CSC.
    nfce_sefaz_csc: Optional[str] = None   # Código do CSC.


@dataclass
class Company:
    """
    Representa os dados de uma empresa.

    Esta classe encapsula as informações e responsabilidades principais de uma empresa, incluindo
    dados fiscais, de contato, endereço, porte e configurações específicas.

    Attributes:
        name (str): Nome fantasia da empresa.
        corporate_name (str): Razão Social da empresa.
        cnpj (CNPJ): CNPJ da empresa.
        state_registration (str): Inscrição Estadual da empresa.
        legal_nature (str): Natureza jurídica da empresa.
        id (Optional[str]): ID opcional da empresa.
        municipal_registration (Optional[str]): Inscrição Municipal da empresa.
        founding_date (Optional[date]): Data da fundação da empresa.
        contact (Optional[ContactInfo]): Informações de contato da empresa.
        address (Optional[Address]): Endereço da empresa.
        size (Optional[CompanySize]): Porte da empresa.
        fiscal (Optional[FiscalData]): Dados fiscais da empresa.
        description (Optional[str]): Descrição opcional da empresa.
        logo_path (Optional[str]): Caminho para o logo da empresa.
        payment_gateway (Optional[AsaasPaymentGateway]): Gateway de pagamento da empresa.
        ALLOWED_ENVIRONMENT (set): Ambientes permitidos para NFCe.

    Example:
        Exemplo de como instanciar e usar a classe:
        >>> from src.domain.models.cnpj import CNPJ
        >>> cnpj = CNPJ("00.000.000/0000-00")
        >>> company = Company(name="Minha Empresa", corporate_name="Minha Empresa Ltda", cnpj=cnpj,
        ...                   state_registration="123456789", legal_nature="Sociedade Limitada")
        >>> print(company)
    """
    name: str  # Nome fantasia
    corporate_name: str  # Razão Social
    cnpj: CNPJ
    state_registration: str  # Inscrição Estadual
    legal_nature: str  # Natureza jurídica
    id: Optional[str] = field(default=None)
    store_name: Optional[str] = None
    municipal_registration: Optional[str] = None  # Inscrição Municipal
    founding_date: Optional[date] = None  # Data da fundação
    contact: Optional[ContactInfo] = None
    address: Optional[Address] = None
    size: Optional[CompanySize] = None  # Porte da empresa
    fiscal: Optional[FiscalData] = None

    # Metadados opcionais
    description: Optional[str] = None
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

        if self.tax_regime < 1 or self.tax_regime > 4:
            raise ValueError(
                f"Código de Regime Tributário (CRT) '{self.tax_regime}' não permitido. CRT permitidos: 1, 2, 3 ou 4")

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
            "crt": self.tax_regime,
            "series": self.nfce_series,
            "sefaz_id_csc": self.nfce_sefaz_id_csc,
            "sefaz_csc": self.nfce_sefaz_csc
        }
