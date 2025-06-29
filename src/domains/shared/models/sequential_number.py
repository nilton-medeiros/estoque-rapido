from dataclasses import dataclass
from datetime import datetime, UTC
from typing import Any


@dataclass
class SequentialNumber:
    """
    Representa um contador sequencial para documentos, específico por empresa.
    """
    name: str  # Ex: "pedido", "fatura"
    next_number: int
    empresa_id: str  # ID da empresa à qual este contador pertence
    id: str | None = None # ID do documento no Firestore (gerado automaticamente)

    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self):
        if not self.name:
            raise ValueError("O nome do contador sequencial é obrigatório.")
        if not isinstance(self.next_number, int) or self.next_number < 0:
            raise ValueError("O próximo número deve ser um inteiro não negativo.")
        if not self.empresa_id:
            raise ValueError("O ID da empresa é obrigatório para um contador sequencial.")
        if self.created_at is None:
            self.created_at = datetime.now(UTC)

    def to_dict_db(self) -> dict[str, Any]:
        """Converte o objeto para um dicionário para o banco de dados."""
        dict_db = {
            "name": self.name,
            "next_number": self.next_number,
            "empresa_id": self.empresa_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        return {k: v for k, v in dict_db.items() if v is not None}

    @classmethod
    def from_dict(cls, data: dict[str, Any], doc_id: str | None = None) -> "SequentialNumber":
        """Cria uma instância de SequentialNumber a partir de um dicionário."""
        # Converte Timestamps do Firestore para datetime
        for key in ['created_at', 'updated_at']:
            if key in data and data.get(key) and hasattr(data[key], 'to_datetime'):
                data[key] = data[key].to_datetime()

        return cls(
            id=doc_id or data.get("id"),
            name=data["name"],
            next_number=data["next_number"],
            empresa_id=data["empresa_id"],
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )
