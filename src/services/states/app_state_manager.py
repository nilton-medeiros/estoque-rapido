import flet as ft
from typing import Optional, Dict, Any

from .state_validator import StateValidator
from src.utils.message_snackbar import MessageType, message_snackbar


class AppStateManager:
    """
    Gerencia o estado global da aplicação e suas atualizações.
    """

    def __init__(self, page: ft.Page):
        self.page = page
        self._state: Dict[str, Any] = {
            'user': None,
            'company': None
        }
        self._validator = StateValidator()

    @property
    def user(self):
        return self._state.get('user')

    @property
    def company(self):
        return self._state.get('company')

    async def set_user(self, user_data: Optional[dict]) -> bool:
        """
        Atualiza os dados do usuário no estado global.
        """
        try:
            if user_data is None:
                print(":")
                print("================================================================================")
                print(f"Debug | Em set_user, user_data é None, publicando logout")
                print("================================================================================")

                self._state['user'] = None
                self.page.pubsub.send_all("user_logout")
                return True

            is_valid, error = self._validator.validate_user_data(user_data)
            if not is_valid:
                await self.handle_error(error)
                print(":")
                print("================================================================================")
                print(f"Debug | Em set_user, user_data não é válido, retornado False")
                print("================================================================================")
                return False

            self._state['user'] = user_data
            self.page.pubsub.send_all("user_updated")
            return True

        except Exception as e:
            await self.handle_error(f"Erro ao atualizar usuário: {str(e)}")
            return False

    async def set_company(self, company_data: Optional[dict]) -> bool:
        """
        Atualiza os dados da empresa no estado global.
        """
        try:
            if company_data is None:
                self._state['company'] = None
                self.page.pubsub.send_all("company_updated")
                return True

            is_valid, error = self._validator.validate_company_data(
                company_data)
            if not is_valid:
                await self.handle_error(error)
                return False

            self._state['company'] = company_data
            self.page.pubsub.send_all("company_updated")
            return True

        except Exception as e:
            await self.handle_error(f"Erro ao atualizar empresa: {str(e)}")
            return False

    async def handle_error(self, error_message: str):
        """Centraliza o tratamento de erros"""
        print(f"Erro: {error_message}")  # Log para debug
        self.page.pubsub.send_all("error_occurred")
        await message_snackbar(self.page, error_message, MessageType.ERROR)

    def clear_state(self):
        """Limpa todo o estado (útil para logout)"""
        self._state['user'] = None
        self._state['company'] = None
        self.page.pubsub.send_all("user_updated")
        self.page.pubsub.send_all("company_updated")