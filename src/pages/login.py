import flet as ft
from typing import Optional

from src.domain.models.nome_pessoa import NomePessoa
from src.domain.models.phone_number import PhoneNumber
from src.controllers.user_controller import handle_get_user
from src.pages.partials import get_responsive_sizes
from src.pages.partials.build_input_responsive import build_input_field
from src.utils.message_snackbar import MessageType, message_snackbar
from src.utils.field_validation_functions import get_first_and_last_name, validate_email, validate_password_strength


class LoginView:
    def __init__(self, page: ft.Page):
        self.page = page
        self.email_input = None
        self.password_input = None
        self.error_text = None
        self.login_button = None
        self.form = self.build_form()
        self.page.on_resized = self.page_resize

    def build_login_button(self, sizes: dict) -> ft.OutlinedButton:
        return ft.OutlinedButton(
            content=ft.Row(
                controls=[
                    ft.Icon(
                        ft.Icons.APP_REGISTRATION,
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

    def build_form(self) -> ft.Container:
        sizes = get_responsive_sizes(self.page.width)

        self.email_input = build_input_field(
            sizes=sizes, label="Email", icon=ft.Icons.EMAIL)
        self.password_input = build_input_field(
            sizes=sizes, label="Senha", icon=ft.Icons.LOCK, password=True)
        self.login_button = self.build_login_button(sizes)
        self.error_text = ft.Text(color=ft.Colors.RED_400, size=sizes["font_size"], visible=False)

        # Debug: Dados Fakes como hardcord, remover isto em produção
        self.email_input.value = 'ajolie@gmail.com'
        self.password_input.value = 'Aj#45678'

        return ft.Container(
            alignment=ft.alignment.center,
            bgcolor=ft.Colors.BLACK,
            opacity=0.75,
            padding=ft.padding.all(sizes["form_padding"]),
            border_radius=10,  # Suaviza as bordas
            border=ft.border.all(color=ft.Colors.YELLOW_ACCENT_400, width=1),
            shadow=ft.BoxShadow(
                offset=ft.Offset(2, 2),  # Deslocamento horizontal e vertical
                blur_radius=16,  # Raio de desfoque
                spread_radius=0,  # Raio de propagação
                color="#F5F5F5",  # Cor da sombra
            ),
            width=500,
            content=ft.Column(
                controls=[
                    ft.Text(
                        "Bem-vindo",
                        size=sizes["font_size"] * 2,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.WHITE
                    ),
                    ft.Text(
                        "Faça o login para entrar",
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
                    self.login_button,
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    ft.TextButton(
                        text="Criar uma conta",
                        on_click=lambda _: self.page.go('/signup'),
                    )
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
        )

    def validate_form(self) -> Optional[str]:
        email = self.email_input.value
        password = self.password_input.value

        if not email:
            return "Por favor, insira seu email"
        if not validate_email(email):
            return "Email inválido"

        if len(password) < 8:
            return "A senha deve ter:\n• pelo menos 8 caracteres"

        return None

    async def handle_login(self, _):
        # Desabilita o botão imediatamente para evitar múltiplos cliques
        self.login_button.disabled = True
        self.login_button.update()

        # Detalhes de UX, com o estado de carregamento do botão
        try:
            # Faz a validação dos campos
            error = self.validate_form()
            if error:
                # Erro na validação dos campos, retorna sem fazer o credenciamento
                self.error_text.value = error
                self.error_text.visible = True
                self.error_text.update()
                return

            # Campos validados, segue com o credenciamento
            # Oculta texto de mensagens de erro.
            self.error_text.visible = False
            self.error_text.update()

            result = await handle_get_user(email=self.email_input.value)

            if not result["is_error"]:
                # Atualiza o estado do app com o novo usuário antes da navegação
                user = result["user"]
                first_name, last_name = get_first_and_last_name(user.display_name)

                await self.page.app_state.set_user({
                    "id": user.id,
                    "name": NomePessoa(first_name, last_name),
                    "email": user.email,
                    "phone_number": PhoneNumber(user.phone_number),
                    "profile": user.profile,
                    # Adicione outros dados relevantes do usuário
                })

                self.page.pubsub.send_all("user_updated")

                if user.empresas:
                    await self.page.app_state.set_company({
                        "id": 'emp_erwerwe34r5ir8u4jdf',
                        "name": 'SISTROM SISTEMA WEB',
                    })
                    self.page.pubsub.send_all("company_updated")


            color = MessageType.ERROR if result["is_error"] else MessageType.SUCCESS
            message_snackbar(
                page=self.page, message=result["message"], message_type=color)

            if not result["is_error"]:
                self.page.go('/home')

        finally:
            # Reabilita o botão independente do resultado
            self.login_button.disabled = False
            self.login_button.update()

    def page_resize(self, e):
        sizes = get_responsive_sizes(e.page.width)

        # Atualiza tamanhos dos inputs
        self.name_input.width = sizes["input_width"]
        self.name_input.text_size = sizes["font_size"]

        self.email_input.width = sizes["input_width"]
        self.email_input.text_size = sizes["font_size"]

        self.phone_input.width = sizes["input_width"]
        self.phone_input.text_size = sizes["font_size"]

        self.password_input.width = sizes["input_width"]
        self.password_input.text_size = sizes["font_size"]

        self.password_again_input.width = sizes["input_width"]
        self.password_again_input.text_size = sizes["font_size"]

        # Atualiza o botão
        icon_control = self.login_button.content.controls[0]
        icon_control.size = sizes["icon_size"]

        text_control = self.login_button.content.controls[1]
        text_control.size = sizes["font_size"]

        self.login_button.content.spacing = sizes["spacing"]
        self.login_button.width = sizes["button_width"]

        self.login_button.style = ft.ButtonStyle(
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


def login(page: ft.Page):
    '''
    Cria uma página Container de formulário de login de usuários.

    Args:
        page (ft.page): Página principal do app.

    Retorna:
        ft.Stack: Stack contendo imagem de fundo e formulário de login.
    '''
    login_view = LoginView(page)

    return ft.Stack(
        controls=[
            ft.Image(
                src="/images/estoquerapido_img_123e4567e89b12d3a456426614174000.svg",
                fit=ft.ImageFit.COVER,
                expand=True,
                width=page.width,
                height=page.height
            ),
            ft.Container(
                alignment=ft.alignment.center,
                content=login_view.build(),
                bgcolor=None,  # Define como transparente
            )
        ],
        expand=True
    )
