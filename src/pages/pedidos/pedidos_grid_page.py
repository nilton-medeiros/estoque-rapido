import flet as ft

from src.domains.pedidos.controllers.grid_controller import PedidoGridController
from src.domains.pedidos.models import Pedido
from src.domains.pedidos.models.pedidos_subclass import DeliveryStatus
from src.domains.pedidos.views.pedidos_grid_ui import PedidoGridUI
from src.shared.utils.messages import show_banner


def show_orders_grid(page: ft.Page):
    """Função coordenadora da página de Pedidos."""

    async def handle_action(action: str, pedido: Pedido | None):
        """Handler unificado para todas as ações"""
        if not pedido and action != "INSERT":
            return

        match action:
            case "INSERT":
                page.app_state.clear_form_data() # type: ignore [attr-defined]
                page.go('/home/pedidos/form')
            case "EDIT":
                if pedido:
                    page.app_state.set_form_data(pedido.to_dict()) # type: ignore [attr-defined]"
                    page.go("/home/pedidos/form")
            case "ITEM_LIST":
                if pedido:
                    from src.pages.pedidos import pedidos_actions_page as order_actions
                    order_actions.show_orders_items_grid(page, pedido.items)
            case "SOFT_DELETE":
                if pedido:
                    if pedido.delivery_status == DeliveryStatus.DELIVERED:
                        show_banner(page, "Não é possível deletar um pedido já entregue.")
                        return
                    from src.pages.pedidos import pedidos_actions_page as order_actions
                    is_deleted = await order_actions.send_to_trash(page, pedido)
                    if is_deleted:
                        await controller.load_pedidos()

    # Configuração da página
    page.theme_mode = ft.ThemeMode.DARK
    page.data = page.route

    # Cria o ontrolador e UI
    controller = PedidoGridController(page, handle_action)
    ui = PedidoGridUI(controller)

    # Carrega dados iniciais
    page.run_task(controller.load_pedidos)

    return ft.View(
        route='/home/pedidos/grid',
        controls=[ui.loading_container, ui.content_area],
        appbar=ui.appbar,
        drawer=page.drawer,
        floating_action_button=ui.fab_buttons, # type: ignore [attr-defined] floating_action_button type FloatingActionButton | None, aceita sim um ft.Column()
        vertical_alignment=ft.MainAxisAlignment.START,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        padding=ft.padding.all(10),
    )
