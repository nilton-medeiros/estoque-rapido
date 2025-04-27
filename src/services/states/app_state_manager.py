import logging
import flet as ft

from typing import Optional, Dict, Any
from .state_validator import StateValidator
from src.shared import MessageType, message_snackbar
from src.shared.config.user_session import refresh_the_user_session

logger = logging.getLogger(__name__)


class AppStateManager:
    """
    Gerencia o estado global da aplicação e suas atualizações.
    """

    def __init__(self, page: ft.Page):
        self.page = page
        self._state: Dict[str, Any] = {
            'usuario': {},
            'empresa': {},
            'empresa_form': {},
        }
        self._validator = StateValidator()

    @property
    def usuario(self):
        return self._state.get('usuario')

    @property
    def empresa(self):
        return self._state.get('empresa')

    @property
    def empresa_form(self):
        return self._state.get('empresa_form')

    def set_usuario(self, usuario_data: Optional[dict]) -> bool:
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
                if all(key in colors for key in ['base_color','primary', 'container', 'accent', 'appbar']):
                    try:
                        refresh_the_user_session(page=self.page, colors=colors)
                    except Exception as e:
                        # ignora: Client storage está com problemas de fábrica, na prática está salvando.
                        logger.error(f"Erro ao atualizar as cores do usuário: {str(e)}")

            self.page.pubsub.send_all("usuario_updated")
            return True

        except Exception as e:
            self.handle_error(f"Erro ao atualizar usuário: {str(e)}")
            return False

    def set_empresa(self, empresa_data: Optional[dict]) -> bool:
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
                self.handle_error(f"Erro de validação: {error}")
                return False

            self._state['empresa'] = empresa_data
            self.page.pubsub.send_all("empresa_updated")
            return True

        except Exception as e:
            self.handle_error(f"Erro ao atualizar empresa: {str(e)}")
            return False

    def set_empresa_form(self, empresa_data: Optional[dict]) -> bool:
        """
        Atualiza os dados da empresa para o formulário no estado global.
        """
        try:
            if empresa_data is None:
                self._state['empresa_form'] = {}
                self.page.pubsub.send_all("empresa_form_updated")
                return True

            is_valid, error = self._validator.validate_empresa_data(
                empresa_data)
            if not is_valid:
                self.handle_error(f"Erro de validação: {error}")
                return False

            self._state['empresa_form'] = empresa_data
            self.page.pubsub.send_all("empresa_form_updated")
            return True

        except Exception as e:
            self.handle_error(f"Erro ao atualizar empresa para o formulário: {str(e)}")
            return False

    def handle_error(self, error_message: str):
        logger.error(error_message)
        """Centraliza o tratamento de erros"""
        self.page.pubsub.send_all("error_occurred")
        message_snackbar(self.page, error_message, MessageType.ERROR)

    def clear_state(self):
        """Limpa todo o estado (útil para logout)"""
        self._state['usuario'] = {}
        self._state['empresa'] = {}
        self._state['empresa_form'] = {}
        self.page.pubsub.send_all("usuario_updated")
        self.page.pubsub.send_all("empresa_updated")
        self.page.pubsub.send_all("empresa_form_updated")

    def clear_empresa_data(self):
        """Limpa os dados da empresa (útil para logout)"""
        self._state['empresa'] = {}
        self.page.pubsub.send_all("empresa_updated")

    def clear_empresa_form_data(self):
        """Limpa os dados da empresa para formulário (útil para logout)"""
        self._state['empresa_form'] = {}
        self.page.pubsub.send_all("empresa_form_updated")
