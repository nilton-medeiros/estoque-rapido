from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import Enum

from src.domains.shared import RegistrationStatus


class TipoPagamento(Enum):
    """Enum para os tipos de pagamento padronizados."""
    DINHEIRO = "Dinheiro"
    PIX = "PIX"
    DEBITO = "Cartão de Débito"
    CREDITO = "Cartão de Crédito"
    CREDIARIO = "Crediário"
    OUTRO = "Outro"

class TipoPercentual(Enum):
    """Enum para os tipos de operação (desconto/acréscimo) de uma forma de pagamento."""
    ACRESCIMO = "ACRÉSCIMO"
    DESCONTO = "DESCONTO"

@dataclass
class FormaPagamento:
    """
    Representa uma forma de pagamento de uma empresa.

    Attributes:
        id (str | None): ID do documento no Firestore.
        empresa_id (str): ID da empresa à qual esta forma de pagamento pertence.
        name (str): Nome de exibição da forma de pagamento (ex: "Crédito à Vista").
        name_lower (str|None): Nome em lowercase para indices e busca no banco de dados
        payment_type (TipoPagamento): O payment_type padronizado de pagamento.
        status (RegistrationStatus): Status do registro (ATIVO, INATIVO).
        percentage (float): Percentual de desconto a ser aplicado (ex: 5.0 para 5%).
        percentage_type (float): Percentual de acréscimo a ser aplicado.
        # order (int): Posição para ordenação na interface. Não está em uso por enquanto
        created_at (datetime | None): Data e hora de criação.
        ... (outros campos de auditoria)
    """
    empresa_id: str
    name: str
    payment_type: TipoPagamento
    name_lower: str | None = None
    id: str | None = None
    status: RegistrationStatus = RegistrationStatus.ACTIVE
    percentage: float = 0.0
    percentage_type: TipoPercentual = TipoPercentual.DESCONTO

    order: int = 99

    # Campos de Auditoria
    created_at: datetime | None = field(default_factory=lambda: datetime.now(UTC))
    created_by_id: str | None = None
    created_by_name: str | None = None
    updated_at: datetime | None = None
    updated_by_id: str | None = None
    updated_by_name: str | None = None
    deleted_at: datetime | None = None
    deleted_by_id: str | None = None
    deleted_by_name: str | None = None

    def __post_init__(self):
        """Validações e normalizações após a inicialização."""
        if not self.empresa_id:
            raise ValueError("O campo 'empresa_id' é obrigatório.")
        if not self.name:
            raise ValueError("O campo 'name' é obrigatório.")
        self.name = self.name.strip()
        self.name_lower = self.name.lower()

        if not isinstance(self.payment_type, TipoPagamento):
            raise ValueError("O campo 'payment_type' deve ser uma instância de TipoPagamento.")

    def to_dict(self) -> dict:
        """Converte o objeto para um dicionário para o form state manager (page.app_state)."""
        dict_db = {
            "id": self.id,
            "empresa_id": self.empresa_id,
            "name": self.name,
            "name_lower": self.name_lower,
            "payment_type": self.payment_type,
            "status": self.status,
            "percentage": self.percentage,
            "percentage_type": self.percentage_type,
            "order": self.order,
            "created_at": self.created_at,
            "created_by_id": self.created_by_id,
            "created_by_name": self.created_by_name,
            "updated_at": self.updated_at,
            "updated_by_id": self.updated_by_id,
            "updated_by_name": self.updated_by_name,
            "deleted_at": self.deleted_at,
            "deleted_by_id": self.deleted_by_id,
            "deleted_by_name": self.deleted_by_name,
        }
        # Remove chaves com valor None para não poluir o banco
        return {k: v for k, v in dict_db.items() if v is not None}

    def to_dict_db(self) -> dict:
        """
        Converte o objeto para um dicionário para salvar no Firestore.
        O ID do registro não está presente; será o ID do documento.
        Filtra chaves com valor None antes de salvar.
        """
        dict_db = {
            "empresa_id": self.empresa_id,
            "name": self.name,
            "name_lower": self.name_lower,
            "payment_type": self.payment_type.name,
            "status": self.status.name,
            "percentage": self.percentage,
            "percentage_type": self.percentage_type.name,
            "order": self.order,
            "created_at": self.created_at,
            "created_by_id": self.created_by_id,
            "created_by_name": self.created_by_name,
            "updated_at": self.updated_at,
            "updated_by_id": self.updated_by_id,
            "updated_by_name": self.updated_by_name,
            "deleted_at": self.deleted_at,
            "deleted_by_id": self.deleted_by_id,
            "deleted_by_name": self.deleted_by_name,
        }
        # Remove chaves com valor None para não poluir o banco
        return {k: v for k, v in dict_db.items() if v is not None}

    @classmethod
    def from_dict(cls, data: dict) -> 'FormaPagamento':
        """Cria uma instância de FormaPagamento a partir de um dicionário."""

        # Converte a string do payment_type para o Enum correspondente
        tipo_str = data.get("payment_type")
        try:
            payment_type = TipoPagamento[tipo_str] if tipo_str else TipoPagamento.OUTRO
        except KeyError:
            # Se o payment_type do banco não existir mais no Enum, trata como "Outro"
            payment_type = TipoPagamento.OUTRO

        # Converte a string de status para o Enum
        status_str = data.get("status", "ACTIVE")
        try:
            status = RegistrationStatus[status_str]
        except KeyError:
            status = RegistrationStatus.ACTIVE

        # Converte a string de percentage_type para o Enum
        percentage_type_str = data.get("percentage_type", "ACRESCIMO")
        try:
            percentage_type = TipoPercentual[percentage_type_str]
        except KeyError:
            percentage_type = TipoPercentual.ACRESCIMO

        # Converte Timestamps do Firestore para datetime
        for key in ['created_at', 'updated_at', 'deleted_at']:
            if key in data and data.get(key) and hasattr(data[key], 'to_datetime'):
                data[key] = data[key].to_datetime()

        return cls(
            id=data.get("id"),
            empresa_id=data["empresa_id"],
            name=data["name"],
            name_lower=data["name_lower"],
            payment_type=payment_type,
            status=status,
            percentage=data.get("percentage", 0.0),
            percentage_type=percentage_type,
            order=data.get("order", 99),
            created_at=data.get("created_at"),
            created_by_id=data.get("created_by_id"),
            created_by_name=data.get("created_by_name"),
            updated_at=data.get("updated_at"),
            updated_by_id=data.get("updated_by_id"),
            updated_by_name=data.get("updated_by_name"),
            deleted_at=data.get("deleted_at"),
            deleted_by_id=data.get("deleted_by_id"),
            deleted_by_name=data.get("deleted_by_name"),
        )
