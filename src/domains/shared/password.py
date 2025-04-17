from cryptography.fernet import Fernet
from dotenv import load_dotenv
import os


class Password:
    def __init__(self, value: str):
        load_dotenv()
        key = os.getenv("FERNET_KEY")
        if not key:
            raise ValueError("FERNET_KEY não encontrada no ambiente.")
        try:
            self._cipher_suite = Fernet(
                key.encode() if isinstance(key, str) else key)
        except Exception as e:
            raise ValueError(f"Chave Fernet inválida: {e}")

        if not isinstance(value, str):
            raise TypeError("A senha deve ser uma string.")

        self.value = self._encrypt(value)

    def __eq__(self, other):
        if not isinstance(other, Password):
            return False
        return self.decrypted == other.decrypted

    def __str__(self):
        return "[Encrypted Password]"

    def _encrypt(self, value: str) -> bytes:
        """
        Criptografa a senha.

        Args:
            value (str): Senha descriptografada.

        Returns:
            bytes: Senha criptografada.
        """
        return self._cipher_suite.encrypt(value.encode())

    @property
    def decrypted(self) -> str:
        """
        Descriptografa a senha.

        Returns:
            str: Senha descriptografada.
        """
        try:
            return self._cipher_suite.decrypt(self.value).decode()
        except Exception as e:
            raise ValueError(f"Erro ao descriptografar a senha: {e}")

    @classmethod
    def from_dict(cls, data) -> 'Password':
        """
        Cria uma instância de Password a partir de um valor (dicionário ou bytes).
        """
        # Se for bytes (vindo diretamente do Firestore)
        if isinstance(data, bytes):
            return cls.from_encrypted(data)

        # Se for dicionário com chave 'value'
        elif isinstance(data, dict) and 'value' in data:
            value = data['value']
            if isinstance(value, bytes):
                return cls.from_encrypted(value)
            elif isinstance(value, str):
                return cls(value)

        # Se for string (senha em texto plano)
        elif isinstance(data, str):
            return cls(data)

        raise ValueError("Formato inválido para criar Password.")

    @staticmethod
    def from_encrypted(encrypted_value: bytes) -> 'Password':
        """
        Cria uma instância de Password a partir de um valor criptografado.

        Args:
            encrypted_value (bytes): Senha criptografada.

        Returns:
            Password: Instância da classe com o valor criptografado.
        """
        instance = Password.__new__(
            Password)  # Cria uma instância sem chamar __init__
        load_dotenv()
        key = os.getenv("FERNET_KEY")
        if not key:
            raise ValueError("FERNET_KEY não encontrada no ambiente.")
        instance._cipher_suite = Fernet(
            key.encode() if isinstance(key, str) else key)
        instance.value = encrypted_value
        return instance


"""
# Exemplo de uso
if __name__ == "__main__":
    # Supondo que FERNET_KEY está definida no .env
    pwd = Password("minha_senha_secreta")
    print(pwd)  # [Encrypted Password]
    print(pwd.decrypted)  # minha_senha_secreta
    pwd2 = Password("minha_senha_secreta")
    print(pwd == pwd2)  # True
"""
