import flet as ft


def home(page: ft.Page):
    user_name = page.app_state.user['name'].nome_completo
    company_name = page.app_state.company['name']

    return ft.Container(
        alignment=ft.alignment.center,
        bgcolor=ft.Colors.AMBER_200,
        border_radius=10,
        # height=300,
        content=ft.Column(
            spacing=20,
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment = ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text('Página Home', size=40, color=ft.Colors.BLACK38),
                ft.Text(value=f"Usuário logado: {user_name}", size=16, color=ft.Colors.BLACK38),
                ft.Text(value=f"Empresa logada: {company_name}", size=16, color=ft.Colors.BLACK38),
                ft.ElevatedButton(
                    text="  Voltar à pagina principal  ",
                    height=45,
                    color=ft.Colors.WHITE,
                    bgcolor=ft.Colors.BLACK,
                    on_click=lambda _: page.go('/')
                )
            ],
        )
    )
