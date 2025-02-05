import flet as ft

# class FunctionalityGraphics:
#     def __init__(self, title: str, value: float):
#         self.title = title
#         self.value = value
#         self.expand = True

class Functionalities(ft.Column):
    def __init__(self, title: str, value: float):
        super().__init__()
        self.title = title
        self.value = value
        self.expand = True

    def build(self):
        return ft.Column(
            controls=[
                ft.Stack(
                    controls=[
                        ft.PieChart(
                            sections=[
                                ft.PieChartSection(
                                    value=self.value, color=ft.Colors.PRIMARY, radius=5),
                                ft.PieChartSection(
                                    value=1 - self.value, color=ft.Colors.BLACK26, radius=5),
                            ],
                            sections_space=0,
                            height=70,
                        ),
                        ft.Container(
                            content=ft.Text(
                                value=f'{self.value:.0%}', theme_style=ft.TextThemeStyle.BODY_LARGE),
                            alignment=ft.alignment.center,
                            height=70,
                        )
                    ]
                ),
                ft.Text(value=self.title,
                        theme_style=ft.TextThemeStyle.BODY_LARGE),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
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