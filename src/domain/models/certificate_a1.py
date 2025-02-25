from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class CertificateA1:
    """Certificado digital (PFX ou P12)."""
    serial_number: Optional[str] = None  # Número de série do certificado
    issuer_name: Optional[str] = None  # Emissor do certificado
    # Data e hora de início da validade do certificado
    not_valid_before: Optional[datetime] = None
    # Data e hora do fim da validade do certificado
    not_valid_after: Optional[datetime] = None
    # O thumbprint (ou impressão digital) de um certificado digital A1 é uma representação única e compacta do certificado
    thumbprint: Optional[str] = None
    subject_name: Optional[str] = None
    cpf_cnpj: Optional[str] = None
    nome_razao_social: Optional[str] = None
    _encrypted_password: str = None  # Senha do certificado digital criptografada

    def _encrypt(self, password: str) -> str:
        """
        Criptografa a senha do certificado digital.

        Args:
            password (str): Senha do certificado digital.
        """
        # Usar a chave para criptografar a senha do certificado digital
        cipher_text = self._cipher_suite.encrypt(password.encode())
        return cipher_text

    def _decrypt(self) -> str:
        """
        Descriptografa a senha do certificado digital.

        Returns:
            str: Senha do certificado digital descriptografada.
        """
        # Usar a chave para descriptografar a senha
        cipher_text = self._encrypted_password
        plain_text = self._cipher_suite.decrypt(cipher_text).decode()
        return plain_text

    @property
    def password(self) -> Optional[str]:
        """
        Getter para a senha do certificado.

        Returns:
            Optional[str]: Senha descriptografada ou None se não houver senha.
        """
        if self._encrypted_password is None:
            return None
        return self._decrypt()

    @password.setter
    def password(self, password: Optional[str]) -> None:
        """
        Setter para a senha do certificado.

        Args:
            password (Optional[str]): Senha a ser criptografada e armazenada.
        """
        if password is None:
            self._encrypted_password = None
        else:
            self._encrypted_password = self._encrypt(password)
