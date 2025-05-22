import flet as ft

# class FunctionalityGraphics:
#     def __init__(self, title: str, value: float):
#         self.title = title
#         self.value = value
#         self.expand = True

class Functionalities(ft.Column):
    def __init__(self, title: str, value: float):
        # Os parâmetros title e value são usados para construir os controles.
        # self.title = title # Desnecessário se title for usado apenas aqui
        # self.value = value # Desnecessário se value for usado apenas aqui

        _controls = [
            ft.Stack(
                controls=[
                    ft.PieChart(
                        sections=[
                            ft.PieChartSection(
                                value=value, color=ft.Colors.PRIMARY, radius=5),
                            ft.PieChartSection(
                                value=1 - value, color=ft.Colors.BLACK26, radius=5),
                        ],
                        sections_space=0,
                        height=50,
                    ),
                    ft.Container(
                        content=ft.Text(
                            value=f'{value:.0%}', theme_style=ft.TextThemeStyle.BODY_SMALL),
                        alignment=ft.alignment.center,
                        height=50,
                    )
                ]
            ),
            ft.Text(value=title,
                    theme_style=ft.TextThemeStyle.BODY_MEDIUM),
        ]

        super().__init__(
            controls=[
                *_controls
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True  # Aplica a expansão à própria instância de Functionalities
        )


class FiscalProgressBar(ft.Container):
    def __init__(self, title: str, value: float):
        super().__init__(
            expand=True,
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(value=title, theme_style=ft.TextThemeStyle.BODY_LARGE),
                            ft.Text(value=f'{value:.0%}', theme_style=ft.TextThemeStyle.BODY_MEDIUM),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.ProgressBar(value=value, color=ft.Colors.PRIMARY, bgcolor=ft.Colors.BLACK26),
                    ft.Divider(height=10, color=ft.Colors.BLACK12),
                ]
            )
        )