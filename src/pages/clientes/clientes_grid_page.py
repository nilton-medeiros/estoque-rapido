# ==========================================
# src/pages/clientes/clientes_grid_page.py (ARQUIVO ORIGINAL - SIMPLIFICADO)
# ==========================================
import flet as ft
from src.domains.clientes.models import Cliente
from src.domains.clientes.controllers.grid_controller import ClienteGridController
from src.domains.clientes.views.clientes_grid_ui import ClienteGridUI


def show_clients_grid(page: ft.Page):
    """Função principal - agora é só o coordenador"""

    async def handle_action(action: str, cliente: Cliente | None):
        """Handler unificado para todas as ações"""
        if not cliente and action != "INSERT":
            return

        match action:
            case "INSERT":
                page.app_state.clear_form_data() # type: ignore [attr-defined]
                page.go('/home/clientes/form')
            case "EDIT":
                page.app_state.set_form_data(cliente.to_dict()) # type: ignore [attr-defined]
                page.go('/home/clientes/form')
            case "SOFT_DELETE":
                from src.pages.clientes import clientes_actions_page as cli_actions
                if cliente:
                    is_deleted = await cli_actions.send_to_trash(page=page, cliente=cliente)
                    if is_deleted:
                        await controller.load_clientes()

    # Configuração da página
    page.theme_mode = ft.ThemeMode.DARK
    page.data = page.route  # Armazena a rota atual em `page.data` para uso pela função `page.back()` de navegação.

    # Cria o controlador e UI
    controller = ClienteGridController(page, handle_action)
    ui = ClienteGridUI(controller)

    # Carrega dados iniciais
    page.run_task(controller.load_clientes)

    return ft.View(
        route="/home/clientes/grid",
        controls=[ui.loading_container, ui.content_area],
        appbar=ui.appbar,
        drawer=page.drawer,
        floating_action_button=ui.fab_buttons, # type: ignore [attr-defined] floating_action_button type FloatingActionButton | None, aceita sim um ft.Column()
        vertical_alignment=ft.MainAxisAlignment.START,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        padding=ft.padding.all(10)
    )
