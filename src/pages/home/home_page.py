import flet as ft

from src.pages.home.sidebar import sidebar_container
from src.pages.home.content import main_content

# Thema da aplicação que começa em home


class AppTheme:
    theme = ft.Theme(
        color_scheme=ft.ColorScheme(
            background='#111418',
            on_background='#2d2d3a',
            on_inverse_surface='#2d2d3a',
            primary=ft.Colors.BLUE,
        ),
        text_theme=ft.TextTheme(
            body_large=ft.TextStyle(
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.WHITE,
                size=14,
            ),
            body_medium=ft.TextStyle(
                weight=ft.FontWeight.NORMAL,
                color=ft.Colors.GREY,
                size=14,
            ),
            headline_large=ft.TextStyle(
                weight=ft.FontWeight.W_900,
                color=ft.Colors.WHITE,
                size=50,
            ),
            label_large=ft.TextStyle(
                weight=ft.FontWeight.W_700,
                color=ft.Colors.WHITE,
                size=16,
            ),
            headline_medium=ft.TextStyle(
                weight=ft.FontWeight.W_700,
                color=ft.Colors.WHITE,
                size=30,
            )
        ),
        scrollbar_theme=ft.ScrollbarTheme(
            track_visibility=False,
            thumb_visibility=False,
            track_color={
                ft.ControlState.DEFAULT: ft.Colors.WHITE10,
            },
            thumb_color={
                ft.ControlState.HOVERED: ft.Colors.WHITE10,
                ft.ControlState.DEFAULT: ft.Colors.WHITE10,
            }
        )
    )


def home_page(page: ft.Page):
    """Página Home do usuário logado"""
    page.theme = AppTheme.theme
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = ft.Colors.BLACK

    sidebar = sidebar_container(page)
    content = main_content()

    # Layout inicial (para telas grandes)
    layout = ft.ResponsiveRow(
        columns=12,
        controls=[sidebar, content],
        expand=True,
    )

    def toggle_sidebar(e):
        sidebar.visible = not sidebar.visible
        page.update()

    def on_page_resized(e=None):
        print(f"DEBUG: page.width = {page.width}")  # Depuração

        if page.width < 768:  # Modo Mobile
            print("DEBUG: Entrando no modo mobile")

            page.appbar = ft.AppBar(
                title=ft.Text("Menu"),  # **Título do menu**
                leading=ft.IconButton(
                    icon=ft.Icons.MENU,
                    icon_color=ft.Colors.WHITE,
                    on_click=toggle_sidebar
                ),
                bgcolor="#111418",
            )

            print(f"DEBUG: page.appbar = {page.appbar}")

            # Ajustar layout para modo mobile
            sidebar.visible = False
            content.col = {"xs": 12}  # O conteúdo ocupa toda a largura
            layout.spacing = 0
            page.bgcolor = "#111418"

        else:  # Modo Desktop
            print("DEBUG: Entrando no modo desktop")

            page.appbar = None  # Remover AppBar
            sidebar.visible = True
            sidebar.col = {"xs": 3}  # Sidebar com 3 colunas
            content.col = {"xs": 9}  # Content com 9 colunas
            layout.spacing = 10
            page.bgcolor = ft.Colors.BLACK

        page.update()  # **Atualiza a página após modificar AppBar**

    page.on_resized = on_page_resized
    on_page_resized(None)

    return ft.Column(  # **Troca Container por Column para respeitar AppBar**
        controls=[layout],
        expand=True,  # Permite que o layout ocupe toda a tela sem sobrepor a AppBar
    )
