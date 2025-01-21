import flet as ft
from typing import Optional


class LoginView:
    def __init__(self, page: ft.Page):
        self.page = page
        self.email_input = None
        self.password_input = None
        self.error_text = None
        self.btn_login = None
        self.form = self.build_form()
        self.page.on_resized = self.page_resize

    def get_responsive_sizes(self, page_width: int) -> dict:
        if page_width < 600:  # Mobile
            return {
                "font_size": 14,
                "icon_size": 16,
                "button_width": 200,
                "input_width": 280,
                "form_padding": 20,
                "spacing": 4,
                "border_width": 1.5
            }
        elif page_width < 1024:  # Tablet
            return {
                "font_size": 16,
                "icon_size": 20,
                "button_width": 250,
                "input_width": 350,
                "form_padding": 40,
                "spacing": 6,
                "border_width": 2
            }
        else:  # Desktop
            return {
                "font_size": 18,
                "icon_size": 24,
                "button_width": 300,
                "input_width": 400,
                "form_padding": 50,
                "spacing": 8,
                "border_width": 2.5
            }

    def build_login_button(self, sizes: dict) -> ft.OutlinedButton:
        return ft.OutlinedButton(
            content=ft.Row(
                controls=[
                    ft.Icon(
                        ft.Icons.LOGIN,
                        color=ft.Colors.WHITE,
                        size=sizes["icon_size"]
                    ),
                    ft.Text(
                        value="Entrar",
                        size=sizes["font_size"],
                        text_align=ft.TextAlign.CENTER,
                        weight=ft.FontWeight.W_500
                    )
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=sizes["spacing"],
                tight=True
            ),
            width=sizes["button_width"],
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                side=ft.BorderSide(
                    color=ft.Colors.BLUE_400,
                    width=sizes["border_width"]
                ),
                padding=ft.padding.symmetric(
                    horizontal=sizes["spacing"] * 2,
                    vertical=sizes["spacing"]
                )
            ),
            on_click=self.handle_login,
            # animate=ft.animation.Animation(300, ft.AnimationCurve.EASE_OUT)
        )

    def build_input_field(self, sizes: dict, label: str, icon: str, password: bool = False) -> ft.TextField:
        return ft.TextField(
            label=label,
            width=sizes["input_width"],
            text_size=sizes["font_size"],
            password=password,
            can_reveal_password=password,
            border_color=ft.Colors.BLUE_400,
            focused_border_color=ft.Colors.BLUE_600,
            prefix_icon=icon,
            text_align=ft.TextAlign.LEFT,
            bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE)
        )

    def build_form(self) -> ft.Container:
        sizes = self.get_responsive_sizes(self.page.width)

        self.email_input = self.build_input_field(
            sizes, "Email", ft.Icons.EMAIL)
        self.password_input = self.build_input_field(
            sizes, "Senha", ft.Icons.LOCK, password=True)
        self.btn_login = self.build_login_button(sizes)
        self.error_text = ft.Text(
            color=ft.Colors.RED_400,
            size=sizes["font_size"],
            visible=False
        )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "Bem-vindo",
                        size=sizes["font_size"] * 2,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.WHITE
                    ),
                    ft.Text(
                        "Faça login para continuar",
                        size=sizes["font_size"],
                        color=ft.Colors.WHITE70,
                        weight=ft.FontWeight.W_300
                    ),
                    ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                    self.email_input,
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    self.password_input,
                    self.error_text,
                    ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                    self.btn_login,
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    ft.TextButton(
                        text="Esqueceu sua senha?",
                        on_click=self.handle_forgot_password,
                    )
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
            padding=ft.padding.all(sizes["form_padding"]),
            border_radius=10,
            bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.BLACK)
        )

    def validate_form(self) -> Optional[str]:
        email = self.email_input.value
        password = self.password_input.value

        if not email:
            return "Por favor, insira seu email"
        if not "@" in email:
            return "Email inválido"
        if not password:
            return "Por favor, insira sua senha"
        if len(password) < 6:
            return "A senha deve ter pelo menos 6 caracteres"

        return None

    def handle_login(self, _):
        error = self.validate_form()
        if error:
            self.error_text.value = error
            self.error_text.visible = True
            self.error_text.update()
            return

        self.error_text.visible = False
        self.error_text.update()
        # Aqui você implementaria a lógica de autenticação
        print(f"Login com email: {self.email_input.value}")
        self.page.go('/dashboard')

    def handle_forgot_password(self, _):
        self.page.go('/forgot-password')

    def page_resize(self, e):
        sizes = self.get_responsive_sizes(e.page.width)

        # Atualiza tamanhos dos inputs
        self.email_input.width = sizes["input_width"]
        self.email_input.text_size = sizes["font_size"]

        self.password_input.width = sizes["input_width"]
        self.password_input.text_size = sizes["font_size"]

        # Atualiza o botão
        icon_control = self.btn_login.content.controls[0]
        icon_control.size = sizes["icon_size"]

        text_control = self.btn_login.content.controls[1]
        text_control.size = sizes["font_size"]

        self.btn_login.content.spacing = sizes["spacing"]
        self.btn_login.width = sizes["button_width"]

        self.btn_login.style = ft.ButtonStyle(
            color=ft.Colors.WHITE,
            side=ft.BorderSide(
                color=ft.Colors.BLUE_400,
                width=sizes["border_width"]
            ),
            padding=ft.padding.symmetric(
                horizontal=sizes["spacing"] * 2,
                vertical=sizes["spacing"]
            )
        )

        # Atualiza o container principal
        form_column = self.form.content
        form_column.controls[0].size = sizes["font_size"] * 2  # Título
        form_column.controls[1].size = sizes["font_size"]      # Subtítulo

        self.error_text.size = sizes["font_size"]

        # Atualiza o padding do container
        self.form.padding = ft.padding.all(sizes["form_padding"])

        self.form.update()

    def build(self) -> ft.Container:
        return self.form


def main(page: ft.Page):
    page.bgcolor = ft.Colors.BLUE_GREY_900
    page.title = "Login"

    login_view = LoginView(page)

    # Centraliza o formulário na página
    page.add(
        ft.Row(
            controls=[login_view.build()],
            alignment=ft.MainAxisAlignment.CENTER
        )
    )


if __name__ == '__main__':
    ft.app(target=main)
