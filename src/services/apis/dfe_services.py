from src.services.contracts.dfe_provider import DFeProvider


class DFeServices:
    def __init__(self, provider: DFeProvider, cpf_cnpj: str):
        self.provider = provider
        self.cpf_cnpj = cpf_cnpj

    async def certificate_save(self, certificado: bytes, password: str):
        return self.provider.certificate_save(self.cpf_cnpj, certificado, password)

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
