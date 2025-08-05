import flet as ft
from src.shared.config.version import APP_VERSION

from src.domains.shared.context.session import get_current_user
from src.pages.home.content_page import MainContent
from src.pages.partials.app_bars.appbar import create_appbar_menu

class HomePageView:
    """
    Encapsula a lógica e a construção da UI para a página inicial.
    """
    def __init__(self, page: ft.Page):
        self.page = page
        self.current_user = get_current_user(page)
        self._setup_theme()
        self.appbar = self._create_appbar()
        
    def _setup_theme(self):
        """Configura o tema da página com base no usuário atual."""
        self.page.theme_mode = ft.ThemeMode.DARK
        if self.current_user and self.current_user.theme_color:
            self.page.theme = self.page.dark_theme = ft.Theme(color_scheme_seed=self.current_user.theme_color)

    def _logoff_user(self, e):
        """Realiza o logoff do usuário."""
        self.page.go('/logout')

    def _handle_icon_hover(self, e):
        """Muda o bgcolor do container no hover."""
        e.control.bgcolor = ft.Colors.with_opacity(0.1, ft.Colors.WHITE) if e.data == "true" else ft.Colors.TRANSPARENT
        e.control.update()

    def _create_appbar(self) -> ft.AppBar:
        """Cria e retorna a AppBar para a página inicial."""
        actions = [
            ft.Container(
                width=40,
                height=40,
                border_radius=ft.border_radius.all(20),
                ink=True,
                bgcolor=ft.Colors.TRANSPARENT,
                alignment=ft.alignment.center,
                on_hover=self._handle_icon_hover,
                content=ft.Icon(ft.Icons.POWER_SETTINGS_NEW, color="white", size=22),
                tooltip="Sair",
                on_click=self._logoff_user,
                margin=ft.margin.only(right=10),
                clip_behavior=ft.ClipBehavior.ANTI_ALIAS
            ),
        ]

        return create_appbar_menu(
            page=self.page,
            title=ft.Text(f"v{APP_VERSION}", size=12),
            actions=actions
        )

    def build(self) -> ft.Container:
        """Constrói o conteúdo principal da página inicial."""
        main_content = MainContent(self.page)

        content_container = ft.Container(
            content=main_content,
            expand=True,
        )

        return content_container

def show_home_page(page: ft.Page) -> ft.View:
    """Página Home do usuário logado"""
    home_page_view = HomePageView(page)
    return ft.View(
        route='/home',
        appbar=home_page_view.appbar,
        drawer=page.drawer,
        controls=[home_page_view.build()],
        bgcolor=ft.Colors.BLACK,
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )
