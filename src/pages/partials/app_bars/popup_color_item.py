import logging
import flet as ft

import src.domains.usuarios.controllers.usuarios_controllers as user_controllers
from src.shared.config import get_theme_colors
from src.shared.utils.messages import message_snackbar, MessageType

logger = logging.getLogger(__name__)


class PopupColorItem(ft.PopupMenuItem):
    def __init__(self, color: str, name: str):
        super().__init__()
        # super trás o self.page por herança
        self.content = ft.Row(
            controls=[
                ft.Icon(name=ft.Icons.COLOR_LENS_OUTLINED, color=color),
                ft.Text(name),
            ],
        )
        self.on_click = self.seed_color_changed
        self.theme_color: str = color

    def seed_color_changed(self, e):
        page = self.page
        if not page:
            logger.warning("A página não está mais disponível. Ação de mudança de cor ignorada.")
            return

        # 1. Atualiza o tema da UI imediatamente para um feedback visual rápido.
        page.theme = page.dark_theme = ft.Theme(color_scheme_seed=self.theme_color)

        # 2. Atualiza a cor no banco de dados.
        usuario_logado = page.app_state.usuario  # type: ignore [attr-defined]
        try:
            result = user_controllers.handle_update_user_colors(id=usuario_logado['id'], theme_color=self.theme_color)

            if result["status"] == "error":
                message_snackbar(page=page, message=result["message"], message_type=MessageType.ERROR)
                return

            # 3. Atualiza o estado local do usuário.
            usuario_logado['theme_color'] = self.theme_color
            page.app_state.set_usuario(usuario_logado)  # type: ignore [attr-defined]

        except Exception as ex:
            logger.error(f"Erro ao atualizar a cor do tema: {ex}")
            message_snackbar(page=page, message=f"Erro ao atualizar a cor do tema: {ex}", message_type=MessageType.ERROR)

        page.update()
