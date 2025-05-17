from dataclasses import dataclass
from datetime import datetime

from src.domains.shared.password import Password


@dataclass
class CertificateA1:
    """Certificado digital (PFX ou P12)."""
    password: Password
    serial_number: str|None = None  # Número de série do certificado
    issuer_name: str|None = None  # Emissor do certificado
    # Data e hora de início da validade do certificado
    not_valid_before: datetime|None = None
    # Data e hora do fim da validade do certificado
    not_valid_after: datetime|None = None

    # O thumbprint (ou impressão digital) de um certificado digital A1 é uma representação única e compacta do certificado
    # thumbprint: str|None = None  NÃO USADO
    subject_name: str|None = None  # Nome do assunto
    file_name: str|None = None  # Nome do arquivo
    # Documento da pessoa ou empresa dona do certificado A1
    cpf_cnpj: str|None = None
    nome_razao_social: str|None = None
    storage_path: str|None = None
