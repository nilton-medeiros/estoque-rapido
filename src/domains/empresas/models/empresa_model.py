from dataclasses import dataclass, field
from typing import Optional, Dict

"""
ToDo: Refatorar, aqui não deveria invocar diretamente a AsaasPaymentGateway
e sim um handle de serviço de pagamento que invocaria os serviços de Asaas
from src.services.gateways.asaas_payment_gateway import AsaasPaymentGateway
"""
from src.services.gateways.asaas_payment_gateway import AsaasPaymentGateway
from src.domains.shared.phone_number import PhoneNumber
from src.domains.empresas.models.empresa_subclass import Environment, EmpresaSize, CodigoRegimeTributario
from src.domains.empresas.models.cnpj import CNPJ
from src.domains.empresas.models.certificate_a1 import CertificateA1


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
    """Dados fiscais e de configuração do sistema."""
    crt: Optional[CodigoRegimeTributario] = field(
        default=CodigoRegimeTributario.REGIME_NORMAL)
    # Valores aceitos: HOMOLOGACAO, PRODUCAO
    environment: Optional[Environment] = field(default=Environment.HOMOLOGACAO)
    nfce_series: Optional[int] = None
    nfce_number: Optional[int] = None
    # ID do Número de identificação do CSC - Código de Segurança do Contribuínte.
    nfce_sefaz_id_csc: Optional[int] = None
    # Código de Segurança do Contribuínte.
    nfce_sefaz_csc: Optional[str] = None
    nfce_api_enabled: bool = False


@dataclass
class Empresa:
    """
    Representa os dados de uma empresa.

    Esta classe encapsula as informações e responsabilidades principais de uma empresa, incluindo
    dados fiscais, de contato, endereço, porte e configurações específicas.

    Attributes:
        corporate_name (str): Razão Social da empresa.
        email: str: E-mail da empresa.
        cnpj (CNPJ): CNPJ da empresa.
        id (Optional[str]): ID opcional da empresa.
        trade_name (Optional[str]): Nome fantasia da empresa.
        store_name (Optional[str]): Nome da loja.
        ie (str): Inscrição Estadual da empresa.
        im (Optional[str]): Inscrição Municipal da empresa.
        phone (Optional[PhoneNumber]): Telefone da empresa.
        address (Optional[Address]): Endereço da empresa.
        size (Optional[EmpresaSize]): Porte da empresa.
        fiscal (Optional[FiscalData]): Dados fiscais da empresa.
        cetificate_a1 (Optional[CertificateA1]): Certificado digital A1.
        logo_url (Optional[str]): Caminho para o logo da empresa.
        payment_gateway (Optional[AsaasPaymentGateway]): Gateway de pagamento da empresa.

    Example:
        Exemplo de como instanciar e usar a classe:
        >>> from src.domain.models.cnpj import CNPJ
        >>> cnpj = CNPJ("00.000.000/0000-00")
        >>> empresa = Empresa(trade_name="Minha Empresa", corporate_name="Minha Empresa Ltda", cnpj=cnpj,
        ...                   ie="123456789")
        >>> print(empresa)
    """
    corporate_name: str  # Razão Social
    email: str  # E-mail
    trade_name: Optional[str] = None  # Nome fantasia
    store_name: Optional[str] = 'Matriz'
    cnpj: Optional[CNPJ] = None  # CNPJ do emitente da NFCe
    id: Optional[str] = field(default=None)
    ie: Optional[str] = None  # Inscrição Estadual
    im: Optional[str] = None  # Inscrição Municipal
    phone: Optional[PhoneNumber] = None  # Telefone
    address: Optional[Address] = None
    size: Optional[EmpresaSize] = None  # Porte da empresa
    fiscal: Optional[FiscalData] = None
    certificate_a1: Optional[CertificateA1] = None

    # Logo no PDF da DANFCE
    logo_url: Optional[str] = None

    # Gateway de pagamento | Troque aqui o gateway de pagamento conforme contratado: Default Asaas
    payment_gateway: Optional[AsaasPaymentGateway] = None

    def __post_init__(self):
        """
        Método chamado automaticamente após a inicialização da instância da classe.

        Realiza validações adicionais e formatações necessárias.
        """
        # Campos obrigatórios
        self.corporate_name = self.corporate_name.upper().strip() if self.corporate_name else None
        if not self.corporate_name:
            raise ValueError("O campo 'corporate_name' é obrigatório.")

        self.email = self.email.lower().strip() if self.email else None
        if not self.email or "@" not in self.email:
            raise ValueError("O campo 'email' é obrigatório e deve conter um endereço de e-mail válido.")

        # Remove os espaços em branco ou garante que seja None caso vazio ''
        self.trade_name = self.trade_name.upper().strip() if self.trade_name else None
        self.store_name = self.store_name.strip() if self.store_name else None
        self.ie = self.ie.strip() if self.ie else None
        self.im = self.im.strip() if self.im else None
        self.logo_url = self.logo_url.strip() if self.logo_url else None

    def get_complete_address(self) -> str:
        """
        Retorna o endereço completo formatado.

        Returns:
            str: Endereço completo formatado ou mensagem indicando que o endereço não está configurado.
        """
        if not self.address:
            return "Endereço não informado"

        components = [
            f"{self.address.street}, {self.address.number}",
            self.address.complement or "",
            f"{self.address.neighborhood}" if self.address.neighborhood else "",
            f"{self.address.city} - {self.address.state}",
            f"CEP: {self.address.postal_code}"
        ]
        return ", ".join(filter(bool, components))

    def is_nfce_enabled(self) -> bool:
        """
        Verifica se a emissão de NFC-e está configurada.

        Returns:
            bool: True se a emissão de NFC-e estiver configurada, False caso contrário.
        """
        f = self.fiscal
        if not f:
            return False

        required_attributes = [
            f.crt,
            f.environment,
            f.nfce_series,
            f.nfce_number,
            f.nfce_sefaz_id_csc,
            f.nfce_sefaz_csc,
            f.nfce_api_enabled,
        ]

        return all(required_attributes)

    def get_nfce_data(self) -> Optional[Dict]:
        """
        Retorna um dicionário com os dados necessários para emissão da NFC-e.

        Returns:
            dict: Dicionário com dados da NFC-e.
        """
        if f := self.fiscal:
            return {
                "crt_name": f.crt.name if f.crt else None,
                "emvironment_name": f.environment.name if f.environment else None,
                "nfce_series": f.nfce_series,
                "nfce_number": f.nfce_number,
                "nfce_sefaz_id_csc": f.nfce_sefaz_id_csc,
                "nfce_sefaz_csc": f.nfce_sefaz_csc,
                "nfce_api_enabled": f.nfce_api_enabled,
            }

    def get_certificate_data(self) -> Optional[Dict]:
        if cert := self.certificate_a1:
            return {
                'serial_number': cert.serial_number,
                'not_valid_before': cert.not_valid_before,
                'not_valid_after': cert.not_valid_after,
                'subject_name': cert.subject_name,
                'file_name': cert.file_name,
                'cpf_cnpj': cert.cpf_cnpj,
                'nome_razao_social': cert.nome_razao_social,
                'password': cert.password.value,
                'storage_path': cert.storage_path,
            }

    def initials(self) -> str:
        """Retorna as iniciais do nome completo"""
        palavras_ignoradas = {'da', 'das', 'de', 'do', 'dos'}
        palavras = self.corporate_name.split()
        iniciais = [palavra[0]
                    for palavra in palavras if palavra not in palavras_ignoradas]
        return ''.join(iniciais)

    def to_dict(self) -> dict:
        """
        Converte a instância da classe Empresa em um dicionário.

        Returns:
            dict: Dicionário representando os dados da empresa.
        """
        return {
            "id": self.id,
            "corporate_name": self.corporate_name,
            "trade_name": self.trade_name,
            "store_name": self.store_name,
            "cnpj": self.cnpj,
            "email": self.email,
            "ie": self.ie,
            "im": self.im,
            "phone": self.phone,
            "address": self.address.__dict__ if self.address else None,
            "size": self.size if self.size else None,
            "fiscal": self.get_nfce_data(),
            "certificate_a1": self.get_certificate_data(),
            "logo_url": self.logo_url,
            "payment_gateway": self.payment_gateway.__dict__ if self.payment_gateway else None,
        }
