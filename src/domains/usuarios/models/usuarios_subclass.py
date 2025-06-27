from enum import Enum


class UserProfile(Enum):
    ADMIN = "Admin"
    BILLING = "Cobrança"
    ACCOUNTING = "Contabil"
    FINANCE = "Financeiro"
    PAYMENT = "Pagamento"
    SALES = "Vendas"
    UNDEFINED = "Indefinido"
