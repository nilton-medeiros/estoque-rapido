from enum import Enum


class UsuarioProfile(Enum):
    ADMIN = "Admin"
    BILLING = "Cobrança"
    ACCOUNTING = "Contabil"
    FINANCE = "Financeiro"
    PAYMENT = "Pagamento"
    SALES = "Vendas"
    UNDEFINED = "Indefinido"
