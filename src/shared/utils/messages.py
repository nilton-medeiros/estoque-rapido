import flet as ft
from enum import Enum


class MessageType(Enum):
    SUCCESS = ("success", ft.Colors.GREEN, ft.Colors.GREEN_200)
    ERROR = ("error", ft.Colors.RED, ft.Colors.RED_200)
    INFO = ("info", ft.Colors.BLUE, ft.Colors.BLUE_200)
    WARNING = ("warning", ft.Colors.ORANGE, ft.Colors.ORANGE_200)
    PROGRESS = ("progress", ft.Colors.PURPLE, ft.Colors.PURPLE_200)


def  message_snackbar(page: ft.Page, message: str, message_type: MessageType = MessageType.INFO, center: bool = False, duration: int = 5000):
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
            - MessageType.PROGRESS: Para mensagens de progresso (roxo)
        center (bool): Se True, a mensagem será centralizada na tela com tamanho máximo de 600px
        duration (int): Duração em milissegundos da mensagem. Padrão é 5 segundos.
    """

    bg_color = message_type.value[1]

    if page.drawer and page.drawer.open:
       page.drawer.open = False
       page.update()
       # Se o menu lateral esquerdo está aberto, será fechado e mensagem será centralizada
       center = True

    snack_bar = ft.SnackBar(
        content=ft.Text(message),
        bgcolor=bg_color,
        show_close_icon=True,
        padding=ft.padding.all(10),
        duration=duration,
        behavior=ft.SnackBarBehavior.FLOATING,
        margin=ft.margin.all(10) if not center else None,
        # Garante que page.width não é None antes de usar em cálculos, com um fallback.
        width=(
            min((page.width or 600) * 0.8, 500)
            if center
            else None
        ),
    )

    # A forma correta e mais moderna de exibir um SnackBar
    page.open(snack_bar)

def show_banner(page: ft.Page, message: str, btn_text: str = 'Entendi') -> None:
    def close_banner(e):
        page.close(banner)

    banner = ft.Banner(
        bgcolor=ft.Colors.PRIMARY,
        leading=ft.Icon(ft.Icons.WARNING_AMBER,
                        color=ft.Colors.ON_PRIMARY, size=40),
        content=ft.Text(message, color=ft.Colors.ON_PRIMARY),
        actions=[ft.ElevatedButton(
            text=btn_text,
            icon=ft.Icons.CLOSE,
            style=ft.ButtonStyle(
                color=ft.Colors.ON_PRIMARY_CONTAINER,
                bgcolor=ft.Colors.PRIMARY_CONTAINER,
            ),
            on_click=close_banner
        )],
    )

    page.open(banner)


class ProgressiveMessage:
    """
    Classe para gerenciar mensagens progressivas que se atualizam automaticamente.
    Ideal para operações que têm múltiplas etapas sequenciais.
    """

    def __init__(self, page: ft.Page, center: bool = False):
        self.page = page
        self.current_snackbar = None
        self.center = center

    def _get_centered_width(self) -> int | None:
        """Calcula a largura para o SnackBar centralizado, com fallback."""
        if not self.center:
            return None
        # Garante que page.width não é None antes de usar em cálculos
        page_width = self.page.width or 600 # Usa 600 como fallback
        return int(min(page_width * 0.8, 500))

    def show_progress(self, message: str, show_spinner: bool = True, duration: int | None = None):
        """
        Mostra uma mensagem de progresso com spinner opcional.

        Args:
            message: Texto da mensagem
            show_spinner: Se deve mostrar um indicador de carregamento
            duration: Duração em ms (None = não fecha automaticamente)
        """
        # Fecha snackbar anterior se existir
        if self.current_snackbar:
            self.page.close(self.current_snackbar)

        # Conteúdo da mensagem
        content_controls = []

        if show_spinner:
            content_controls.append(
                ft.ProgressRing(
                    width=20,
                    height=20,
                    stroke_width=3,
                    color=ft.Colors.WHITE
                )
            )

        content_controls.append(ft.Text(message, color=ft.Colors.WHITE))

        content = ft.Row(
            controls=content_controls,
            spacing=10,
            alignment=ft.MainAxisAlignment.START
        )

        self.current_snackbar = ft.SnackBar(
            content=content,
            bgcolor=ft.Colors.PURPLE,
            duration=duration or 10000,  # Default longo para progresso
            behavior=ft.SnackBarBehavior.FLOATING,
            margin=ft.margin.all(10) if not self.center else None,
            width=self._get_centered_width(),
            show_close_icon=False if duration is None else True,
        )

        self.page.open(self.current_snackbar)

    def update_progress(self, message: str, show_spinner: bool = True):
        """
        Atualiza a mensagem de progresso atual.
        """
        if self.current_snackbar and self.current_snackbar.open:
            # Atualiza o conteúdo
            content_controls = []

            if show_spinner:
                content_controls.append(
                    ft.ProgressRing(
                        width=20,
                        height=20,
                        stroke_width=3,
                        color=ft.Colors.WHITE
                    )
                )

            content_controls.append(ft.Text(message, color=ft.Colors.WHITE))

            self.current_snackbar.content = ft.Row(
                controls=content_controls,
                spacing=10,
                alignment=ft.MainAxisAlignment.START
            )
            self.page.update()
        else:
            # Se não há snackbar ativo, cria um novo
            self.show_progress(message, show_spinner)

    def show_success(self, message: str, duration: int = 4000):
        """
        Mostra mensagem de sucesso final.
        """
        # Fecha snackbar de progresso
        if self.current_snackbar:
            self.page.close(self.current_snackbar)
            self.current_snackbar = None
        success_snackbar = ft.SnackBar(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.WHITE, size=20),
                    ft.Text(message, color=ft.Colors.WHITE)
                ],
                spacing=10
            ),
            bgcolor=ft.Colors.GREEN,
            duration=duration,
            behavior=ft.SnackBarBehavior.FLOATING,
            margin=ft.margin.all(10) if not self.center else None,
            width=self._get_centered_width(),
            show_close_icon=True,
        )

        self.page.open(success_snackbar)

    def show_warning(self, message: str, duration: int = 5000):
        """
        Mostra mensagem de aviso final.
        """
        # Fecha snackbar de progresso
        if self.current_snackbar:
            self.page.close(self.current_snackbar)
            self.current_snackbar = None
        warning_snackbar = ft.SnackBar(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color=ft.Colors.WHITE, size=20),
                    ft.Text(message, color=ft.Colors.WHITE)
                ],
                spacing=10
            ),
            bgcolor=ft.Colors.ORANGE, # Cor para aviso
            duration=duration,
            behavior=ft.SnackBarBehavior.FLOATING,
            margin=ft.margin.all(10) if not self.center else None,
            width=self._get_centered_width(),
            show_close_icon=True,
        )

        self.page.open(warning_snackbar)

    def show_error(self, message: str, duration: int = 6000):
        """
        Mostra mensagem de erro final.
        """
        # Fecha snackbar de progresso
        if self.current_snackbar:
            self.page.close(self.current_snackbar)
            self.current_snackbar = None
        error_snackbar = ft.SnackBar(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.ERROR, color=ft.Colors.WHITE, size=20),
                    ft.Text(message, color=ft.Colors.WHITE)
                ],
                spacing=10
            ),
            bgcolor=ft.Colors.RED,
            duration=duration,
            behavior=ft.SnackBarBehavior.FLOATING,
            margin=ft.margin.all(10) if not self.center else None,
            width=self._get_centered_width(),
            show_close_icon=True,
        )

        self.page.open(error_snackbar)

    def close(self):
        """
        Fecha a mensagem de progresso atual.
        """
        if self.current_snackbar:
            self.page.close(self.current_snackbar)
            self.current_snackbar = None
