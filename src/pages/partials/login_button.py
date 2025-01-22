import flet as ft


class LoginBtn:
    '''
    Login Button (LoginBtn):
        Cria um Botão de Login totalmente responsivo para a página de Landing Page.

    Args:
        page (ft.Page): Recebe um ft.Page

    Methods:
        get_responsive_sizes: Obtem um dicionário com os devidos tamanhos:
            font_size: tamanho de fonte adaptativo
            icon_size: tamanho do ícone proporcional
            button_width: Largura do botão ajustável
            spacing: Espaço interno (padding) responsivo
            border_width: Espaçamento entre ícone e texto ajustável

        build_login_button: Constrói o botão com o tamanho de fonte inicial

        handle_login: On_click do botão, troca a rota para página de login

        build: Retorna btn_login (ft.OutlinedButton)
    '''

    def __init__(self, page: ft.Page):
        self.page = page
        self.btn_login = self.build_login_button()

    def get_responsive_sizes(self, page_width: int) -> dict:
        if page_width < 600:  # Mobile
            return {
                "font_size": 14,
                "icon_size": 16,
                "button_width": 100,
                "spacing": 4,
                "border_width": 1.5
            }
        elif page_width < 1024:  # Tablet
            return {
                "font_size": 16,
                "icon_size": 20,
                "button_width": 120,
                "spacing": 6,
                "border_width": 2
            }
        else:  # Desktop
            return {
                "font_size": 18,
                "icon_size": 24,
                "button_width": 140,
                "spacing": 8,
                "border_width": 2.5
            }

    def build_login_button(self) -> ft.OutlinedButton:
        sizes = self.get_responsive_sizes(self.page.width)

        return ft.OutlinedButton(
            content=ft.Row(
                controls=[
                    ft.Icon(
                        ft.Icons.LOGIN,
                        color=ft.Colors.WHITE,
                        size=sizes["icon_size"]
                    ),
                    ft.Text(
                        value="Login",
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
                side={
                    # Normal
                    "": ft.BorderSide(color=ft.Colors.BLUE_400, width=sizes["border_width"]),
                    # Hover
                    "hovered": ft.BorderSide(color=ft.Colors.BLUE_300, width=sizes["border_width"]),
                },
                padding=ft.padding.symmetric(
                    horizontal=sizes["spacing"] * 2,
                    vertical=sizes["spacing"]
                ),
                bgcolor={
                    "": ft.Colors.TRANSPARENT,  # Normal
                    "hovered": ft.Colors.BLUE_600  # Hover
                }
            ),
            on_click=self.handle_login,
            animate_size=ft.animation.Animation(
                300, ft.AnimationCurve.EASE_OUT),
            animate_opacity=ft.animation.Animation(
                300, ft.AnimationCurve.EASE_OUT),
            animate_scale=ft.animation.Animation(
                300, ft.AnimationCurve.EASE_OUT)
        )

    def handle_login(self, _):
        self.page.go('/login')

    def update_sizes(self, width: int):
        sizes = self.get_responsive_sizes(width)

        # Atualiza o ícone
        icon_control = self.btn_login.content.controls[0]
        icon_control.size = sizes["icon_size"]

        # Atualiza o texto
        text_control = self.btn_login.content.controls[1]
        text_control.size = sizes["font_size"]

        # Atualiza a largura do botão
        self.btn_login.width = sizes["button_width"]

        # Recria o estilo do botão
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

        self.btn_login.update()

    def build(self) -> ft.Control:
        return self.btn_login
