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


@dataclass
class FormaPagamento:
    """
    Representa uma forma de pagamento de uma empresa.

    Attributes:
        id (str | None): ID do documento no Firestore.
        empresa_id (str): ID da empresa à qual esta forma de pagamento pertence.
        nome (str): Nome de exibição da forma de pagamento (ex: "Crédito à Vista").
        nome_lower (str|None): Nome em lowercase para indices e busca no banco de dados
        tipo (TipoPagamento): O tipo padronizado de pagamento.
        status (RegistrationStatus): Status do registro (ATIVO, INATIVO).
        desconto_percentual (float): Percentual de desconto a ser aplicado (ex: 5.0 para 5%).
        acrescimo_percentual (float): Percentual de acréscimo a ser aplicado.
        # ordem (int): Posição para ordenação na interface. Não está em uso por enquanto
        created_at (datetime | None): Data e hora de criação.
        ... (outros campos de auditoria)
    """
    empresa_id: str
    nome: str
    tipo: TipoPagamento
    nome_lower: str | None = None
    id: str | None = None
    status: RegistrationStatus = RegistrationStatus.ACTIVE
    desconto_percentual: float = 0.0
    acrescimo_percentual: float = 0.0
    ordem: int = 99

    # Campos de Auditoria
    created_at: datetime | None = field(default_factory=lambda: datetime.now(UTC))
    created_by_id: str | None = None
    created_by_name: str | None = None
    updated_at: datetime | None = None
    updated_by_id: str | None = None
    updated_by_name: str | None = None

    def __post_init__(self):
        """Validações e normalizações após a inicialização."""
        if not self.empresa_id:
            raise ValueError("O campo 'empresa_id' é obrigatório.")
        if not self.nome:
            raise ValueError("O campo 'nome' é obrigatório.")
        self.nome = self.nome.strip()
        self.nome_lower = self.nome.lower()

        if not isinstance(self.tipo, TipoPagamento):
            raise ValueError("O campo 'tipo' deve ser uma instância de TipoPagamento.")

    def to_dict(self) -> dict:
        """Converte o objeto para um dicionário para salvar no Firestore."""
        dict_db = {
            "id": self.id,
            "empresa_id": self.empresa_id,
            "nome": self.nome,
            "nome_lower": self.nome_lower,
            "tipo": self.tipo.name,  # Salva o nome do enum (ex: "PIX")
            "status": self.status.name,
            "desconto_percentual": self.desconto_percentual,
            "acrescimo_percentual": self.acrescimo_percentual,
            "ordem": self.ordem,
            "created_at": self.created_at,
            "created_by_id": self.created_by_id,
            "created_by_name": self.created_by_name,
            "updated_at": self.updated_at,
            "updated_by_id": self.updated_by_id,
            "updated_by_name": self.updated_by_name,
        }
        # Remove chaves com valor None para não poluir o banco
        return {k: v for k, v in dict_db.items() if v is not None}

    @classmethod
    def from_dict(cls, data: dict) -> 'FormaPagamento':
        """Cria uma instância de FormaPagamento a partir de um dicionário."""

        # Converte a string do tipo para o Enum correspondente
        tipo_str = data.get("tipo")
        try:
            tipo = TipoPagamento[tipo_str] if tipo_str else TipoPagamento.OUTRO
        except KeyError:
            # Se o tipo do banco não existir mais no Enum, trata como "Outro"
            tipo = TipoPagamento.OUTRO

        # Converte a string de status para o Enum
        status_str = data.get("status", "ACTIVE")
        try:
            status = RegistrationStatus[status_str]
        except KeyError:
            status = RegistrationStatus.ACTIVE

        # Converte Timestamps do Firestore para datetime
        for key in ['created_at', 'updated_at']:
            if key in data and data.get(key) and hasattr(data[key], 'to_datetime'):
                data[key] = data[key].to_datetime()

        return cls(
            id=data.get("id"),
            empresa_id=data["empresa_id"],
            nome=data["nome"],
            nome_lower=data["nome_lower"],
            tipo=tipo,
            status=status,
            desconto_percentual=data.get("desconto_percentual", 0.0),
            acrescimo_percentual=data.get("acrescimo_percentual", 0.0),
            ordem=data.get("ordem", 99),
            created_at=data.get("created_at"),
            created_by_id=data.get("created_by_id"),
            created_by_name=data.get("created_by_name"),
            updated_at=data.get("updated_at"),
            updated_by_id=data.get("updated_by_id"),
            updated_by_name=data.get("updated_by_name"),
        )
