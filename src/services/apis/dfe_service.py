from src.domain.models.company_subclass import Environment
from src.services.interfaces.dfe_provider import DFeProvider


class DFeService:
    def __init__(self, provider: DFeProvider, cpf_cnpj: str):
        self.provider = provider
        self.cpf_cnpj = cpf_cnpj

    async def certificate_save(self, certificado: bytes, passowrd: str):
        return self.provider.certificate_save(self.cpf_cnpj, certificado, passowrd)

    async def certificate_get(self):
        pass

    async def certificate_delete(self):
        pass

    async def issuer_save(self):
        pass

    async def issuer_update(self):
        pass

    async def issuer_get(self):
        pass

    async def issuer_delete(self):
        pass
