import flet as ft




def main_content():
    main_content = ft.Container(
        expand=True,
        bgcolor="#111418",
        border_radius=10,
        content=ft.Column(
            controls=[
                ft.Text("Estou no Main Content"),
            ]
        )
    )
    return main_content
