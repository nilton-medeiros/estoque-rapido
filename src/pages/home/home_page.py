import flet as ft

from src.pages.home import main_content
from src.pages.home.sidebar import sidebar_container


def dashboard(page: ft.Page):
    """Página Home do usuário logado"""
    # page.theme = AppTheme.theme
    page.theme_mode = ft.ThemeMode.DARK

    if colors := page.app_state.usuario.get('user_colors'): # type: ignore
       page.theme = page.dark_theme = ft.Theme(color_scheme_seed=colors.get('base_color')) # type: ignore

    # if colors := page.app_state.usuario.get('user_colors'):
        # page.theme.color_scheme.primary = colors.get('primary')
        # page.theme.color_scheme.primary_container = colors.get('container')

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
        print(f"Debug  -> page.width: {page.width}")
        print(f"Debug  -> page.window.width: {page.window.width}")
        if page.width < 768: # type: ignore
            # Mobile
            sidebar.visible = not sidebar.visible
            content.visible = not sidebar.visible
            print(f"Debug  -> sidebar.visible: {sidebar.visible}")
            print(f"Debug  -> content.visible: {content.visible}")
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
    def handle_icon_hover(e):
        """Muda o bgcolor do container no hover."""
        e.control.bgcolor = ft.Colors.with_opacity(0.1, ft.Colors.WHITE) if e.data == "true" else ft.Colors.TRANSPARENT
        e.control.update()

    appbar = ft.AppBar(
        leading=ft.Container(
            alignment=ft.alignment.center_left,
            padding=ft.padding.only(left=10),
            content=ft.Container(
                width=40,
                height=40,
                border_radius=ft.border_radius.all(20),
                ink=True,  # Aplica ink ao wrapper (ao clicar da um feedback visual para o usuário)
                bgcolor=ft.Colors.TRANSPARENT,
                alignment=ft.alignment.center,
                on_hover=handle_icon_hover,
                content=ft.Icon(ft.Icons.MENU),
                on_click=toggle_sidebar,
                tooltip="Menu",
                clip_behavior=ft.ClipBehavior.ANTI_ALIAS # Ajuda a garantir que o hover respeite o border_radius
            ),
        ),
        # bgcolor=ft.Colors.PRIMARY_CONTAINER,
        bgcolor=ft.Colors.with_opacity(0.9, ft.Colors.PRIMARY_CONTAINER), # Exemplo com opacidade
        adaptive=True,
        actions=[
            ft.Container(
                width=40,
                height=40,
                border_radius=ft.border_radius.all(20), # Metade da largura/altura para ser círculo
                ink=True,
                bgcolor=ft.Colors.TRANSPARENT,
                alignment=ft.alignment.center,
                on_hover=handle_icon_hover,
                content=ft.Icon(ft.Icons.POWER_SETTINGS_NEW, color="white", size=22),
                tooltip="Sair",
                on_click=logoff_user,
                margin=ft.margin.only(right=10),
                clip_behavior=ft.ClipBehavior.ANTI_ALIAS # Boa prática adicionar aqui também
            ),
        ],
    )

    def on_page_resized(e=None):
        if page.width < 1024: # type: ignore # Modo Mobile, tablet
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

            side_right = content.content.controls[0].content.controls[1] # type: ignore

            if page.width < 1024: # type: ignore
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
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=None,
            controls=[layout]
        ),
        data=appbar,
    )

    return parent_container
