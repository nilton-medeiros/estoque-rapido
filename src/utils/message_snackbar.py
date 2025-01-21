import flet as ft
from enum import Enum


class MessageType(Enum):
    SUCCESS = ("success", ft.Colors.GREEN, ft.Colors.GREEN_200)
    ERROR = ("error", ft.Colors.RED, ft.Colors.RED_200)
    INFO = ("info", ft.Colors.BLUE, ft.Colors.BLUE_200)
    WARNING = ("warning", ft.Colors.ORANGE, ft.Colors.ORANGE_200)


def message_snackbar(page: ft.Page, message: str, message_type: MessageType = MessageType.INFO):
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
        duration=10000,
        behavior=ft.SnackBarBehavior.FLOATING,
        margin=ft.margin.all(10),
    )

    page.overlay.append(snack_bar)
    page.update()
    snack_bar.open = True
    page.update()