# ==========================================
# src/pages/produtos/produtos_grid_page.py (ARQUIVO ORIGINAL - SIMPLIFICADO)
# ==========================================
import flet as ft
from src.domains.produtos.models.produtos_model import Produto
from src.domains.produtos.controllers.grid_controller import ProdutoGridController
from src.domains.produtos.views.produtos_grid_ui import ProdutoGridUI


def show_products_grid(page: ft.Page):
    """Função principal - agora é só o coordenador"""

    async def handle_action(action: str, produto: Produto | None):
        """Handler unificado para todas as ações"""
        match action:
            case "INSERT":
                page.app_state.clear_form_data() # type: ignore [attr-defined]
                page.go('/home/produtos/form')
            case "EDIT":
                if produto:
                    page.app_state.set_form_data(produto.to_dict()) # type: ignore [attr-defined]
                    page.go('/home/produtos/form')
            case "SOFT_DELETE":
                if produto:
                    from src.pages.produtos import produtos_actions_page as pro_actions
                    is_deleted = await pro_actions.send_to_trash(page=page, produto=produto)
                    if is_deleted:
                        await controller.load_produtos()

    # Configuração da página
    page.theme_mode = ft.ThemeMode.DARK
    page.data = "/home/produtos/grid"

    # Cria o controlador e UI
    controller = ProdutoGridController(page, handle_action)
    ui = ProdutoGridUI(controller)

    # Carrega dados iniciais
    page.run_task(controller.load_produtos)

    return ft.View(
        route="/home/produtos/grid",
        controls=[ui.loading_container, ui.content_area],
        appbar=ui.appbar,
        floating_action_button=ui.fab_buttons, # type: ignore [attr-defined] floating_action_button type FloatingActionButton | None aceita sim um ft.Column()
        vertical_alignment=ft.MainAxisAlignment.START,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        padding=ft.padding.all(10)
    )
