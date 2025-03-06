from dataclasses import dataclass, field
# from datetime import datetime
from enum import Enum

from cryptography.fernet import Fernet
from dotenv import load_dotenv
import os

from typing import Optional, Dict

from src.domain.models.company_subclass import Environment, CodigoRegimeTributario, CompanySize
from src.domain.models.certificate_a1 import CertificateA1
from src.domain.models.cnpj import CNPJ
from src.domain.models.cpf import CPF
from src.domain.models.phone_number import PhoneNumber

"""
ToDo: Refatorar, aqui não deveria invocar diretamente a AsaasPaymentGateway
e sim um handle de serviço de pagamento que invocaria os serviços de Asaas
from src.services.gateways.asaas_payment_gateway import PaymentGateway
"""
from src.services.gateways.asaas_payment_gateway import AsaasPaymentGateway


class TypeOfDocument(Enum):
    CNPJ = "CNPJ"
    CPF = "CPF"



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
    crt: Optional[CodigoRegimeTributario] = field(default=CodigoRegimeTributario.REGIME_NORMAL)
    environment: Optional[Environment] = field(default=Environment.HOMOLOGACAO)  # Valores aceitos: HOMOLOGACAO, PRODUCAO
    nfce_series: Optional[int] = None
    nfce_number: Optional[int] = None
    nfce_sefaz_id_csc: Optional[int] = None  # ID do Número de identificação do CSC - Código de Segurança do Contribuínte.
    nfce_sefaz_csc: Optional[str] = None   # Código de Segurança do Contribuínte.


@dataclass
class Company:
    """
    Representa os dados de uma empresa.

    Esta classe encapsula as informações e responsabilidades principais de uma empresa, incluindo
    dados fiscais, de contato, endereço, porte e configurações específicas.

    Attributes:
        document_type (TypeOfDocument): Tipo de documento: CNPJ ou CPF
        corporate_name (str): Razão Social da empresa.
        email: str: E-mail da empresa.
        cnpj (CNPJ): CNPJ da empresa.
        cpf (CPF): CPF do emitente da NFCe.
        id (Optional[str]): ID opcional da empresa.
        name (Optional[str]): Nome fantasia da empresa.
        store_name (Optional[str]): Nome da loja.
        ie (str): Inscrição Estadual da empresa.
        im (Optional[str]): Inscrição Municipal da empresa.
        phone (Optional[PhoneNumber]): Telefone da empresa.
        address (Optional[Address]): Endereço da empresa.
        size (Optional[CompanySize]): Porte da empresa.
        fiscal (Optional[FiscalData]): Dados fiscais da empresa.
        cetificate_a1 (Optional[CertificateA1]): Certificado digital A1.
        logo_url (Optional[str]): Caminho para o logo da empresa.
        payment_gateway (Optional[AsaasPaymentGateway]): Gateway de pagamento da empresa.

    Example:
        Exemplo de como instanciar e usar a classe:
        >>> from src.domain.models.cnpj import CNPJ
        >>> cnpj = CNPJ("00.000.000/0000-00")
        >>> company = Company(name="Minha Empresa", corporate_name="Minha Empresa Ltda", cnpj=cnpj,
        ...                   ie="123456789")
        >>> print(company)
    """
    document_type: TypeOfDocument
    corporate_name: str  # Razão Social ou Nome do Emitente qdo CPF
    email: str  # E-mail
    name: Optional[str]  # Nome fantasia
    initials_corporate_name: Optional[str] = None
    cnpj: Optional[CNPJ] = None  # CNPJ do emitente da NFCe
    cpf: Optional[CPF] = None  # CPF do responsável
    store_name: Optional[str] = 'Matriz'
    id: Optional[str] = field(default=None)
    ie: Optional[str] = None  # Inscrição Estadual
    im: Optional[str] = None  # Inscrição Municipal
    phone: Optional[PhoneNumber] = None  # Telefone
    address: Optional[Address] = None
    size: Optional[CompanySize] = None  # Porte da empresa
    fiscal: Optional[FiscalData] = None
    certificate_a1: Optional[CertificateA1] = None

    # Metadados opcionais
    logo_url: Optional[str] = None

    # Gateway de pagamento | Troque aqui o gateway de pagamento conforme contratado: Default Asaas
    payment_gateway: Optional[AsaasPaymentGateway] = None

    _key: str = field(init=False)
    _cipher_suite: Fernet = field(init=False)

    def __post_init__(self):
        """
        Método chamado automaticamente após a inicialização da instância da classe.

        Realiza validações adicionais e formatações necessárias.
        """
        self.name = self.name.upper()
        self.corporate_name = self.corporate_name.upper()
        self.initials_corporate_name = self.initials()

        # Carrega a chave de criptografia para senhas usadas no app
        load_dotenv()
        self._key = os.getenv("FERNET_KEY")
        self._cipher_suite = Fernet(self._key)

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
        ]

        return all(required_attributes)

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
                "nfce_sefaz_csc": f.nfce_sefaz_csc
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
                'password_encrypted': cert.password_encrypted,
                'storage_path': cert.storage_path,
            }

    def initials(self) -> str:
        """Retorna as iniciais do nome completo"""
        palavras_ignoradas = {'da', 'de', 'do'}
        palavras = self.corporate_name.split()
        iniciais = [palavra[0] for palavra in palavras if palavra not in palavras_ignoradas]
        return ''.join(iniciais)
