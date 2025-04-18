import logging

import flet as ft
from typing import Optional

from src.domains.shared.nome_pessoa import NomePessoa
from src.domains.shared.password import Password
from src.pages.partials.get_responsive_sizes import get_responsive_sizes
from src.pages.partials.build_input_responsive import build_input_field

from src.shared import MessageType, message_snackbar, validate_email
from src.shared.config import app_colors

import src.domains.empresas.controllers.empresas_controllers as empresas_controllers
import src.domains.usuarios.controllers.usuarios_controllers as usuarios_controllers

from src.domains.empresas.models.empresa_model import Empresa

logger = logging.getLogger(__name__)


class LoginView:
    def __init__(self, page: ft.Page):
        self.page = page
        self.email_input = None
        self.password_input = None
        self.error_text = None
        self.login_button = None
        self.form = self.build_form()
        self.page.on_resized = self.page_resize

        self.page.update()

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
                tight=True
            ),
            width=sizes["button_width"],
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                side=ft.BorderSide(
                    color=app_colors["accent"],
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
            page_width=self.page.width, label="Email", icon=ft.Icons.EMAIL)
        self.password_input = build_input_field(
            page_width=self.page.width, label="Senha", icon=ft.Icons.LOCK, password=True, can_reveal_password=True)
        self.login_button = self.build_login_button(sizes)
        self.error_text = ft.Text(
            color=ft.Colors.RED_400, size=sizes["font_size"], visible=False)

        # Debug: Dados Fakes como hardcord, remover isto em produção
        self.email_input.value = 'ajolie@gmail.com'
        self.password_input.value = 'Aj#45678'

        self.page.user_name_text.visible = False  # Invisible, sem uso
        self.page.company_name_text_btn.visible = False  # Invisible, sem uso

        print(f"Debug  -> login (app_colors): {app_colors}")

        return ft.Container(
            alignment=ft.alignment.center,
            bgcolor=ft.Colors.BLACK,
            opacity=0.75,
            padding=ft.padding.all(sizes["form_padding"]),
            border_radius=10,  # Suaviza as bordas
            border=ft.border.all(color=app_colors['accent'], width=1),
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
                    self.page.user_name_text,   # Invisible, sem uso
                    self.page.company_name_text_btn,   # Invisible, sem uso
                    ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                    self.login_button,
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    ft.TextButton(
                        content=ft.Text(value="Criar uma conta",
                                        color=app_colors["accent"]),
                        on_click=lambda _: self.page.go('/signup'),
                    ),
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    ft.TextButton(
                        text="Voltar",
                        icon=ft.CupertinoIcons.BACK,
                        icon_color=app_colors['primary'],
                        style=ft.ButtonStyle(
                            color=app_colors["accent"]),
                        on_click=lambda _: self.page.go('/'),
                    )
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
        )

    def validate_form(self) -> Optional[str]:
        email = self.email_input.value
        email = email.strip().lower()

        if not email:
            return "Por favor, insira seu email"
        if not validate_email(email):
            return "Email inválido"

        self.email_input.value = email

        # ToDo: Passar esta responsabilidade para a classe Password
        password = self.password_input.value

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
                # Erro na validação dos campos, retorna sem fazer o login
                self.error_text.value = error
                self.error_text.visible = True
                self.error_text.update()
                return

            # Campos validados, segue com login
            # Oculta texto de mensagens de erro.
            self.error_text.visible = False
            self.error_text.update()

            result = await usuarios_controllers.handle_login_usuarios(
                email=self.email_input.value, password=self.password_input.value)

            if result["is_error"]:
                message_snackbar(
                    page=self.page, message=result["message"], message_type=MessageType.ERROR)
                return

            # Atualiza o estado do app com o novo usuário antes da navegação
            user = result["authenticated_user"]

            self.page.app_state.set_usuario(user.to_dict())

            print(
                f"Usuário autenticado: {user.name.nome_completo} ({user.email})")

            if user.empresa_id is None:
                print("Usuário não tem empresa registrada.")
                self.page.app_state.clear_empresa_data()
                self.page.on_resized = None
                print('Redirecionando para /home')
                self.page.go('/home')
                return

            print(f"Usuário tem empresa registrada: {user.empresa_id} ({user.name.iniciais})")
            # Usuário tem empresa(s) registrada(s), obtem os dados da última empresa utilizada
            result = await empresas_controllers.handle_get_empresas(id=user.empresa_id)

            if result["is_error"]:
                message_snackbar(
                    page=self.page, message=result["message"], message_type=MessageType.ERROR)
                return

            cia: Empresa = result["empresa"]

            # Adiciona o empresa_id no state e publíca-a
            self.page.app_state.set_empresa(cia.to_dict())

            print(f"Empresa atual registrada: {cia.corporate_name}")

            self.page.on_resized = None
            print('Redirecionando para /home')
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
        icon_control = self.login_button.content.controls[0]
        icon_control.size = sizes["icon_size"]

        text_control = self.login_button.content.controls[1]
        text_control.size = sizes["font_size"]

        self.login_button.content.spacing = sizes["spacing"]
        self.login_button.width = sizes["button_width"]

        self.login_button.style = ft.ButtonStyle(
            color=ft.Colors.WHITE,
            side=ft.BorderSide(
                color=app_colors['primary'],
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
