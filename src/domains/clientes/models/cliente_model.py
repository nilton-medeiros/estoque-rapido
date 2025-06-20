from dataclasses import dataclass
from datetime import date

from src.domains.shared import Address, NomePessoa, PhoneNumber


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
        - is_whatsapp (bool): Se o número do celular tem Whatsapp.
        - cpf (str | None): CPF do cliente (opcional, mas obrigatório para emitir NFCe).
        - delivery_address (Address | None): Endereço de entrega do cliente (opcional).
        - birthday (date | None): Data de nascimento do cliente (opcional).
    """
    name: NomePessoa
    phone: PhoneNumber
    is_whatsapp: bool
    cpf: str | None
    id: str | None
    delivery_address: Address | None
    birthday: date | None

    # --- Campos de Status e Auditoria
    status: 