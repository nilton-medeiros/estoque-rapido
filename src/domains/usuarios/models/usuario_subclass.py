from enum import Enum


class UsuarioStatus(Enum):
    ACTIVE = "Ativo"
    INACTIVE = "Inativo"
    DELETED = "Lixeira"


class UsuarioProfile(Enum):
    ADMIN = "Admin"
    BILLING = "Cobrança"
    ACCOUNTING = "Contabil"
    FINANCE = "Financeiro"
    PAYMENT = "Pagamento"
    SALES = "Vendas"
    UNDEFINED = "Indefinido"
