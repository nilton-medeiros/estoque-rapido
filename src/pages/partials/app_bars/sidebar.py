import flet as ft
from src.pages.partials.app_bars.popup_color_item import PopupColorItem
from src.shared.config.get_app_colors import THEME_COLOR_NAMES, COLOR_DISPLAY_NAMES
from src.pages.partials.app_bars.sidebar_header import create_sidebar_header

def create_menu_item(page: ft.Page, item: dict):
    return ft.ListTile(
        leading=ft.Icon(item["icon"], color=ft.Colors.WHITE),
        title=ft.Text(item["label"], color=ft.Colors.WHITE),
        tooltip=item.get("tooltip"),
        on_click=lambda e: page.go(item["route"]) if item["route"] else None,
        bgcolor=ft.Colors.TRANSPARENT,
        hover_color=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
        disabled=item["route"] is None,
        selected=page.route == item["route"],
        selected_color=ft.Colors.PRIMARY,
    )

def create_navigation_drawer(page: ft.Page):
    menu_items = [
        {"icon": ft.Icons.HOME_OUTLINED, "label": "Home", "tooltip": "Página inicial", "route": "/home"},
        {"icon": ft.Icons.PEOPLE, "label": "Clientes", "tooltip": "Lista de Clientes", "route": "/home/clientes/grid"},
        {"icon": ft.Icons.BUSINESS, "label": "Empresas", "tooltip": "Empresas cadastradas", "route": "/home/empresas/grid"},
        {"icon": ft.Icons.GROUPS, "label": "Usuários", "tooltip": "Usuários cadastrados", "route": "/home/usuarios/grid"},
        {"icon": ft.Icons.ASSIGNMENT_OUTLINED, "label": "Categorias", "tooltip": "Categorias de produtos", "route": "/home/produtos/categorias/grid"},
        {"icon": ft.Icons.SHOPPING_BAG_OUTLINED, "label": "Produtos", "tooltip": "Produtos cadastrados", "route": "/home/produtos/grid"},
        {"icon": ft.Icons.FACT_CHECK_OUTLINED, "label": "Estoque", "route": None},
        {"icon": ft.Icons.POINT_OF_SALE_OUTLINED, "label": "Pedidos", "tooltip": "Pedidos de venda", "route": "/home/pedidos/grid"},
    ]

    # Empilha os menus iniciais do menu_items na lista

    drawer_controls = [create_menu_item(page, item) for item in menu_items]

    # Mapeia nomes de cores para nomes de exibição mais amigáveis

    # Adicionamos a anotação de tipo para satisfazer o Pylance
    popup_color_items: list[ft.PopupMenuItem] = [
        PopupColorItem(color=color, name=COLOR_DISPLAY_NAMES.get(color, color.title()))
        for color in THEME_COLOR_NAMES
    ]

    # Cria o item de menu cor de tema
    theme_item = ft.ListTile(
        leading=ft.Icon(ft.Icons.COLOR_LENS_OUTLINED, color=ft.Colors.WHITE),
        title=ft.Text("Tema", color=ft.Colors.WHITE),
        tooltip="Escolha o tema de cores",
        trailing=ft.PopupMenuButton(
            items=popup_color_items,
            icon=ft.Icons.ARROW_DROP_DOWN,
        ),
        bgcolor=ft.Colors.TRANSPARENT,
        hover_color=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
    )

    header = create_sidebar_header(page)

    exit_button = create_menu_item(
        page,
        {
            "icon": ft.Icons.POWER_SETTINGS_NEW,
            "label": "Sair",
            "tooltip": "Fechar home page e deslogar usuário",
            "route": "/logout"
        }
    )

    return ft.NavigationDrawer(
        controls=[
            header,
            ft.Divider(height=5),
            *drawer_controls,
            ft.Divider(height=5),
            theme_item,
            ft.Divider(height=5),
            exit_button,
        ],
        bgcolor="#111418",
        open=False,
    )
