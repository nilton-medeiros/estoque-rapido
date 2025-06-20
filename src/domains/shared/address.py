from dataclasses import dataclass


@dataclass
class Address:
    street: str
    number: str
    city: str
    state: str
    postal_code: str
    complement: str | None = None
    neighborhood: str | None = None
