
import flet as ft

from src.utils.message_snackbar import MessageType, message_snackbar


def login(page: ft.Page):
    def test_msg_green(e):
        message_snackbar(page, "Teste do botão VERDE", MessageType.SUCCESS)

    def test_msg_red(e):
        message_snackbar(page, "Teste do botão VERMELHO", MessageType.ERROR)

    def test_msg_blue(e):
        message_snackbar(page, "Teste do botão AZUL", MessageType.INFO)

    def test_msg_warning(e):
        message_snackbar(page, "Teste do botão LARANJA", MessageType.WARNING)

    return ft.Container(
        bgcolor='amber',
        height=300,
        alignment=ft.alignment.center,
        content=ft.Column(
            spacing=20,
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text('Login em construção!',
                        size=40, color=ft.Colors.WHITE),
                ft.ElevatedButton(
                    text="  Voltar à pagina principal  ",
                    height=45,
                    color=ft.Colors.WHITE,
                    bgcolor=ft.Colors.BLACK,
                    on_click=lambda _: page.go('/')
                ),
                ft.Row(
                    spacing=20,
                    controls=[
                        ft.ElevatedButton(
                            text="  SUCESSO!  ",
                            height=45,
                            color=ft.Colors.WHITE,
                            bgcolor=ft.Colors.BLACK,
                            on_click=test_msg_green
                        ),
                        ft.ElevatedButton(
                            text="  ERRO!  ",
                            height=45,
                            color=ft.Colors.WHITE,
                            bgcolor=ft.Colors.BLACK,
                            on_click=test_msg_red
                        ),
                        ft.ElevatedButton(
                            text="  AVISO GERAL  ",
                            height=45,
                            color=ft.Colors.WHITE,
                            bgcolor=ft.Colors.BLACK,
                            on_click=test_msg_blue
                        ),
                        ft.ElevatedButton(
                            text="  ADVERTÊNCIA!  ",
                            height=45,
                            color=ft.Colors.WHITE,
                            bgcolor=ft.Colors.BLACK,
                            on_click=test_msg_warning
                        ),
                    ],
                ),
            ],
        )
    )
