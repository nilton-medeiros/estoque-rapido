# from dataclasses import dataclass
# from typing import Optional, Dict, Any
# from datetime import datetime, timedelta

import flet as ft

# Em construção...
class AuthManager:
    """Gerencia o estado de autenticação e sessão do usuário."""

    _instance = None

    @classmethod
    def initialize(cls, page: ft.Page):
        if cls._instance is None:
            cls._instance = cls(page)
        return cls._instance

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            raise Exception("AuthManager não foi inicializado")
        return cls._instance

    def __init__(self, page: ft.Page):
        self.page = page
        self._session_key = "current_user"


    def login(self, user_data) -> bool:
        pass