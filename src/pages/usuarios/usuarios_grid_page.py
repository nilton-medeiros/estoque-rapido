import flet as ft
from src.domains.usuarios.models.usuario_model import Usuario
from src.domains.usuarios.controllers.grid_controller import UsuarioGridController
from src.domains.usuarios.views.usuarios_grid_ui import UsuarioGridUI
from src.shared.components.dialogs.change_password_dialog import ChangePasswordDialog


def user_change_password(page: ft.Page, usuario: Usuario):
    password_dialog = ChangePasswordDialog(page=page, user=usuario)
    password_dialog.show()

def show_users_grid(page: ft.Page):
    async def handle_action(action: str, usuario: Usuario | None):
        """Handler unificado para todas as ações"""
        match action:
            case "INSERT":
                page.app_state.clear_form_data() # type: ignore [attr-defined]
                page.go('/home/usuarios/form')
            case "EDIT":
                if usuario:
                    page.app_state.set_form_data(usuario.to_dict()) # type: ignore [attr-defined]
                    page.go('/home/usuarios/form')
            case "CHANGE_PASSWORD":
                if usuario:
                    user_change_password(page, usuario)
            case "SOFT_DELETE":
                if usuario:
                    from src.pages.usuarios import usuarios_actions_page as user_actions
                    is_deleted = await user_actions.send_to_trash(page=page, usuario=usuario)
                    if is_deleted:
                        await controller.load_usuarios()

    # Configuração da página
    page.theme_mode = ft.ThemeMode.DARK
    page.data = "/home/usuarios/grid"

    # Cria o controlador e UI
    controller = UsuarioGridController(page, handle_action)
    ui = UsuarioGridUI(controller)

    # Carrega dados iniciais
    page.run_task(controller.load_usuarios)

    return ft.View(
        route="/home/usuarios/grid",
        controls=[ui.loading_container, ui.content_area],
        appbar=ui.appbar,
        floating_action_button=ui.fab_buttons, # type: ignore [attr-defined] floating_action_button type FloatingActionButton | None : Aceita sim um ft.Column()
        vertical_alignment=ft.MainAxisAlignment.START,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        padding=ft.padding.all(10)
    )
