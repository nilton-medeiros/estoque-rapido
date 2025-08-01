import logging
import flet as ft

from src.domains.shared.context.session import get_current_user
import src.domains.usuarios.controllers.usuarios_controllers as user_controllers
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
        page.theme = page.dark_theme = ft.Theme(color_scheme_seed=self.theme_color) # type: ignore [attr-defined]


        try:
            # 2. Atualiza a cor no banco de dados.
            current_user = get_current_user(page)
            if not current_user:
                logger.warning("Usuário não encontrado. Ação de mudança de cor ignorada.")
                message_snackbar(page=page, message="Usuário não encontrado. Ação de mudança de cor ignorada.", message_type=MessageType.ERROR)
                return

            result = user_controllers.handle_update_user_colors(id=current_user.id, theme_color=self.theme_color)  # type: ignore [attr-defined]

            if result["status"] == "error":
                message_snackbar(page=page, message=result["message"], message_type=MessageType.ERROR)
                return

            # 3. Atualiza o estado local do usuário.
            current_user.theme_color = self.theme_color
            page.app_state.set_usuario(current_user)  # type: ignore [attr-defined]

        except Exception as ex:
            logger.error(f"Erro ao atualizar a cor do tema: {ex}")
            message_snackbar(page=page, message=f"Erro ao atualizar a cor do tema: {ex}", message_type=MessageType.ERROR)

        page.update()
