from typing import Tuple

from src.domains.shared import NomePessoa, PhoneNumber


class StateValidator:
    """
    Centraliza a validação de dados do estado da aplicação.
    """
    @staticmethod
    def validate_usuario_data(usuario_data: dict) -> Tuple[bool, str]:
        """
        Valida os dados do usuário.
        Retorna uma tupla (is_valid, error_message).
        """
        if not isinstance(usuario_data, dict):
            return False, "Dados do usuário devem ser um dicionário"

        required_fields = ['id', 'name', 'email', 'phone_number', 'profile']
        for field in required_fields:
            if field not in usuario_data:
                return False, f"Campo obrigatório ausente: {field}"

        if 'name' in usuario_data and not isinstance(usuario_data['name'], NomePessoa):
            return False, "Nome deve ser uma instância de NomePessoa"

        if 'phone_number' in usuario_data and not isinstance(usuario_data['phone_number'], PhoneNumber):
            return False, "Telefone deve ser uma instância de PhoneNumber"

        return True, ""

    @staticmethod
    def validate_empresa_data(company_data: dict) -> Tuple[bool, str]:
        """
        Valida os dados da empresa.
        """
        if not isinstance(company_data, dict):
            return False, "Dados da empresa devem ser um dicionário"

        # Campos obrigatórios da entidade Empresa
        required_fields = ['id', 'corporate_name', 'email']
        for field in required_fields:
            if field not in company_data:
                return False, f"Campo obrigatório ausente: {field}"

        return True, ""

    @staticmethod
    def validate_form_data(form_data: dict, required_fields: list[str]) -> Tuple[bool, str]:
        """
        Valida os dados de form_data.
        Retorna uma tupla (is_valid, error_message).
        """
        if not isinstance(form_data, dict):
            return False, "Dados do formulário devem ser um dicionário"

        if not isinstance(required_fields, list):
            return True, ""  # Se não passou a lista, não valida nada

        # Campos obrigatórios da entidade em Dados de formulário
        for field in required_fields:
            if field not in form_data:
                return False, f"Campo obrigatório ausente: {field}"

        return True, ""
