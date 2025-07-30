import flet as ft

from src.domains.formas_pagamento.controllers.grid_controller import FormaPagamentoGridController
from src.domains.formas_pagamento.models import FormaPagamento
from src.domains.formas_pagamento.views.formas_pagamento_grid_ui import FormasPagamentoGridUI


def show_formas_pagamento_grid(page: ft.Page) -> ft.View:
    """Função coordenadora da página de Formas de Pagamento."""
    async def handle_action(action: str, forma_pagamento: FormaPagamento | None):
        """Handler unificado para todas as ações"""
        if not forma_pagamento and action != "INSERT":
            return

        match action:
            case "INSERT":
                page.app_state.clear_form_data()  # type: ignore [attr-defined]
                page.go('/home/formasdepagamento/form')
            case "EDIT":
                if forma_pagamento:
                    page.app_state.set_form_data(forma_pagamento.to_dict()) # type: ignore [attr-defined]
                    page.go("/home/formasdepagamento/form")
            case "SOFT_DELETE":
                if forma_pagamento:
                    from src.pages.formas_pagamento.formas_pagamento_actions_page import send_to_trash
                    is_deleted = await send_to_trash(page, forma_pagamento)
                    if is_deleted:
                        await controller.load_formas_pagamento()

    # Configuração da página
    page.theme_mode = ft.ThemeMode.DARK
    page.data = page.route

    # Cria o ontrolador e UI
    controller = FormaPagamentoGridController(page, handle_action)
    ui = FormasPagamentoGridUI(controller)

    # Carrega dados iniciais
    page.run_task(controller.load_formas_pagamento)

    return ft.View(
        route="/home/formasdepagamento/grid",
        controls=[ui.loading_container, ui.content_area],
        appbar=ui.appbar,
        drawer=page.drawer,
        # floating_action_button type FloatingActionButton | None aceita sim ft.Column()
        floating_action_button=ui.fab_buttons, # type: ignore [attr-defined]
        vertical_alignment=ft.MainAxisAlignment.START,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        padding=ft.padding.all(10)
    )
