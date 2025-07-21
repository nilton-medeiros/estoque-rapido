from typing import Tuple

from src.domains.shared import NomePessoa, PhoneNumber
from src.domains.usuarios.models.usuarios_model import Usuario


class StateValidator:
    """
    Centraliza a validação de dados do estado da aplicação.
    """
    @staticmethod
    def validate_usuario_data(current_user: Usuario) -> Tuple[bool, str]:
        """
        Valida os dados do usuário.
        Retorna uma tupla (is_valid, error_message).
        """
        if not isinstance(current_user, Usuario):
            return False, "O argumento current_user deve ser uma instância de 'Usuario'"
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
