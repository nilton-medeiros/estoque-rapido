import flet as ft

def create_appbar_menu(page: ft.Page, title: ft.Text | None = None, actions: list | None = None) -> ft.AppBar:
    def toggle_drawer(e):
        if page.drawer:
            page.drawer.open = not page.drawer.open
            page.update()

    return ft.AppBar(
        leading=ft.IconButton(ft.Icons.MENU, on_click=toggle_drawer),
        bgcolor=ft.Colors.with_opacity(0.9, ft.Colors.PRIMARY_CONTAINER),
        adaptive=True,
        title=title,
        actions=actions,
    )

def create_appbar_back(page: ft.Page, title: ft.Text | None = None, actions: list | None = None) -> ft.AppBar:
    return ft.AppBar(
        leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: page.back()), # type: ignore [attr-defined]
        bgcolor=ft.Colors.with_opacity(0.9, ft.Colors.PRIMARY_CONTAINER),
        adaptive=True,
        title=title,
        actions=actions,
    )
