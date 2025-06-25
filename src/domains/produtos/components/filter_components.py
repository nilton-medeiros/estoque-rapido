# ==========================================
# src/domains/produtos/components/filter_components.py
# ==========================================
import flet as ft


class FilterComponents:
    """Componentes de filtro reutilizáveis"""

    @staticmethod
    def create_radio_filter(on_change_callback) -> ft.RadioGroup:
        return ft.RadioGroup(
            value="all",
            content=ft.Row([
                ft.Radio(value="all", label="Todos"),
                ft.Radio(value="active", label="Ativos"),
                ft.Radio(value="inactive", label="Descontinuados"),
            ]),
            on_change=on_change_callback,
        )

    @staticmethod
    def create_search_field(on_click_callback) -> ft.TextField:
        return ft.TextField(
            label="Busca pelo nome do produto",
            width=300,
            height=40,
            text_size=13,
            label_style=ft.TextStyle(size=10),
            suffix=ft.IconButton(
                icon=ft.Icons.FILTER_ALT_OUTLINED,
                icon_color=ft.Colors.PRIMARY,
                on_click=on_click_callback,
            ),
            bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.BLACK),
        )

    @staticmethod
    def create_stock_dropdown(on_change_callback) -> ft.Dropdown:
        return ft.Dropdown(
            label="Estoque",
            text_size=13,
            options=[
            ft.DropdownOption(key="all", text= "Todos", content=ft.Text("Todos", size=13, color=ft.Colors.WHITE)),
            ft.DropdownOption(key="normal", text= "Normal", content=ft.Text("Normal", size=13, color=ft.Colors.GREEN)),
            ft.DropdownOption(key="excellent", text= "Excelente", content=ft.Text("Excelente", size=13, color=ft.Colors.BLUE)),
            ft.DropdownOption(key="replace", text="Repor", content=ft.Text("Repor", size=13, color=ft.Colors.RED)),
            ],
            on_change=on_change_callback,
        )
