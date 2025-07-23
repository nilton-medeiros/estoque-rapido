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
            ]),
            on_change=on_change_callback,
        )
