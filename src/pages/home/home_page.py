import flet as ft

from src.pages.home.sidebar import sidebar_container
from src.pages.home.content import main_content
from src.shared.config.app_theme import AppTheme


def home_page(page: ft.Page):
    """Página Home do usuário logado"""
    page.theme = AppTheme.theme
    page.theme_mode = ft.ThemeMode.DARK

    print(f"Página Home -> user_colors: {page.app_state.usuario.get('user_colors')}")
    if colors := page.app_state.usuario.get('user_colors'):
        page.theme.color_scheme.primary = colors.get('primary')
        page.theme.color_scheme.primary_container = colors.get('container')

    print(f"Home Page -> Usuário: {page.app_state.usuario.get('name').nome_completo}")
    print(f"Home Page -> Color Scheme (primary): {page.theme.color_scheme.primary}")
    print(f"Home Page -> Color Scheme (primary_container): {page.theme.color_scheme.primary_container}")
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
    Nota: Na View rora /home, appbar=page.appbar não tem efeito, pois pega a primeira AppBar definida em landing_page.
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

            side_right = content.content.controls[0].content.controls[1]

            print(f"page.width: {page.width}")

            if page.width < 1024:
                # Oculta imagem de fundo
                side_right.visible = False
            else:
                side_right.visible = True

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
            scroll=None,
            controls=[layout]
        ),
        data=appbar,
    )

    print("Retornando parent_container para a View (conteúdo da página home)")
    return parent_container
