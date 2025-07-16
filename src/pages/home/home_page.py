import flet as ft
from src.pages.home.content_page import MainContent
from src.pages.home.sidebar_page import create_navigation_drawer

def show_home_page(page: ft.Page) -> ft.Container:
    """Página Home do usuário logado"""
    page.theme_mode = ft.ThemeMode.DARK

    if colors := page.app_state.usuario.get('user_colors'): # type: ignore [attr-defined]
        page.theme = page.dark_theme = ft.Theme(color_scheme_seed=colors.get('base_color'))

    # Criar o NavigationDrawer e adicioná-lo à página
    drawer = create_navigation_drawer(page) # sidebar_page.py
    page.drawer = drawer

    main_content = MainContent(page)

    content_container = ft.Container(
        content=main_content,
        expand=True,
    )

    def toggle_drawer(e):
        if page.drawer:
            page.drawer.open = not page.drawer.open
            page.update()

    def logoff_user(e):
        page.go('/logout')

    def handle_icon_hover(e):
        """Muda o bgcolor do container no hover."""
        e.control.bgcolor = ft.Colors.with_opacity(0.1, ft.Colors.WHITE) if e.data == "true" else ft.Colors.TRANSPARENT
        e.control.update()

    #AppBar
    appbar = ft.AppBar(
        # leading_width=40,
        # leading=ft.Icon(ft.Icons.MENU),
        leading=ft.IconButton(ft.Icons.MENU, on_click=toggle_drawer),
        bgcolor=ft.Colors.with_opacity(0.9, ft.Colors.PRIMARY_CONTAINER),
        adaptive=True,
        actions=[
            ft.Container(
                width=40,
                height=40,
                border_radius=ft.border_radius.all(20),
                ink=True,
                bgcolor=ft.Colors.TRANSPARENT,
                alignment=ft.alignment.center,
                on_hover=handle_icon_hover,
                content=ft.Icon(ft.Icons.POWER_SETTINGS_NEW, color="white", size=22),
                tooltip="Sair",
                on_click=logoff_user,
                margin=ft.margin.only(right=10),
                clip_behavior=ft.ClipBehavior.ANTI_ALIAS
            ),
        ],
    )

    # O conteúdo principal da página home.
    # Usamos um container que encapsula o conteúdo e anexa o appbar
    # através do atributo 'data' para que a função route_change em main.py possa usá-lo.
    home_content_container = ft.Container(
        content=content_container,
        expand=True,
        data=appbar,  # Anexando o appbar para ser usado na View
    )

    return home_content_container # Retorna o container com o conteúdo principal e o AppBar