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
    # page.bgcolor = ft.Colors.BLACK

    sidebar = sidebar_container(page)
    content = main_content()

    def toggle_sidebar(e):
        sidebar.visible = not sidebar.visible
        content.visible = not sidebar.visible if page.width < 768 else True
        page.update()

    page.appbar = ft.AppBar(
        leading_width=40,
        leading=ft.IconButton(
            icon=ft.Icons.MENU,
            icon_color=ft.Colors.WHITE,
            on_click=toggle_sidebar
        ),
        title="MENU",
        # bgcolor="#111418",
        bgcolor=ft.Colors.BLUE_700,
        actions=[
            ft.Container(
                content=ft.Icons.CLOSE,
                margin=ft.margin.only(right=10),
            )
        ],
    )

    # Layout inicial (para telas grandes)
    layout = ft.ResponsiveRow(
        columns=12,
        controls=[sidebar, content],
        expand=True,
        alignment=ft.MainAxisAlignment.CENTER,
    )

    def on_page_resized(e=None):
        print(f"DEBUG: page.width = {page.width}")  # Depuração

        if page.width < 768:  # Modo Mobile
            print("DEBUG: Entrando no modo mobile")
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

    parent_container = ft.Container(
        expand=True,
        height=page.height,
        alignment=ft.alignment.center,
        content=ft.Column(
            spacing=0,
            alignment=ft.alignment.center,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            controls=[layout]
        )
    )

    page.update()

    return parent_container
