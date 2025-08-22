import logging
import flet as ft

from typing import Any, Optional, TypedDict
from src.domains.usuarios.models.usuarios_model import Usuario

from src.shared.config import get_theme_colors

from .state_validator import StateValidator
from src.shared.utils import MessageType, message_snackbar

logger = logging.getLogger(__name__)


class EmpresaStateDict(TypedDict, total=False): # total=False porque o estado pode começar vazio
    """Define a estrutura do dicionário de estado da empresa para a UI."""
    id: str
    corporate_name: str
    trade_name: str
    store_name: str
    cnpj: dict[str, Any] # ou str, dependendo de como é armazenado
    email: str
    # Adicione outros campos que são frequentemente acessados no estado

class AppStateDict(TypedDict):
    """Define a estrutura do dicionário de estado para melhor type-hinting."""
    usuario: Optional[Usuario]
    empresa: EmpresaStateDict
    form_data: dict[str, Any]


class AppStateManager:
    """
    Gerencia o estado global da aplicação e suas atualizações.
    """
    def __init__(self, page: ft.Page):
        self.page = page
        self._state: AppStateDict = {
            'usuario': None,  # Usuário logado obj
            'empresa': {},  # Empresa logada dict (usando EmpresaStateDict)
            'form_data': {},  # Armazenamento temporário de dados para preenchimento de formulários em entidades de domínio.
        }
        self._validator = StateValidator()
        self.user_name_text: ft.Text = ft.Text("Nenhum Usuário logado")
        self.company_name_text_btn: ft.TextButton = ft.TextButton(
            text="NENHUMA EMPRESA SELECIONADA",
            style=ft.ButtonStyle(
                alignment=ft.alignment.center,
                text_style=ft.TextStyle(
                    color=ft.Colors.WHITE, size=14, weight=ft.FontWeight.NORMAL)
            ),
            tooltip="Clique aqui e preencha os dados da empresa"
        )

    @property
    def usuario(self):
        return self._state['usuario']

    @property
    def empresa(self):
        return self._state['empresa']

    @property
    def form_data(self):
        return self._state['form_data']

    def set_usuario(self, current_user: Usuario) -> bool:
        """
        Atualiza os dados do usuário no estado global.
        """
        try:
            is_valid, error = self._validator.validate_usuario_data(current_user)
            if not is_valid:
                self.handle_error(error)
                return False

            self._state['usuario'] = current_user

            # Atualiza as cores do usuário

            theme_colors: dict = get_theme_colors(current_user.theme_color)
            self.page.session.set("user_authenticaded", True)
            self.page.session.set("theme_colors", theme_colors)
            self.page.pubsub.send_all("usuario_updated")
            return True

        except Exception as e:
            self.handle_error(f"Erro ao atualizar usuário: {str(e)}")
            return False

    def set_empresa(self, empresa_data: EmpresaStateDict | None) -> bool:
        """
        Atualiza os dados da empresa no estado global.
        """
        try:
            if empresa_data is None:
                self._state['empresa'] = {}
                self.page.pubsub.send_all("empresa_updated")
                return True

            is_valid, error = self._validator.validate_empresa_data(
                empresa_data)
            if not is_valid:
                self.handle_error(f"set_empresa(). Erro de validação: {error}")
                return False

            self._state['empresa'] = empresa_data
            self.page.pubsub.send_all("empresa_updated")
            return True

        except Exception as e:
            self.handle_error(f"Erro ao atualizar empresa: {str(e)}")
            return False

    def set_form_data(self, form_data: dict | None, required_fields: list[str] = []) -> bool:
        """
        Atualiza os dados da empresa para o formulário no estado global.
        """
        try:
            if form_data is None:
                self._state['form_data'] = {}
                return True

            is_valid, error = self._validator.validate_form_data(
                form_data, required_fields)
            if not is_valid:
                self.handle_error(f"set_form_data(). Erro de validação: {error}")
                return False

            self._state['form_data'] = form_data
            return True

        except Exception as e:
            self.handle_error(
                f"Erro ao atualizar dados para o formulário: {str(e)}")
            return False

    def handle_error(self, error_message: str):
        logger.error(error_message)
        """Centraliza o tratamento de erros"""
        # self.page.pubsub.send_all("error_occurred")
        message_snackbar(self.page, error_message, MessageType.ERROR)

    def clear_states(self):
        """Limpa todo o estado (útil para logout)"""
        self._state['usuario'] = None
        self._state['empresa'] = {}
        self._state['form_data'] = {}
        self.page.pubsub.send_all("usuario_updated")
        self.page.pubsub.send_all("empresa_updated")
        self.page.session.clear()

    def clear_empresa_data(self):
        """Limpa os dados da empresa (útil para logout)"""
        self._state['empresa'] = {}
        self.page.pubsub.send_all("empresa_updated")

    def clear_form_data(self):
        """Limpa os dados da empresa para formulário (útil para logout)"""
        self._state['form_data'] = {}
