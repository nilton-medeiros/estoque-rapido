
class DomainException(Exception):
    """Base exception for all domain exceptions"""
    def __init__(self, message="Erro no domínio da aplicação"):
        self.message = message
        super().__init__(self.message)


class AuthenticationException(DomainException):
    """Exception for authentication failures"""
    def __init__(self, message="Erro de autenticação"):
        self.message = message
        super().__init__(self.message)


class UserNotFoundException(AuthenticationException):
    """Exception when user is not found"""
    def __init__(self, message="Usuário não encontrado"):
        self.message = message
        super().__init__(self.message)


class InvalidCredentialsException(AuthenticationException):
    """Exception for invalid credentials"""
    def __init__(self, message="Credenciais inválidas"):
        self.message = message
        super().__init__(self.message)