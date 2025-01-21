import flet as ft
from typing import Optional

from src.domain.models.nome_pessoa import NomePessoa
from src.domain.models.phone_number import PhoneNumber
from src.controllers.user_controller import handle_save_user
from src.utils.message_snackbar import MessageType, message_snackbar
from src.utils.field_validation_functions import get_first_and_last_name, validate_email, validate_password_strength, validate_phone


class SignupView:
    def __init__(self, page: ft.Page):
        self.page = page
        self.name_input = None
        self.email_input = None
        self.phone_input = None
        self.password_input = None
        self.password_again_input = None
        self.error_text = None
        self.btn_signup = None
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
                    color=ft.Colors.BLUE_400,
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

    def build_input_field(self, sizes: dict, label: str, icon: str, hint_text: str = None, password: bool = False) -> ft.TextField:
        return ft.TextField(
            label=label,
            hint_text=hint_text,
            width=sizes["input_width"],
            text_size=sizes["font_size"],
            password=password,
            can_reveal_password=password,
            border_color=ft.Colors.YELLOW_ACCENT_400,
            focused_border_color=ft.Colors.YELLOW_ACCENT,
            prefix=ft.Icon(
                name=icon,
                color=ft.Colors.YELLOW_ACCENT_400,
                size=sizes["icon_size"]
            ),
            text_align=ft.TextAlign.LEFT,
            bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
            label_style=ft.TextStyle(
                color=ft.Colors.YELLOW_ACCENT_400,          # Cor do label igual à borda
                weight=ft.FontWeight.W_500                  # Label um pouco mais grosso
            ),
            hint_style=ft.TextStyle(
                color=ft.Colors.YELLOW_ACCENT_200,          # Cor do placeholder mais visível
                weight=ft.FontWeight.W_300                  # Placeholder um pouco mais fino
            ),
            cursor_color=ft.Colors.YELLOW_ACCENT_400,
            focused_color=ft.Colors.YELLOW_ACCENT,
            text_style=ft.TextStyle(                        # Estilo do texto digitado
                color=ft.Colors.WHITE,
                weight=ft.FontWeight.W_400
            )
        )

    def build_form(self) -> ft.Container:
        sizes = self.get_responsive_sizes(self.page.width)

        self.name_input = self.build_input_field(
            sizes=sizes, label="Nome e Sobrenome", icon=ft.Icons.PERSON)
        self.email_input = self.build_input_field(
            sizes=sizes, label="Email", icon=ft.Icons.EMAIL)
        self.phone_input = self.build_input_field(
            sizes=sizes, label="Celular", hint_text="11987654321", icon=ft.Icons.PHONE)
        self.password_input = self.build_input_field(
            sizes=sizes, label="Senha", icon=ft.Icons.LOCK, password=True)
        self.password_again_input = self.build_input_field(
            sizes=sizes, label="Confirme a Senha", icon=ft.Icons.LOCK, password=True)
        self.btn_signup = self.build_signup_button(sizes)
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
                    self.btn_signup,
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    ft.TextButton(
                        text="Já tenho uma conta",
                        on_click=lambda _: self.page.go('/login'),
                    )
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
        )

    def validate_form(self) -> Optional[str]:
        name = self.name_input.value
        email = self.email_input.value
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

        password_msg = validate_password_strength(password)
        if password_msg.upper() != "SENHA FORTE":
            return password_msg

        if password != password_again:
            return "As senhas não coincidem!"

        return None

    async def handle_signup(self, _):
        # Desabilita o botão imediatamente para evitar múltiplos cliques
        self.btn_signup.disabled = True
        self.btn_signup.update()

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

            result = await handle_save_user(
                email=self.email_input.value,
                first_name=first_name,
                last_name=last_name,
                phone=self.phone_input.value,
                password=self.password_input.value,
                profile='admin'
            )

            if not result["is_error"]:
                # Atualiza o estado do app com o novo usuário antes da navegação
                user = result["user"]
                await self.page.app_state.set_user({
                    "id": user.id,
                    "name": NomePessoa(first_name, last_name),
                    "email": user.email,
                    "phone_number": PhoneNumber(self.phone_input.value),
                    "profile": user.profile,
                    # Adicione outros dados relevantes do usuário
                })

                await self.page.app_state.set_company({
                    "id": 'emp_erwerwe34r5ir8u4jdf',
                    "name": 'SISTROM SISTEMA WEB',
                })

                self.page.pubsub.send_all("user_updated")

            color = MessageType.ERROR if result["is_error"] else MessageType.SUCCESS
            message_snackbar(
                page=self.page, message=result["message"], message_type=color)

            if not result["is_error"]:
                self.page.go('/home')

        finally:
            # Reabilita o botão independente do resultado
            self.btn_signup.disabled = False
            self.btn_signup.update()

    def page_resize(self, e):
        sizes = self.get_responsive_sizes(e.page.width)

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
        icon_control = self.btn_signup.content.controls[0]
        icon_control.size = sizes["icon_size"]

        text_control = self.btn_signup.content.controls[1]
        text_control.size = sizes["font_size"]

        self.btn_signup.content.spacing = sizes["spacing"]
        self.btn_signup.width = sizes["button_width"]

        self.btn_signup.style = ft.ButtonStyle(
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
        controls=[
            ft.Image(
                src="/images/estoquerapido_img_123e4567e89b12d3a456426614174000.jpg",
                fit=ft.ImageFit.COVER,
                expand=True,
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
