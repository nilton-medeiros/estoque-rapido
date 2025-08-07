import flet as ft

from src.domains.pedidos.models import Pedido
from src.domains.pedidos.models.pedidos_subclass import DeliveryStatus
from src.domains.shared.models.registration_status import RegistrationStatus
from src.shared.utils.time_zone import format_datetime_to_utc_minus_3

class OrderCard:
    """Componente reutilizável para card de pedido"""

    @staticmethod
    def create(pedido: Pedido, on_action_callback) -> ft.Card:
        """Cria um card individual do pedido"""
        return ft.Card(
            content=ft.Container(
                padding=15,
                content=ft.Column([
                    OrderCard._create_card_header(pedido, on_action_callback),
                    ft.Text(f"Total do pedido: {pedido.total_amount}", weight=ft.FontWeight.BOLD,
                           theme_style=ft.TextThemeStyle.BODY_MEDIUM,
                           no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Text(pedido.client.get("name", "Cliente não informado"),
                           theme_style=ft.TextThemeStyle.BODY_SMALL,
                           no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Text(pedido.client.get("phone"),
                           theme_style=ft.TextThemeStyle.BODY_SMALL),
                    OrderCard._create_status_row(pedido),
                ])
            ),
            margin=ft.margin.all(5),
            col={"xs": 12, "sm": 6, "md": 4, "lg": 3}
        )

    @staticmethod
    def _create_card_header(pedido: Pedido, on_action_callback) -> ft.Row:
        """Cria o cabeçalho do card com imagem e menu"""
        return ft.Row(
            [
                ft.Text(f"Nº: {pedido.order_number}",
                    weight=ft.FontWeight.BOLD,
                    theme_style=ft.TextThemeStyle.BODY_LARGE),
                ft.Container(expand=True),  # Spacer
                ft.Text(
                    f"Data: {format_datetime_to_utc_minus_3(pedido.order_date)}",
                    weight=ft.FontWeight.NORMAL,
                    theme_style=ft.TextThemeStyle.BODY_MEDIUM),
                OrderCard._create_action_menu(pedido, on_action_callback),
            ],
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    @staticmethod
    def _create_action_menu(pedido: Pedido, on_action_callback) -> ft.Container:
        """Cria o menu de ações do pedido"""
        return ft.Container(
            content=ft.PopupMenuButton(
                icon=ft.Icons.MORE_VERT,
                tooltip="Mais Ações",
                items=[
                    ft.PopupMenuItem(
                        text="Editar pedido",
                        icon=ft.Icons.EDIT_NOTE_OUTLINED,
                        on_click=lambda e: on_action_callback("EDIT", pedido)
                    ),
                    ft.PopupMenuItem(
                        text="Itens do pedido",
                        icon=ft.Icons.FORMAT_LIST_NUMBERED,
                        on_click=lambda e: on_action_callback("ITEM_LIST", pedido)
                    ),
                    ft.PopupMenuItem(
                        text="Excluir pedido",
                        icon=ft.Icons.DELETE_OUTLINE,
                        on_click=lambda e: on_action_callback("SOFT_DELETE", pedido)
                    ),
                ],
            ),
        )

    @staticmethod
    def _create_status_row(pedido: Pedido) -> ft.Row:
        """Cria a linha com status"""
        return ft.Row([
            ft.Text(
                value=pedido.status.default_label,
                theme_style=ft.TextThemeStyle.BODY_SMALL,
                color=ft.Colors.GREEN if pedido.status == RegistrationStatus.ACTIVE else ft.Colors.RED,
            ),
            ft.Text(
                value=f"Entrega: {pedido.delivery_status.value}",
                theme_style=ft.TextThemeStyle.BODY_SMALL,
                color=OrderCard._get_status_color(pedido.delivery_status),
            )
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    @staticmethod
    def _get_status_color(status: DeliveryStatus) -> ft.Colors:
        """Determina a cor baseada no status"""
        match status:
            case DeliveryStatus.DELIVERED:
                return ft.Colors.BLUE
            case DeliveryStatus.IN_TRANSIT:
                return ft.Colors.GREEN
            case DeliveryStatus.PENDING:
                return ft.Colors.ORANGE
            case DeliveryStatus.CANCELED:
                return ft.Colors.RED
            case _:
                return ft.Colors.GREY
