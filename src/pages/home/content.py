import flet as ft

def main_content():
    main_content = ft.Container(
        col={"xs": 12, "md": 7, "lg": 8, "xxl": 9},
        expand=True,
        bgcolor="#111418",
        border_radius=10,
        padding=ft.padding.all(30),
        margin=ft.margin.only(top=30),
        content=ft.Column(
            scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.Text("Estou no Main Content"),
            ]
        )
    )
    return main_content
