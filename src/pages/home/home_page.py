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

    sidebar = sidebar_container(page)
    content = main_content()

    # Layout inicial (para telas grandes)
    layout = ft.ResponsiveRow(
        columns=12,
        controls=[sidebar, content],
        expand=True,
        alignment=ft.MainAxisAlignment.CENTER,
    )

    def toggle_sidebar(e):
        if page.width < 768:
            # Mobile
            sidebar.visible = not sidebar.visible
            content.visible = not sidebar.visible
            if sidebar.visible:
                sidebar.col = {"xs": 12}
                content.col = {"xs": 0}
            else:
                sidebar.col = {"xs": 0}
                content.col = {"xs": 12}
        else:
            # Desktop
            sidebar.visible = not sidebar.visible
            content.visible = True
        page.update()

    def logoff_user(e):
        page.go('/logout')

    """
    O page.appbar não tem efeito aqui, pois a View já possui um AppBar!
    Solução: Envio a variável appbar como data para a View, para que possa ser acessada através de appbar=home.data
    Nota: Na View rora /home, appbar=page.appbar não tem efeito, pois a AppBar já foi definida.
    """
    appbar = ft.AppBar(
        leading=ft.IconButton(
            icon=ft.Icons.MENU,
            on_click=toggle_sidebar,
        ),
        actions=[
            ft.Container(
                content=ft.IconButton(
                    icon=ft.Icons.POWER_SETTINGS_NEW,
                    icon_color="white",
                    on_click=logoff_user,
                ),

                margin=ft.margin.only(right=10),
            )
        ],
    )

    def on_page_resized(e=None):
        if page.width < 768:  # Modo Mobile
            # Ajustar layout para modo mobile
            sidebar.visible = False
            content.col = {"xs": 12}  # O conteúdo ocupa toda a largura
            layout.spacing = 0
            page.bgcolor = "#111418"

        else:  # Modo Desktop

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
        ),
        data=appbar,
    )

    return parent_container
