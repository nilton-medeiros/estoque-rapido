from enum import Enum


class UsuarioStatus(Enum):
    ACTIVE = "Ativo"
    INACTIVE = "Inativo"
    DELETED = "Lixeira"
