import flet as ft

def main(page: ft.Page):
    page.title = "EstoqueRápido"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    def handle_trial_click(e):
        pass  # Implementar lógica de trial

    page.add(
        ft.Container(
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(
                        content=ft.Text(
                            "EstoqueRápido - Claude",
                            size=40,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.BLUE_700,
                        ),
                        margin=ft.margin.only(bottom=20),
                    ),
                    ft.Text(
                        "Controle de estoque simplificado para sua empresa",
                        size=20,
                        color=ft.Colors.GREY_800,
                    ),
                    ft.Container(
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.CENTER,
                            controls=[
                                ft.Card(
                                    col=4,
                                    content=ft.Container(
                                        content=ft.Column(
                                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                            controls=[
                                                ft.Icon(ft.Icons.INVENTORY, size=40, color=ft.Colors.BLUE_400),
                                                ft.Text("Gestão de Estoque", size=16, weight=ft.FontWeight.BOLD),
                                                ft.Text("Controle total do seu inventário"),
                                            ],
                                        ),
                                        padding=20,
                                    ),
                                    width=250,
                                ),
                                ft.Card(
                                    col=4,
                                    content=ft.Container(
                                        content=ft.Column(
                                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                            controls=[
                                                ft.Icon(ft.Icons.BAR_CHART, size=40, color=ft.Colors.BLUE_400),
                                                ft.Text("Relatórios", size=16, weight=ft.FontWeight.BOLD),
                                                ft.Text("Análises detalhadas em tempo real"),
                                            ],
                                        ),
                                        padding=20,
                                    ),
                                    width=250,
                                ),
                                ft.Card(
                                    col=4,
                                    content=ft.Container(
                                        content=ft.Column(
                                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                            controls=[
                                                ft.Icon(ft.Icons.DEVICES, size=40, color=ft.Colors.BLUE_400),
                                                ft.Text("Multi-plataforma", size=16, weight=ft.FontWeight.BOLD),
                                                ft.Text("Acesse de qualquer dispositivo"),
                                            ],
                                        ),
                                        padding=20,
                                    ),
                                    width=250,
                                ),
                            ],
                            spacing=30,
                        ),
                        margin=ft.margin.symmetric(vertical=40),
                    ),
                    ft.ElevatedButton(
                        "Comece seu teste grátis",
                        style=ft.ButtonStyle(
                            color=ft.Colors.WHITE,
                            bgcolor=ft.Colors.BLUE_700,
                            padding=ft.padding.all(20),
                        ),
                        on_click=handle_trial_click,
                    ),
                ],
            ),
            padding=ft.padding.all(40),
        )
    )

ft.app(target=main)