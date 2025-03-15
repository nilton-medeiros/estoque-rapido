import flet as ft
from typing import Optional

import src.domains.usuarios.controllers.usuarios_controllers as usuarios_controllers

from src.domains.shared import PhoneNumber, NomePessoa
from src.shared import message_snackbar, MessageType, validate_password_strength, get_first_and_last_name, validate_email, validate_phone

from src.pages.partials.get_responsive_sizes import get_responsive_sizes
from src.pages.partials.build_input_responsive import build_input_field


class SignupView:
    def __init__(self, page: ft.Page):
        self.page = page
        self.name_input = None
        self.email_input = None
        self.phone_input = None
        self.password_input = None
        self.password_again_input = None
        self.error_text = None
        self.signup_button = None
        self.form = self.build_form()
        self.page.on_resized = self.page_resize

    # Botão Registrar
    def build_signup_button(self, sizes: dict) -> ft.OutlinedButton:
        return ft.OutlinedButton(
            content=ft.Row(
                controls=[
                    ft.Icon(
                        ft.Icons.APP_REGISTRATION,
                        color=ft.Colors.WHITE,
                        size=sizes["icon_size"]
                    ),
                    ft.Text(
                        value="Registrar",
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
                    color=ft.Colors.YELLOW_ACCENT_400,
                    width=sizes["border_width"]
                ),
                padding=ft.padding.symmetric(
                    horizontal=sizes["spacing"] * 2,
                    vertical=sizes["spacing"]
                )
            ),
            on_click=self.handle_signup,
            # animate=ft.animation.Animation(300, ft.AnimationCurve.EASE_OUT)
        )

    def build_form(self) -> ft.Container:
        sizes = get_responsive_sizes(self.page.width)

        self.name_input = build_input_field(
            sizes=sizes, label="Nome e Sobrenome", icon=ft.Icons.PERSON)
        self.email_input = build_input_field(
            sizes=sizes, label="Email", icon=ft.Icons.EMAIL)
        self.phone_input = build_input_field(
            sizes=sizes, label="Celular", hint_text="11987654321", icon=ft.Icons.PHONE)
        self.password_input = build_input_field(
            sizes=sizes, label="Senha", icon=ft.Icons.LOCK, password=True)
        self.password_again_input = build_input_field(
            sizes=sizes, label="Confirme a Senha", icon=ft.Icons.LOCK, password=True)
        self.signup_button = self.build_signup_button(sizes)
        self.error_text = ft.Text(
            color=ft.Colors.RED_400,
            size=sizes["font_size"],
            visible=False
        )

        # Debug: Dados Fakes como hardcord, remover isto em produção
        self.name_input.value = 'Angelina Jolie'
        self.email_input.value = 'ajolie@gmail.com'
        self.phone_input.value = '11987654321'
        self.password_input.value = 'Aj#45678'
        self.password_again_input.value = 'Aj#45678'

        self.page.user_name_text.visible=False  # Invisible, sem uso
        self.page.company_name_text_btn.visible=False # Invisible, sem uso

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
                        "Inscreva-se para continuar",
                        size=sizes["font_size"],
                        color=ft.Colors.WHITE70,
                        weight=ft.FontWeight.W_300
                    ),
                    self.page.user_name_text,   # Invisible, sem uso
                    self.page.company_name_text_btn,   # Invisible, sem uso
                    ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                    self.name_input,
                    ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                    self.email_input,
                    ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                    self.phone_input,
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    self.password_input,
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    self.password_again_input,
                    self.error_text,
                    ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                    self.signup_button,
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    ft.TextButton(
                        content=ft.Text(value="Já tenho uma conta", color=ft.Colors.YELLOW_ACCENT_400),
                        on_click=lambda _: self.page.go('/login'),
                    ),
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    ft.TextButton(
                        text="Voltar",
                        icon=ft.CupertinoIcons.BACK,
                        icon_color=ft.Colors.YELLOW_ACCENT_400,
                        style=ft.ButtonStyle(color=ft.Colors.YELLOW_ACCENT_400),
                        on_click=lambda _: self.page.go('/'),
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
        )

    def validate_form(self) -> Optional[str]:
        name = self.name_input.value
        email = self.email_input.value
        email = email.strip().lower()
        phone = self.phone_input.value
        password = self.password_input.value
        password_again = self.password_again_input.value

        if not name or len(name.strip()) < 3:
            return "O nome deve ter pelo menos 3 caracteres"
        if not email:
            return "Por favor, insira seu email"
        if not validate_email(email):
            return "Email inválido"

        phone_msg = validate_phone(phone)

        if not phone_msg.startswith("OK"):
            return phone_msg

        self.email_input.value = email

        password_msg = validate_password_strength(password)
        if password_msg.upper() != "SENHA FORTE":
            return password_msg

        if password != password_again:
            return "As senhas não coincidem!"

        return None

    # Executa ação do botão Registrar
    async def handle_signup(self, _):
        # Desabilita o botão imediatamente para evitar múltiplos cliques
        self.signup_button.disabled = True
        self.signup_button.update()

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

            first_name, last_name = get_first_and_last_name(
                self.name_input.value)

            usuario = Usuario(
                email=self.email_input.value,
                name=NomePessoa(first_name, last_name),
                phone_number=PhoneNumber(self.phone_input.value),
                profile='admin',
            )

            result = await usuarios_controllers.handle_save_usuarios(
                usuario=usuario,
                create_new=True,
                password=self.password_input.value
            )

            if not result["is_error"]:
                usuario.id = result["user_id"]
                # Atualiza o estado do app com o novo usuário antes da navegação
                await self.page.app_state.set_usuario({
                    "id": usuario.id,
                    "name": usuario.name,
                    "email": usuario.email,
                    "phone_number": usuario.phone_number,
                    "profile": usuario.profile,
                    "companies": usuario.companies,
                    "photo": usuario.photo,
                    # Adicione outros dados relevantes do usuário
                })

                # No registro de um novo usuario, não há empresas definidas para este usuário
                await self.page.app_state.set_empresa({
                        "id": "",
                        "name": "NEUMHUMA EMPRESA SELECIONADA",
                        "corporate_name": "",
                        "cnpj": "",
                        "ie": "",
                        "store_name": "Matriz",
                        "im": "",
                        "address": None,
                        "size": None,
                        "fiscal": None,
                        "logo_url": None,
                        "payment_gateway": None,
                })
                message_snackbar(page=self.page, message=result["message"], message_type=MessageType.SUCCESS)
                self.page.on_resized = None
                self.page.go('/home')
            else:
                message_snackbar(page=self.page, message=result["message"], message_type=MessageType.ERROR)
        finally:
            # Reabilita o botão independente do resultado
            self.signup_button.disabled = False
            self.signup_button.update()

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
        icon_control = self.signup_button.content.controls[0]
        icon_control.size = sizes["icon_size"]

        text_control = self.signup_button.content.controls[1]
        text_control.size = sizes["font_size"]

        self.signup_button.content.spacing = sizes["spacing"]
        self.signup_button.width = sizes["button_width"]

        self.signup_button.style = ft.ButtonStyle(
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


def signup(page: ft.Page):
    '''
    Cria uma página Container de formulário de registro para novos usuários.

    Args:
        page (ft.page): Página principal do app.

    Retorna:
        ft.Stack: Stack contendo imagem de fundo e formulário de registro.
    '''
    signup_view = SignupView(page)

    return ft.Stack(
        alignment=ft.alignment.center,
        controls=[
            # Imagem de fundo - background
            ft.Image(
                # Na web, flet 0.26.0 não carrega imagem via https, somente no destkop, imagens .svg não redimenciona, tive que usar .jpg
                src="images/estoquerapido_img_123e4567e89b12d3a456426614174000.jpg",
                fit=ft.ImageFit.CONTAIN,
                width=page.width,
                height=page.height
            ),
            ft.Container(
                alignment=ft.alignment.center,
                content=signup_view.build(),
                bgcolor=None,  # Define como transparente
            )
        ],
        expand=True
    )
