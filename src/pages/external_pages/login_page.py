import logging

import flet as ft

from src.domains.shared.context.session import get_session_colors
from src.domains.shared import Password, RegistrationStatus
from src.pages.partials import get_responsive_sizes, build_input_field

from src.services.states.app_state_manager import AppStateManager
from src.shared.utils import MessageType, message_snackbar, validate_email

import src.domains.empresas.controllers.empresas_controllers as company_controllers
import src.domains.usuarios.controllers.usuarios_controllers as user_controllers

from src.domains.empresas.models.empresas_model import Empresa

logger = logging.getLogger(__name__)


class LoginView:
    def __init__(self, page: ft.Page):
        self.page: ft.Page = page
        self.email_input: ft.TextField
        self.password_input: ft.TextField
        self.error_text: ft.Text
        self.login_button: ft.OutlinedButton
        self.title_text: ft.Text
        self.subtitle_text: ft.Text
        self.app_colors = get_session_colors(page)
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
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=sizes["spacing"],
                tight=True,
            ),
            width=sizes["button_width"],
            height=50,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                side=ft.BorderSide(
                    color=self.app_colors["accent"],
                    width=sizes["border_width"]
                ),
                padding=ft.padding.symmetric(
                    horizontal=sizes["spacing"] * 2,
                    vertical=sizes["spacing"]
                )
            ),
            on_click=self.handle_login,
        )

    def build_form(self) -> ft.Container:
        sizes = get_responsive_sizes(self.page.width)

        self.email_input = build_input_field(
            page_width=self.page.width, app_colors=self.app_colors, label="Email", icon=ft.Icons.EMAIL) # type: ignore
        self.password_input = build_input_field(
            page_width=self.page.width, app_colors=self.app_colors, label="Senha", icon=ft.Icons.LOCK, password=True, can_reveal_password=True) # type: ignore
        self.login_button: ft.OutlinedButton = self.build_login_button(sizes)
        self.error_text: ft.Text = ft.Text(
            color=ft.Colors.RED_400, size=sizes["font_size"], visible=False)
        self.title_text = ft.Text(
            "Bem-vindo",
            size=sizes["font_size"] * 2,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.WHITE
        )
        self.subtitle_text = ft.Text(
            "Faça o login para entrar",
            size=sizes["font_size"],
            color=ft.Colors.WHITE70,
            weight=ft.FontWeight.W_300
        )
        self.app_state: AppStateManager = self.page.app_state  # type: ignore [attr-defined]
        if self.app_state.user_name_text:
            self.app_state.user_name_text.visible = False
        if self.app_state.company_name_text_btn:
            self.app_state.company_name_text_btn.visible = False

        return ft.Container(
            alignment=ft.alignment.center,
            bgcolor=ft.Colors.BLACK,
            opacity=0.75,
            padding=ft.padding.all(sizes["form_padding"]),
            border_radius=10,  # Suaviza as bordas
            border=ft.border.all(color=self.app_colors['accent'], width=1),
            shadow=ft.BoxShadow(
                offset=ft.Offset(2, 2),  # Deslocamento horizontal e vertical
                blur_radius=16,  # Raio de desfoque
                spread_radius=0,  # Raio de propagação
                color="#F5F5F5",  # Cor da sombra
            ),
            width=500,
            height=700,
            content=ft.Column(
                controls=[
                    self.title_text,
                    self.subtitle_text,
                    ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                    self.email_input,
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    self.password_input,
                    self.error_text,
                    ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                    self.login_button,
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    ft.TextButton(
                        content=ft.Text(value="Criar uma conta",
                                        color=self.app_colors["accent"]),
                        on_click=lambda _: self.page.go('/signup'),
                    ),
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    ft.TextButton(
                        text="Voltar",
                        icon=ft.CupertinoIcons.BACK,
                        icon_color=self.app_colors['primary'],
                        style=ft.ButtonStyle(
                            color=self.app_colors["accent"]),
                        on_click=lambda _: self.page.go('/'),
                    )
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                scroll=ft.ScrollMode.AUTO,
            ),
        )

    def validate_form(self) -> str|None:
        email: str = self.email_input.value # type: ignore
        email = email.strip().lower()

        if not email:
            return "Por favor, insira seu email"
        if not validate_email(email):
            return "Email inválido"

        self.email_input.value = email # type: ignore

        # A classe Password lida com senhas inválidas
        if self.password_input.value:
            password = Password(self.password_input.value)
            if password.error:
                return password.error_message
        return None

    def handle_login(self, _):
        # Desabilita o botão imediatamente para evitar múltiplos cliques
        self.login_button.disabled = True # type: ignore
        self.login_button.update()

        # Detalhes de UX, com o estado de carregamento do botão
        try:
            # Faz a validação dos campos
            error = self.validate_form()
            if error:
                # Erro na validação dos campos, retorna sem fazer o login
                self.error_text.value = error
                self.error_text.visible = True
                self.error_text.update()
                return

            # Campos validados, segue com login
            # Oculta texto de mensagens de erro.
            self.error_text.visible = False
            self.error_text.update()

            result = user_controllers.handle_login(
                email=self.email_input.value, password=self.password_input.value) # type: ignore

            if result["status"] == "error":
                logger.error(f"Erro ao fazer login: {result['message']}")
                message_snackbar(
                    page=self.page, message=result["message"], message_type=MessageType.ERROR)
                return

            # Atualiza o estado do app com o novo usuário antes da navegação
            user = result["data"]["authenticated_user"]
            self.app_state.set_usuario(user) # type: ignore

            if user.empresa_id is None:
                self.app_state.clear_empresa_data() # type: ignore
                self.page.on_resized = None
                self.page.go('/home')
                return

            # Usuário tem empresa(s) registrada(s), obtem os dados da última empresa utilizada
            result = company_controllers.handle_get_empresas_by_id(id=user.empresa_id)

            if result["status"] == "error":
                user.empresa_id = None
                self.app_state.clear_empresa_data()
                self.page.on_resized = None
                self.page.go('/home')
                return

            cia: Empresa = result["data"]

            # Adiciona o empresa_id no state e publica-a
            if cia.status == RegistrationStatus.ACTIVE:
                self.app_state.set_empresa(cia.to_dict())
            else:
                user.empresa_id = None
                self.app_state.clear_empresa_data()

            self.page.on_resized = None
            self.page.go('/home')

        finally:
            # Reabilita o botão independente do resultado
            self.login_button.disabled = False
            self.login_button.update()

    def page_resize(self, e):
        sizes = get_responsive_sizes(e.page.width)

        # Atualiza tamanhos dos inputs
        self.email_input.width = sizes["input_width"]
        self.email_input.text_size = sizes["font_size"]

        self.password_input.width = sizes["input_width"]
        self.password_input.text_size = sizes["font_size"]

        # Atualiza o botão
        icon_control = self.login_button.content.controls[0] # type: ignore
        icon_control.size = sizes["icon_size"]

        text_control = self.login_button.content.controls[1] # type: ignore
        text_control.size = sizes["font_size"]

        self.login_button.content.spacing = sizes["spacing"] # type: ignore
        self.login_button.width = sizes["button_width"]

        self.login_button.style = ft.ButtonStyle(
            color=ft.Colors.WHITE,
            side=ft.BorderSide(
                color=self.app_colors['primary'],
                width=sizes["border_width"]
            ),
            padding=ft.padding.symmetric(
                horizontal=sizes["spacing"] * 2,
                vertical=sizes["spacing"]
            )
        )

        # Atualiza o container principal
        self.title_text.size = sizes["font_size"] * 2
        self.subtitle_text.size = sizes["font_size"]

        self.error_text.size = sizes["font_size"]

        # Atualiza o padding do container
        self.form.padding = ft.padding.all(sizes["form_padding"])

        self.form.update()

    def build(self) -> ft.Container:
        return self.form


def show_login_page(page: ft.Page) -> ft.View:
    '''
    Cria uma página Container de formulário de login de usuários.

    Args:
        page (ft.page): Página principal do app.

    Retorna:
        ft.Stack: Stack contendo imagem de fundo e formulário de login.
    '''
    login_view = LoginView(page)

    stack = ft.Stack(
        alignment=ft.alignment.center,
        controls=[
            # Imagem de fundo do login
            ft.Image(
                # Na web, flet 0.25.2 não carrega imagem via https, somente no destkop, imagens .svg não redimenciona, tive que usar .jpg
                src="images/estoquerapido_img_123e4567e89b12d3a456426614174000.jpg",
                fit=ft.ImageFit.CONTAIN,
                width=page.width,
                height=page.height
            ),
            # Formulário de login
            ft.Container(
                alignment=ft.alignment.center,
                content=login_view.build(),
                bgcolor=None,  # Define como transparente
            )
        ],
        expand=True
    )

    return ft.View(
        route='/login',
        controls=[stack],
        bgcolor=ft.Colors.BLACK,
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )
