from dataclasses import dataclass
from datetime import date


@dataclass
class AsaasPaymentGateway:
    customer_id: str  # ID do cliente na Asaas
    nextDueDate: date = None  # YYYY-MM-DD
    billingType: str = ''
    status: str = ""
    dateCreated: date = None
