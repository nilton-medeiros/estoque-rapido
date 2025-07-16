import flet as ft

def create_menu_item(page: ft.Page, item):
    return ft.ListTile(
        leading=ft.Icon(item["icon"], color=ft.Colors.WHITE),
        title=ft.Text(item["label"], color=ft.Colors.WHITE),
        tooltip=item["tooltip"],
        on_click=lambda e: page.go(item["route"]) if item["route"] else None,
        bgcolor=ft.Colors.TRANSPARENT,
        hover_color=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
        disabled=item["route"] is None,
        selected=page.route == item["route"],
        selected_color=ft.Colors.PRIMARY,
    )

def create_navigation_drawer(page: ft.Page):
    menu_items = [
        {"icon": ft.Icons.BUSINESS, "label": "Empresas", "tooltip": "Empresas", "route": "/home/empresas/grid"},
        {"icon": ft.Icons.GROUPS, "label": "Usuários", "tooltip": "Usuários", "route": "/home/usuarios/grid"},
        {"icon": ft.Icons.ASSIGNMENT_OUTLINED, "label": "Categorias", "tooltip": "Categorias de produtos", "route": "/home/produtos/categorias/grid"},
        {"icon": ft.Icons.SHOPPING_BAG_OUTLINED, "label": "Produtos", "tooltip": "Produtos", "route": "/home/produtos/grid"},
        {"icon": ft.Icons.FACT_CHECK_OUTLINED, "label": "Estoque", "tooltip": "Estoque", "route": None},
        {"icon": ft.Icons.POINT_OF_SALE_OUTLINED, "label": "Pedidos", "tooltip": "Pedidos", "route": "/home/pedidos/grid"},
    ]

    drawer_controls = [create_menu_item(page, item) for item in menu_items]

    header = ft.Container(
        content=ft.Text("Menu", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
        padding=ft.padding.all(16),
        bgcolor=ft.Colors.PRIMARY,
    )

    return ft.NavigationDrawer(
        controls=[header] + drawer_controls,
        bgcolor="#111418",
        # width=300,
        open=False,
    )
