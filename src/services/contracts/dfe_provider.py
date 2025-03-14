from abc import ABC, abstractmethod

from src.domains.empresas import CertificateA1, Empresa

class DFeProvider(ABC):
    """Classe base abstrata que define o contrato para operações de repositório de usuários."""

    @abstractmethod
    async def certificate_save(self, cpf_cnpj: str, certificate: bytes, password: str) -> CertificateA1:
        """
        Cadastra ou atualiza um certificado digital e vincula a empresa emitente,
        para que possa iniciar a emissão de notas.
        """
        raise NotImplementedError("Este método deve ser implementado pela subclasse")

    @abstractmethod
    async def certificate_get(self, cpf_cnpj: str) -> CertificateA1:
        """Consulta um certificado digital pelo documento vinculado a empresa emitente."""
        raise NotImplementedError("Este método deve ser implementado pela subclasse")

    @abstractmethod
    async def certificate_delete(self, cpf_cnpj: str) -> bool:
        """Exclui um certificado digital pelo documento vinculado a empresa emitente."""
        raise NotImplementedError("Este método deve ser implementado pela subclasse")


    @abstractmethod
    async def company_save(self, issuer: Empresa) -> str:
        """Cadastra uma nova empresa (emitente/prestador) no Provedor DFe."""
        raise NotImplementedError("Este método deve ser implementado pela subclasse")


    @abstractmethod
    async def company_update(self, issuer: Empresa) -> str:
        """Altera o cadastro de uma empresa (emitente/prestador) no Provedor DFe."""
        raise NotImplementedError("Este método deve ser implementado pela subclasse")

    @abstractmethod
    async def company_get(self, cpf_cnpj: str) -> Empresa:
        """Consulta uma empresa (emitente/prestador) pelo seu documento."""
        raise NotImplementedError("Este método deve ser implementado pela subclasse")

    @abstractmethod
    async def company_delete(self, cpf_cnpj: str) -> bool:
        """Exclui uma empresa (emitente/prestador) no Provedor de DFe."""
        raise NotImplementedError("Este método deve ser implementado pela subclasse")
