from .app_state_manager import AppStateManager

class AppState:
    """
    Mantém compatibilidade com o código existente enquanto usa o novo AppStateManager.
    """
    def __init__(self, page):
        self.page = page
        self._state_manager = AppStateManager(page)

    @property
    def user(self):
        return self._state_manager.user

    @user.setter
    def user(self, value):
        # Usando asyncio.run não é a melhor prática, mas mantém compatibilidade
        import asyncio
        asyncio.run(self._state_manager.set_user(value))

    @property
    def company(self):
        return self._state_manager.company

    @company.setter
    def company(self, value):
        import asyncio
        asyncio.run(self._state_manager.set_company(value))