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
                ft.Radio(value="inactive", label="Inativos"),
                ft.Radio(value="delivered", label="Entregues"),
                ft.Radio(value="canceled", label="Cancelados"),
            ]),
            on_change=on_change_callback,
        )

    @staticmethod
    def create_search_field(on_click_callback) -> ft.TextField:
        return ft.TextField(
            label="Buscar pelo nome, número ou telefone",
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
