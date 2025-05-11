import flet as ft
from enum import Enum


class MessageType(Enum):
    SUCCESS = ("success", ft.Colors.GREEN, ft.Colors.GREEN_200)
    ERROR = ("error", ft.Colors.RED, ft.Colors.RED_200)
    INFO = ("info", ft.Colors.BLUE, ft.Colors.BLUE_200)
    WARNING = ("warning", ft.Colors.ORANGE, ft.Colors.ORANGE_200)


def message_snackbar(page: ft.Page, message: str, message_type: MessageType = MessageType.INFO, duration: int = 5000):
    """
    Exibe uma notificação de mensagem no topo da tela.

    Parâmetros:
        page (ft.Page): Página onde o Snackbar será exibido.
        message (str): Mensagem a ser exibida.
        message_type (MessageType): Tipo da mensagem que define o esquema de cores.
            Valores possíveis:
            - MessageType.SUCCESS: Para mensagens de sucesso (verde)
            - MessageType.ERROR: Para mensagens de erro (vermelho)
            - MessageType.INFO: Para informações gerais (azul)
            - MessageType.WARNING: Para advertências (laranja)
    """

    bg_color = message_type.value[1]
    # icon_color = message_type.value[2]

    snack_bar = ft.SnackBar(
        content=ft.Text(message),
        bgcolor=bg_color,
        show_close_icon=True,
        # close_icon_color=icon_color,
        padding=ft.padding.all(10),
        duration=duration,
        behavior=ft.SnackBarBehavior.FLOATING,
        margin=ft.margin.all(10),
    )

    # page.show_snack_bar(snack_bar) # Este método não existe em page
    page.overlay.append(snack_bar)
    page.update()
    snack_bar.open = True
    page.update()


async def show_banner(page: ft.Page, message: str, btn_text: str = 'Entendi') -> None:
    def close_banner(e):
        banner.open = False
        e.control.page.update()

    banner = ft.Banner(
        bgcolor=ft.Colors.PRIMARY,
        leading=ft.Icon(ft.Icons.WARNING_AMBER,
                        color=ft.Colors.ON_PRIMARY, size=40),
        content=ft.Text(message, color=ft.Colors.ON_PRIMARY),
        actions=[ft.ElevatedButton(
            text=btn_text,
            icon=ft.icons.CLOSE,
            style=ft.ButtonStyle(
                color=ft.Colors.ON_PRIMARY_CONTAINER,
                bgcolor=ft.Colors.PRIMARY_CONTAINER,
            ),
            on_click=close_banner
        )],
    )

    page.overlay.append(banner)
    banner.open = True
    page.update()
