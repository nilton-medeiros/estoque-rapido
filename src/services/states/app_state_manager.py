import logging
import flet as ft

from typing import Any
from .state_validator import StateValidator
from src.shared import MessageType, message_snackbar

logger = logging.getLogger(__name__)


class AppStateManager:
    """
    Gerencia o estado global da aplicação e suas atualizações.
    """

    def __init__(self, page: ft.Page):
        self.page = page
        self._state: dict[str, Any] = {
            'usuario': {},  # Usuário logado
            'empresa': {},  # Empresa logada
            'form_data': {},  # Armazenamento temporário de dados para preenchimento de formulários em entidades de domínio.
        }
        self._validator = StateValidator()

    @property
    def usuario(self):
        return self._state.get('usuario')

    @property
    def empresa(self):
        return self._state.get('empresa')

    @property
    def form_data(self):
        return self._state.get('form_data')

    def set_usuario(self, usuario_data: dict | None) -> bool:
        """
        Atualiza os dados do usuário no estado global.
        """
        try:
            if usuario_data is None:
                self._state['usuario'] = {}
                self.page.pubsub.send_all("usuario_logout")
                return True

            is_valid, error = self._validator.validate_usuario_data(
                usuario_data)
            if not is_valid:
                self.handle_error(error)
                return False

            self._state['usuario'] = usuario_data

            # Atualiza as cores do usuário
            if colors := usuario_data.get('user_colors', {}):
                if all(key in colors for key in ['base_color', 'primary', 'container', 'accent', 'appbar']):
                    self.page.session.set("user_colors", colors)

            self.page.pubsub.send_all("usuario_updated")
            return True

        except Exception as e:
            self.handle_error(f"Erro ao atualizar usuário: {str(e)}")
            return False

    def set_empresa(self, empresa_data: dict | None) -> bool:
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
        self._state['usuario'] = {}
        self._state['empresa'] = {}
        self._state['form_data'] = {}
        self.page.pubsub.send_all("usuario_updated")
        self.page.pubsub.send_all("empresa_updated")
        # self.page.pubsub.send_all("form_data_updated")

    def clear_empresa_data(self):
        """Limpa os dados da empresa (útil para logout)"""
        self._state['empresa'] = {}
        self.page.pubsub.send_all("empresa_updated")

    def clear_form_data(self):
        """Limpa os dados da empresa para formulário (útil para logout)"""
        self._state['form_data'] = {}
        # self.page.pubsub.send_all("form_data_updated")
