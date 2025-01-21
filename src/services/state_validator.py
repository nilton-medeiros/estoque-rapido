from typing import Tuple
from src.domain.models.nome_pessoa import NomePessoa
from src.domain.models.phone_number import PhoneNumber

class StateValidator:
    """
    Centraliza a validação de dados do estado da aplicação.
    """
    @staticmethod
    def validate_user_data(user_data: dict) -> Tuple[bool, str]:
        """
        Valida os dados do usuário.
        Retorna uma tupla (is_valid, error_message).
        """
        if not isinstance(user_data, dict):
            return False, "Dados do usuário devem ser um dicionário"

        required_fields = ['id', 'name', 'email', 'profile']
        for field in required_fields:
            if field not in user_data:
                return False, f"Campo obrigatório ausente: {field}"

        if 'name' in user_data and not isinstance(user_data['name'], NomePessoa):
            return False, "Nome deve ser uma instância de NomePessoa"

        if 'phone_number' in user_data and not isinstance(user_data['phone_number'], PhoneNumber):
            return False, "Telefone deve ser uma instância de PhoneNumber"

        return True, ""

    @staticmethod
    def validate_company_data(company_data: dict) -> Tuple[bool, str]:
        """
        Valida os dados da empresa.
        """
        if not isinstance(company_data, dict):
            return False, "Dados da empresa devem ser um dicionário"

        required_fields = ['name']  # Adicione outros campos obrigatórios
        for field in required_fields:
            if field not in company_data:
                return False, f"Campo obrigatório ausente: {field}"

        return True, ""