"""
ToDo: Refatorar. Aqui não deveria invocar diretamente a AsaasPaymentGateway (Está quebrando regra DDD)
e sim um handle de serviço de pagamento que invocaria os serviços de Asaas
from src.services.gateways.asaas_payment_gateway import AsaasPaymentGateway
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from src.domains.shared import Password, PhoneNumber, Address, RegistrationStatus
from src.services import AsaasPaymentGateway
from src.domains.empresas.models.empresas_subclass import Environment, EmpresaSize, CodigoRegimeTributario
from src.domains.empresas.models.certificate_a1 import CertificateA1
from src.domains.empresas.models.cnpj import CNPJ


@dataclass
class FiscalData:
    """Dados fiscais e de configuração do sistema."""
    crt: CodigoRegimeTributario | None = field(
        default=CodigoRegimeTributario.REGIME_NORMAL)
    # Valores aceitos: HOMOLOGACAO, PRODUCAO
    environment: Environment | None = field(default=Environment.HOMOLOGACAO)
    nfce_series: int | None = None
    nfce_number: int | None = None
    # ID do Número de identificação do CSC - Código de Segurança do Contribuínte.
    nfce_sefaz_id_csc: int | None = None
    # Código de Segurança do Contribuínte.
    nfce_sefaz_csc: str | None = None
    nfce_api_enabled: bool = False


@dataclass
class Empresa:
    """
    Representa os dados de uma empresa.

    Esta classe encapsula as informações e responsabilidades principais de uma empresa, incluindo
    dados fiscais, de contato, endereço, porte e configurações específicas.

    Attributes:
        corporate_name (str): Razão Social da empresa.
        email (str): E-mail da empresa.
        status (RegistrationStatus:Enum): Status da empresa.
        deleted_at: (datetime): Data de exclusão
        archived_at: (datetime | None): Data de arquivamento
        cnpj (CNPJ): CNPJ da empresa.
        id (str | None): ID opcional da empresa.
        trade_name (str | None): Nome fantasia da empresa.
        store_name (str | None): Nome da loja.
        ie (str): Inscrição Estadual da empresa.
        im (str | None): Inscrição Municipal da empresa.
        phone (PhoneNumber | None): Telefone da empresa.
        address (Address | None): Endereço da empresa.
        size (EmpresaSize | None): Porte da empresa.
        fiscal (FiscalData | None): Dados fiscais da empresa.
        certificate_a1 (CertificateA1 | None): Certificado digital A1.
        logo_url (str | None): Caminho para o logo da empresa.
        payment_gateway (AsaasPaymentGateway | None): Gateway de pagamento da empresa.

    Example:
        Exemplo de como instanciar e usar a classe:
        >>> from src.domain.models.cnpj import CNPJ
        >>> cnpj = CNPJ("00.000.000/0000-00")
        >>> empresa = Empresa(trade_name="Minha Empresa", corporate_name="Minha Empresa Ltda", cnpj=cnpj,
        ...                   ie="123456789", email="contato@empresa.com")
        >>> print(empresa)
    """
    corporate_name: str  # Razão Social
    email: str  # E-mail
    status: RegistrationStatus = RegistrationStatus.ACTIVE
    trade_name: str | None = None  # Nome fantasia
    store_name: str | None = 'Matriz'
    cnpj: CNPJ | None = None  # CNPJ do emitente da NFCe
    id: str | None = field(default=None)
    ie: str | None = None  # Inscrição Estadual
    im: str | None = None  # Inscrição Municipal
    phone: PhoneNumber | None = None  # Telefone
    address: Address | None = None
    size: EmpresaSize | None = None  # Porte da empresa
    fiscal: FiscalData | None = None
    certificate_a1: CertificateA1 | None = None
    activated_at: datetime | None = None
    activated_by_id: str | None = None
    activated_by_name: str | None = None
    created_at: datetime | None = None
    created_by_id: str | None = None
    created_by_name: str | None = None
    updated_at: datetime | None = None
    updated_by_id: str | None = None
    updated_by_name: str | None = None
    deleted_at: datetime | None = None
    deleted_by_id: str | None = None
    deleted_by_name: str | None = None
    archived_at: datetime | None = None
    archived_by_id: str | None = None
    archived_by_name: str | None = None

    # Logo no PDF da DANFCE
    logo_url: str | None = None

    # Gateway de pagamento | Troque aqui o gateway de pagamento conforme contratado: Default Asaas
    payment_gateway: AsaasPaymentGateway | None = None

    def __post_init__(self):
        """
        Método chamado automaticamente após a inicialização da instância da classe.

        Realiza validações adicionais e formatações necessárias.
        """
        # Campos obrigatórios
        if not self.corporate_name:
            raise ValueError("O campo 'corporate_name' é obrigatório.")
        self.corporate_name = self.corporate_name.upper(
        ).strip()

        if not self.email or "@" not in self.email:
            raise ValueError(
                "O campo 'email' é obrigatório e deve conter um endereço de e-mail válido.")
        self.email = self.email.lower().strip()

        # Remove os espaços em branco ou garante que seja None caso vazio ''
        self.trade_name = self.trade_name.upper().strip() if self.trade_name else None
        self.store_name = self.store_name.strip().capitalize() if self.store_name else None
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
        # Primeiro, verificar o CNPJ da empresa, que é fundamental.
        if not self.cnpj:
            return False

        # Depois, verificar se os dados fiscais existem.
        f = self.fiscal
        if not f:
            return False

        # Lista de atributos fiscais que devem estar preenchidos (não None).
        # nfce_api_enabled é um booleano e será verificado separadamente ou no final.
        required_fiscal_data_fields = [
            f.crt,
            f.environment,
            f.nfce_series,
            f.nfce_number,
            f.nfce_sefaz_id_csc,
            f.nfce_sefaz_csc,
        ]

        # Verifica se todos os campos de dados fiscais necessários estão preenchidos.
        if not all(required_fiscal_data_fields):
            return False

        # Por fim, verifica se a API NFC-e está habilitada.
        return f.nfce_api_enabled

    def get_nfce_data(self) -> dict[str, Any] | None:
        """
        Retorna um dicionário com os dados necessários para emissão da NFC-e.

        Returns:
            dict[str, Any] | None: Dicionário com dados da NFC-e ou None.
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

    def get_certificate_data(self) -> dict[str, Any] | None:
        """
        Retorna um dicionário com os dados do certificado A1.

        Returns:
            dict[str, Any] | None: Dicionário com dados do certificado ou None.
        """
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
        return None

    def initials(self) -> str:
        """Retorna as iniciais do nome completo"""
        palavras_ignoradas = {'da', 'das', 'de', 'do', 'dos', 'e'}
        palavras = self.corporate_name.split()
        iniciais = [palavra[0]
                    for palavra in palavras if palavra not in palavras_ignoradas]
        return ''.join(iniciais)

    def to_dict(self) -> dict[str, Any]:
        """
        Converte a instância da classe Empresa em um dicionário.

        Returns:
            dict[str, Any]: Dicionário representando os dados da empresa.
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
            "size": self.size.name if self.size else None,  # Usar .name para Enums
            "fiscal": self.get_nfce_data(),
            "certificate_a1": self.get_certificate_data(),
            "logo_url": self.logo_url,
            "payment_gateway": self.payment_gateway.__dict__ if self.payment_gateway and hasattr(self.payment_gateway, '__dict__') else None,
            "status": self.status,
            "activated_at": self.activated_at,
            "activated_by_id": self.activated_by_id,
            "activated_by_name": self.activated_by_name,
            "created_at": self.created_at,
            "created_by_id": self.created_by_id,
            "created_by_name": self.created_by_name,
            "updated_at": self.updated_at,
            "updated_by_id": self.updated_by_id,
            "updated_by_name": self.updated_by_name,
            "deleted_at": self.deleted_at,
            "deleted_by_id": self.deleted_by_id,
            "deleted_by_name": self.deleted_by_name,
            "archived_at": self.archived_at,
            "archived_by_id": self.archived_by_id,
            "archived_by_name": self.archived_by_name,
        }

    def to_dict_db(self) -> dict[str, Any]:
        """
        Converte o objeto Empresa e todos os seus atributos para um dicionário.

        Returns:
            dict[str, Any]: Representação da entidade Empresa como dicionário para um database.
            O ID da empresa não faz parte dos campos a serem salvos/alterados.
            O repositório do database obtem o ID do objeto Empresa.
        """

        dict_db = {
            "corporate_name": self.corporate_name,
            "trade_name": self.trade_name,
            "store_name": self.store_name,
            "cnpj": self.cnpj.raw_cnpj if self.cnpj else None,
            "email": self.email,
            "ie": self.ie,
            "im": self.im,
            "phone": self.phone.get_e164() if self.phone else None,
            "address": self.address.__dict__ if self.address else None,
            "size": self.size.name if self.size else None,
            "fiscal": self.get_nfce_data(),
            "certificate_a1": self.get_certificate_data(),  # Já é um dict ou None
            "logo_url": self.logo_url,
            "payment_gateway": self.payment_gateway.__dict__ if self.payment_gateway else None,
            "status": self.status.name,
            "activated_at": self.activated_at,
            "activated_by_id": self.activated_by_id,
            "activated_by_name": self.activated_by_name,
            "created_at": self.created_at,
            "created_by_id": self.created_by_id,
            "created_by_name": self.created_by_name,
            "updated_at": self.updated_at,
            "updated_by_id": self.updated_by_id,
            "updated_by_name": self.updated_by_name,
            "deleted_at": self.deleted_at,
            "deleted_by_id": self.deleted_by_id,
            "deleted_by_name": self.deleted_by_name,
            "archived_at": self.archived_at,
            "archived_by_id": self.archived_by_id,
            "archived_by_name": self.archived_by_name,
        }

        # Remove campos desnecessários para o banco de dados,
        # por exemplo, campos que não devem ser salvos ou são None (null)
        dict_db_filtered = {k: v for k, v in dict_db.items() if v is not None}

        return dict_db_filtered

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'Empresa':
        """
        Cria uma instância de Empresa a partir de um dicionário.

        Args:
            data (dict[str, Any]): Dicionário contendo os dados da empresa.

        Returns:
            Empresa: Nova instância de Empresa.
        """
        cnpj = None
        if cnpj_data := data.get("cnpj"):
            if isinstance(cnpj_data, CNPJ):
                cnpj = cnpj_data
            elif isinstance(cnpj_data, str):
                cnpj = CNPJ(cnpj_data)

        phone = None
        if phone_data := data.get("phone"):
            if isinstance(phone_data, PhoneNumber):
                phone = phone_data
            elif isinstance(phone_data, str):
                phone = PhoneNumber(phone_data)

        address = None
        if address_data := data.get("address"):
            if isinstance(address_data, Address):
                address = address_data
            elif isinstance(address_data, dict):
                address = Address(**address_data)

        size = None
        if size_data := data.get("size"):
            if isinstance(size_data, EmpresaSize):
                size = size_data
            elif type(size_data) is str:
                size = EmpresaSize[size_data]

        fiscal: FiscalData | None = None
        if fiscal_data := data.get("fiscal"):
            if isinstance(fiscal_data, FiscalData):
                fiscal = fiscal_data
            elif isinstance(fiscal_data, dict):
                # Processar enums e valores convertidos separadamente para maior clareza
                crt_name = fiscal_data.get("crt_name")
                crt = CodigoRegimeTributario[crt_name] if crt_name else None

                env_name = fiscal_data.get("environment_name")
                environment = Environment[env_name] if env_name else None

                nfce_series_raw = fiscal_data.get("nfce_series")
                nfce_series = int(nfce_series_raw) if nfce_series_raw is not None else None

                # Criar objeto fiscal com valores processados
                fiscal = FiscalData(
                    crt=crt,
                    environment=environment,
                    nfce_series=nfce_series,
                    nfce_number=fiscal_data.get("nfce_number"),
                    nfce_sefaz_id_csc=fiscal_data.get("nfce_sefaz_id_csc"),
                    nfce_sefaz_csc=fiscal_data.get("nfce_sefaz_csc"),
                    nfce_api_enabled=fiscal_data.get("nfce_api_enabled", False),
                )

        certificate_a1: CertificateA1 | None = None
        if certificate_a1_input_data := data.get("certificate_a1"):
            # Caso já seja uma instância do tipo correto
            if isinstance(certificate_a1_input_data, CertificateA1):
                certificate_a1 = certificate_a1_input_data

            # Caso seja um dicionário, extrair dados e criar nova instância
            elif isinstance(certificate_a1_input_data, dict):
                # Extrair a senha do certificado
                password_value = certificate_a1_input_data.get('password')
                if password_value is None:
                    raise ValueError("Senha do certificado ausente ao criar CertificateA1 a partir de dict")

                # Converter para objeto Password se necessário
                cert_password = (password_value if isinstance(password_value, Password)
                                else Password(str(password_value)))

                # Criar cópia do dicionário sem a senha para passar como kwargs
                cert_data = {k: v for k, v in certificate_a1_input_data.items() if k != 'password'}

                # Criar nova instância de CertificateA1
                certificate_a1 = CertificateA1(password=cert_password, **cert_data)

        payment_gateway : AsaasPaymentGateway | None = None
        if payment_gateway_data := data.get("payment_gateway"):
            if isinstance(payment_gateway_data, AsaasPaymentGateway):
                payment_gateway = payment_gateway_data
            elif isinstance(payment_gateway_data, dict):
                payment_gateway = AsaasPaymentGateway(**payment_gateway_data)

        # Converte enums
        status_data = data.get("status", RegistrationStatus.ACTIVE)
        status = status_data # Por padrão status é do tipo RegistrationStatus

        if not isinstance(status_data, RegistrationStatus):
            if isinstance(status_data, str) and status_data in RegistrationStatus.__members__:
                status = RegistrationStatus[status_data]
            else:
                status = RegistrationStatus.ACTIVE

        return cls(
            id=data.get("id"),  # id pode ser None
            corporate_name=data["corporate_name"],
            trade_name=data.get("trade_name"),
            store_name=data.get("store_name"),
            cnpj=cnpj,
            email=data["email"],
            ie=data.get("ie"),
            im=data.get("im"),
            phone=phone,
            address=address,
            size=size,
            fiscal=fiscal,
            certificate_a1=certificate_a1,
            logo_url=data.get("logo_url"),
            payment_gateway=payment_gateway,
            status=status,
            activated_at=data.get("activated_at"),
            activated_by_id=data.get("activated_by_id"),
            activated_by_name=data.get("activated_by_name"),
            created_at=data.get("created_at"),
            created_by_id=data.get("created_by_id"),
            created_by_name=data.get("created_by_name"),
            updated_at=data.get("updated_at"),
            updated_by_id=data.get("updated_by_id"),
            updated_by_name=data.get("updated_by_name"),
            deleted_at=data.get("deleted_at"),
            deleted_by_id=data.get("deleted_by_id"),
            deleted_by_name=data.get("deleted_by_name"),
            archived_at=data.get("archived_at"),
            archived_by_id=data.get("archived_by_id"),
            archived_by_name=data.get("archived_by_name"),
        )
