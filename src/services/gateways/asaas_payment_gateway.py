from dataclasses import dataclass
from datetime import date

# ToDo: Implementar a integração com a API da Asaas
@dataclass
class AsaasPaymentGateway:
    customer_id: str  # ID do cliente na Asaas
    nextDueDate: date|None = None  # YYYY-MM-DD
    billingType: str = ''
    status: str = ""
    dateCreated: date|None = None
