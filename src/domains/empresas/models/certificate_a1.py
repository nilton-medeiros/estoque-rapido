from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from src.domains.shared.password import Password


@dataclass
class CertificateA1:
    """Certificado digital (PFX ou P12)."""
    password: Password
    serial_number: Optional[str] = None  # Número de série do certificado
    issuer_name: Optional[str] = None  # Emissor do certificado
    # Data e hora de início da validade do certificado
    not_valid_before: Optional[datetime] = None
    # Data e hora do fim da validade do certificado
    not_valid_after: Optional[datetime] = None

    # O thumbprint (ou impressão digital) de um certificado digital A1 é uma representação única e compacta do certificado
    # thumbprint: Optional[str] = None  NÃO USADO
    subject_name: Optional[str] = None  # Nome do assunto
    file_name: Optional[str] = None  # Nome do arquivo
    # Documento da pessoa ou empresa dona do certificado A1
    cpf_cnpj: Optional[str] = None
    nome_razao_social: Optional[str] = None
    storage_path: str = None
