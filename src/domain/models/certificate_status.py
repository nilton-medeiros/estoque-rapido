from enum import Enum


class CertificateStatus(Enum):
    ACTIVE = "ATIVO"
    EXPIRED = "EXPIRADO"
    INVALID = "INVÁLIDO"
    EMPTY = "VAZIO"
