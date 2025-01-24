import re
from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional
from enum import Enum

from models.cnpj import CNPJ
from models.phone_number import PhoneNumber
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
    complement: Optional[str] = None
    neighborhood: Optional[str] = None
    city: str
    state: str
    postal_code: str


@dataclass
class FiscalData:
    """
    Fiscal and system configuration (tax data)
    tax_regime:
        1 – Simples Nacional;
        2 – Simples Nacional – excesso de sublimite de receita bruta;
        3 - Regime Normal;
        4 - Simples Nacional - Microempreendedor individual (MEI).
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
    name: str   # nome fantasia
    corporate_name: str # Razão Social
    cnpj: CNPJ
    state_registration: str  # Inscrição Estadual
    legal_nature: str  # Natureza jurídica
    id: Optional[str] = field(default=None)
    municipal_registration: Optional[str] = None  # Inscrição Municipal
    founding_date: Optional[date] = None  # Data da fundação
    contact: Optional[ContactInfo] = None
    address: Optional[Address] = None
    size: Optional[CompanySize] = None  # Porte da empresa
    fiscal: Optional[FiscalData] = None

    # Optional metadata
    description: Optional[str] = None
    logo_path: Optional[str] = None

    # Payment gateway | Troque aqui o gateway de pagamento conforme contratado: Default Asaas
    payment_gateway: Optional[AsaasPaymentGateway] = None

    # Lista de ambientes permitidos em NFCe
    ALLOWED_ENVIRONMENT = {"homologacao", "producao"}

    def __post_init__(self):
        # Validações adicionais podem ser adicionadas aqui

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
        """Check if NFC-e emission is configured"""
        return self.nfce_series is not None

    def get_complete_address(self) -> str:
        """Return formatted complete address"""
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

    def get_nfce_data(self):
        # Retorna um dicionário com os dados necessários para emissão da NFC-e
        return {
            "ambiente": self.nfce_environment,
            "certificado": self.nfce_certificate,
            "certificado_date": self.nfce_certificate_date,
            "certificato_password": self.nfce_certificate_password,
            "crt": self.tax_regime,
            "series": self.nfce_series,
            "sefaz_id_csc": self.nfce_sefaz_id_csc,
            "sefaz_csc": self.nfce_sefaz_csc
        }
