from dataclasses import dataclass, field
from datetime import datetime, date, UTC
import re

from src.domains.shared import Address, NomePessoa, PhoneNumber, RegistrationStatus


@dataclass
class Cliente:
    """
    Representa os dados de um cliente.

    Esta classe encapsula as informações e responsabilidade principais de um cliente, incluíndo
    dados para emissão de NFCe, endereço e outros.

    Attributes:
        - id (str): Identificação do cliente no sistema.
        - name (NomePessoa): Nome do cliente.
        - phone (PhoneNumber): Número do celular do cliente.
        - cpf (str | None): CPF do cliente (opcional, mas obrigatório para emitir NFCe).
        - email (str | None): E-mail do cliente (opcional).
        - delivery_address (Address | None): Endereço de entrega do cliente (opcional).
        - birthday (date | None): Data de nascimento do cliente (opcional).
        - is_whatsapp (bool): Se o número do celular tem Whatsapp.
        - status (RegistrationStatus): Status do cliente (Ativo, Inativo, Lixeira)
        - Demais Campos padrão de Auditoria
    """
    name: NomePessoa
    phone: PhoneNumber
    id: str | None
    cpf: str | None
    email: str | None
    delivery_address: Address | None
    birthday: date | None
    is_whatsapp: bool = False
    status: RegistrationStatus = RegistrationStatus.ACTIVE

    # --- Campos de Auditoria
    created_at: datetime | None = field(default_factory=lambda: datetime.now(UTC))
    created_by_id: str | None = None
    created_by_name: str | None = None

    updated_at: datetime | None = None
    updated_by_id: str | None = None
    updated_by_name: str | None = None

    activated_at: datetime | None = None
    activated_by_id: str | None = None
    activated_by_name: str | None = None

    inactivated_at: datetime | None = None
    inactivated_by_id: str | None = None
    inactivated_by_name: str | None = None

    deleted_at: datetime | None = None
    deleted_by_id: str | None = None
    deleted_by_name: str | None = None

    def __post_init__(self):
        """
        Executa validações e normalizações após a inicialização do objeto.
        """
        if not self.name or not self.name.first_name:
            raise ValueError("O nome do cliente é obrigatório.")

        if self.cpf:
            # Remove qualquer formatação do CPF, mantendo apenas os dígitos
            self.cpf = re.sub(r'\D', '', self.cpf)

        if self.email:
            self.email = self.email.strip().lower()
            if "@" not in self.email:
                raise ValueError("O campo e-mail deve conter um endereço de e-mail válido")

        # Se o cliente está sendo criado como ACTIVE e não tem activated_at, define-o
        if self.status == RegistrationStatus.ACTIVE and self.created_at and not self.activated_at:
            self.activated_at = self.created_at
            self.activated_by_id = self.created_by_id
            self.activated_by_name = self.created_by_name


    def to_dict(self) -> dict:
        """
        Converte o objeto Cliente para um dicionário.

        Returns:
            dict: Representação do cliente como dicionário.
        """
        return {
            "id": self.id,
            "name": self.name,
            "phone": self.phone,
            "is_whatsapp": self.is_whatsapp,
            "cpf": self.cpf,
            "email": self.email,
            "delivery_address": self.delivery_address.__dict__ if self.delivery_address else None,
            "birthday": self.birthday,
            "status": self.status.name,
            "created_at": self.created_at,
            "created_by_id": self.created_by_id,
            "created_by_name": self.created_by_name,
            "updated_at": self.updated_at,
            "updated_by_id": self.updated_by_id,
            "updated_by_name": self.updated_by_name,
            "activated_at": self.activated_at,
            "activated_by_id": self.activated_by_id,
            "activated_by_name": self.activated_by_name,
            "inactivated_at": self.inactivated_at,
            "inactivated_by_id": self.inactivated_by_id,
            "inactivated_by_name": self.inactivated_by_name,
            "deleted_at": self.deleted_at,
            "deleted_by_id": self.deleted_by_id,
            "deleted_by_name": self.deleted_by_name,
        }

    def to_dict_db(self) -> dict:
        """
        Converte o objeto Cliente para um dicionário para persistência no banco de dados.
        O ID do cliente não é incluído, pois é a chave do documento.
        Valores None são removidos para otimizar o armazenamento.
        """
        dict_db = {
            "name": self.name.to_dict() if self.name else None,
            "phone": self.phone.get_e164() if self.phone else None,
            "is_whatsapp": self.is_whatsapp,
            "cpf": self.cpf,
            "delivery_address": self.delivery_address.__dict__ if self.delivery_address else None,
            "birthday": self.birthday,
            "status": self.status.name,
            "created_at": self.created_at,
            "created_by_id": self.created_by_id,
            "created_by_name": self.created_by_name,
            "updated_at": self.updated_at,
            "updated_by_id": self.updated_by_id,
            "updated_by_name": self.updated_by_name,
            "activated_at": self.activated_at,
            "activated_by_id": self.activated_by_id,
            "activated_by_name": self.activated_by_name,
            "inactivated_at": self.inactivated_at,
            "inactivated_by_id": self.inactivated_by_id,
            "inactivated_by_name": self.inactivated_by_name,
            "deleted_at": self.deleted_at,
            "deleted_by_id": self.deleted_by_id,
            "deleted_by_name": self.deleted_by_name,
        }
        # Remove chaves com valor None
        return {k: v for k, v in dict_db.items() if v is not None}

    @classmethod
    def from_dict(cls, data: dict) -> 'Cliente':
        """
        Cria uma instância de Cliente a partir de um dicionário (geralmente do Firestore).
        """
        # Converte enums
        status_data = data.get("status")
        status = RegistrationStatus[status_data] if isinstance(
            status_data, str) else RegistrationStatus.ACTIVE

        # Converte Timestamps do Firestore para datetime/date
        for key in ['created_at', 'updated_at', 'activated_at', 'inactivated_at', 'deleted_at', 'birthday']:
            if key in data and data.get(key) and hasattr(data[key], 'to_datetime'):
                dt_obj = data[key].to_datetime()
                data[key] = dt_obj.date() if key == 'birthday' else dt_obj

        # Converte objetos aninhados
        try:
            # Fornece um dict vazio como padrão para evitar passar None para from_dict.
            # O próprio from_dict/NomePessoa.__init__ levantará um ValueError se os dados forem insuficientes.
            name_obj = NomePessoa.from_dict(data.get("name", {}))
        except ValueError:  # Captura o erro de validação de NomePessoa
            # Se houver erro ao criar NomePessoa, cria uma instância padrão
            name_obj = NomePessoa(first_name="[Nome não informado]")

        try:
            # Fornece uma string vazia como padrão para que from_dict possa validar.
            phone_obj = PhoneNumber.from_dict(data.get("phone", ""))
        except ValueError:  # Captura o erro de validação de PhoneNumber
            # Se houver erro ao criar PhoneNumber, cria uma instância padrão
            phone_obj = PhoneNumber("+5500000000000")

        address_data = data.get("delivery_address")
        address_obj = Address(**address_data) if isinstance(address_data, dict) and address_data else None

        # Remove campos já tratados para evitar passar duas vezes no construtor
        for key in ["name", "phone", "delivery_address", "status"]:
            data.pop(key, None)

        return cls(
            name=name_obj,
            phone=phone_obj,
            delivery_address=address_obj,
            status=status,
            **data
        )
