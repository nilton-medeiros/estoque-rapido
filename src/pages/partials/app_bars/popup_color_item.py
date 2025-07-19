import logging
import flet as ft

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
        # Atualiza a tela com o novo thema de cores com a cor base do usuário
        # super() trás o self.page por herança
        self.page.theme = self.page.dark_theme = ft.Theme(color_scheme_seed=self.theme_color)  # type: ignore [attr-defined]
        usuario_logado = self.page.app_state.usuario  # type: ignore [attr-defined]
        msg_error = None

        try:
            result = user_controllers.handle_update_user_colors(id=usuario_logado['id'], theme_color=self.theme_color)

            if result["status"] == "error":
                msg_error = result["message"]
                message_snackbar(page=self.page, message=msg_error,  # type: ignore [attr-defined]
                                 message_type=MessageType.ERROR)
                return  # Não continua se houve erro

            # Atualiza o estado local ANTES de atualizar a UI globalmente
            user_dict = self.page.app_state.usuario  # type: ignore
            # Atualiza a cor de thema preferencial no dicionário
            user_dict['theme_color'] = self.theme_color
            self.page.app_state.set_usuario(user_dict)  # type: ignore [attr-defined]

        except ValueError as e:
            logger.error(str(e))
            msg_error = f"Erro: {str(e)}"
        except RuntimeError as e:
            logger.error(str(e))
            # Provavelmente um erro de digitação, deveria ser "Erro na atualização"
            msg_error = f"Erro no upload: {str(e)}"

        if msg_error:
            message_snackbar(page=self.page, message=msg_error,  # type: ignore
                             message_type=MessageType.ERROR)
        self.page.update()  # type: ignore
