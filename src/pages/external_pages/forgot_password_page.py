import logging
import asyncio
from typing import Dict, Any

import flet as ft

from src.domains.shared.context import session
from src.domains.shared.context.session import get_session_colors
from src.pages.partials import get_responsive_sizes, build_input_field
from src.services.states.app_state_manager import AppStateManager
from src.shared.utils import MessageType, message_snackbar, validate_email

# Importações para envio de email
from src.services.emails.send_email import (
    ModernEmailSender,
    EmailMessage,
    create_email_config_from_env,
    EmailValidationError,
    EmailAuthenticationError,
    EmailConnectionError,
    EmailRecipientError,
    EmailSendError
)

import src.domains.usuarios.controllers.usuarios_controllers as user_controllers

logger = logging.getLogger(__name__)


class ForgotPasswordView:
    """
    Classe responsável pela interface de recuperação de senha

    Analogia: Como um balcão de atendimento especializado em recuperação
    de senhas, onde o usuário fornece seu email e recebe uma nova senha
    """

    def __init__(self, page: ft.Page):
        self.page: ft.Page = page
        self.email_input: ft.TextField
        self.error_text: ft.Text
        self.send_button: ft.OutlinedButton
        self.title_text: ft.Text
        self.subtitle_text: ft.Text
        self.info_text: ft.Text
        self.app_colors = get_session_colors(page)
        self.page_width: int = session.get_current_page_width(page)
        self.form = self.build_form()
        self.page.on_resized = self.page_resize

        # Estado para controle de envio
        self.is_sending = False

    def build_send_button(self, sizes: dict) -> ft.OutlinedButton:
        """Constrói o botão de envio de senha"""
        return ft.OutlinedButton(
            content=ft.Row(
                controls=[
                    ft.Icon(
                        ft.Icons.SEND,
                        color=ft.Colors.WHITE,
                        size=sizes["icon_size"]
                    ),
                    ft.Text(
                        value="Enviar Senha",
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
            on_click=self.handle_send_password,
        )

    def build_form(self) -> ft.Container:
        """Constrói o formulário de recuperação de senha"""
        sizes = get_responsive_sizes(self.page.width)

        self.email_input = build_input_field(
            page_width=self.page_width,
            app_colors=self.app_colors,
            label="Email",
            icon=ft.Icons.EMAIL
        ) # type: ignore

        self.send_button: ft.OutlinedButton = self.build_send_button(sizes)

        self.error_text: ft.Text = ft.Text(
            color=ft.Colors.RED_400,
            size=sizes["font_size"],
            visible=False
        )

        self.title_text = ft.Text(
            "Recuperar Senha",
            size=sizes["font_size"] * 2,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.WHITE
        )

        self.subtitle_text = ft.Text(
            "Esqueceu sua senha?",
            size=sizes["font_size"] * 1.2,
            color=ft.Colors.WHITE70,
            weight=ft.FontWeight.W_400
        )

        self.info_text = ft.Text(
            "Digite seu email abaixo e enviaremos uma nova senha temporária.",
            size=sizes["font_size"] * 0.9,
            color=ft.Colors.WHITE60,
            weight=ft.FontWeight.W_300,
            text_align=ft.TextAlign.CENTER,
        )

        self.app_state: AppStateManager = self.page.app_state  # type: ignore [attr-defined]

        # Esconde elementos do header se existirem
        if self.app_state.user_name_text:
            self.app_state.user_name_text.visible = False
        if self.app_state.company_name_text_btn:
            self.app_state.company_name_text_btn.visible = False

        return ft.Container(
            alignment=ft.alignment.center,
            bgcolor=ft.Colors.BLACK,
            opacity=0.75,
            padding=ft.padding.all(sizes["form_padding"]),
            border_radius=10,
            border=ft.border.all(color=self.app_colors['accent'], width=1),
            shadow=ft.BoxShadow(
                offset=ft.Offset(2, 2),
                blur_radius=16,
                spread_radius=0,
                color="#F5F5F5",
            ),
            width=500,
            height=650,
            content=ft.Column(
                controls=[
                    self.title_text,
                    self.subtitle_text,
                    ft.Divider(height=15, color=ft.Colors.TRANSPARENT),
                    self.info_text,
                    ft.Divider(height=25, color=ft.Colors.TRANSPARENT),
                    self.email_input,
                    self.error_text,
                    ft.Divider(height=25, color=ft.Colors.TRANSPARENT),
                    self.send_button,
                    ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                    ft.Row(
                        controls=[
                            ft.TextButton(
                                content=ft.Text(
                                    value="Lembrei da senha",
                                    color=self.app_colors["accent"]
                                ),
                                on_click=lambda _: self.page.go('/login'),
                            ),
                            ft.Text(" | ", color=ft.Colors.WHITE60),
                            ft.TextButton(
                                content=ft.Text(
                                    value="Criar conta",
                                    color=self.app_colors["accent"]
                                ),
                                on_click=lambda _: self.page.go('/signup'),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=5,
                    ),
                    ft.Divider(height=15, color=ft.Colors.TRANSPARENT),
                    ft.TextButton(
                        text="Voltar",
                        icon=ft.CupertinoIcons.BACK,
                        icon_color=self.app_colors['primary'],
                        style=ft.ButtonStyle(
                            color=self.app_colors["accent"]
                        ),
                        on_click=lambda _: self.page.go('/login'),
                    )
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                scroll=ft.ScrollMode.AUTO,
            ),
        )

    def validate_form(self) -> str | None:
        """
        Valida o formulário de recuperação de senha

        Returns:
            str | None: Mensagem de erro se houver, None se válido
        """
        email: str = self.email_input.value # type: ignore
        email = email.strip().lower()

        if not email:
            return "Por favor, insira seu email"

        if not validate_email(email):
            return "Email inválido"

        self.email_input.value = email # type: ignore
        return None

    def generate_temporary_password(self) -> str:
        """
        Gera uma senha temporária segura

        Analogia: Como um gerador de chaves temporárias que cria
        uma combinação única e segura
        """
        import secrets
        import string

        # Gera senha com 8 caracteres: letras maiúsculas, minúsculas e números
        characters = string.ascii_letters + string.digits
        temp_password = ''.join(secrets.choice(characters) for _ in range(8))

        return temp_password

    def create_password_reset_email(self, user_email: str, temp_password: str) -> EmailMessage:
        """
        Cria a mensagem de email para recuperação de senha

        Args:
            user_email: Email do usuário
            temp_password: Senha temporária gerada

        Returns:
            EmailMessage: Objeto de email formatado
        """
        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #f8f9fa; padding: 20px;">
            <div style="background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: {self.app_colors.get('primary', '#007bff')}; margin-bottom: 10px;">🔐 Estoque Rápido</h1>
                    <h2 style="color: #2c3e50; margin: 0;">Recuperação de Senha</h2>
                </div>

                <p style="color: #333; font-size: 16px; line-height: 1.6;">
                    Olá! Recebemos uma solicitação para redefinir a senha da sua conta.
                </p>

                <div style="background-color: #e3f2fd; border-left: 4px solid {self.app_colors.get('accent', '#007bff')}; padding: 20px; margin: 25px 0; border-radius: 5px;">
                    <h3 style="color: #1976d2; margin: 0 0 15px 0;">📧 Seus dados de acesso:</h3>
                    <p style="margin: 8px 0;"><strong>Email:</strong> {user_email}</p>
                    <p style="margin: 8px 0;">
                        <strong>Senha temporária:</strong>
                        <code style="background-color: #fff; padding: 8px 12px; border: 1px solid #ddd; border-radius: 4px; font-size: 16px; font-weight: bold; color: #c62828;">
                            {temp_password}
                        </code>
                    </p>
                </div>

                <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 20px; border-radius: 8px; margin: 25px 0;">
                    <p style="margin: 0; color: #856404; font-weight: 500;">
                        <strong>⚠️ IMPORTANTE:</strong> Por segurança, altere sua senha assim que fizer login!
                    </p>
                </div>

                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://estoque-rapido.com/login"
                       style="background-color: {self.app_colors.get('accent', '#007bff')}; color: white; padding: 15px 30px;
                              text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 16px; display: inline-block;">
                        🚀 Fazer Login Agora
                    </a>
                </div>

                <hr style="margin: 30px 0; border: none; border-top: 1px solid #dee2e6;">

                <div style="text-align: center;">
                    <p style="font-size: 14px; color: #6c757d; margin: 5px 0;">
                        Se você não solicitou esta alteração, ignore este email.
                    </p>
                    <p style="font-size: 12px; color: #6c757d; margin: 5px 0;">
                        Este é um email automático do sistema Estoque Rápido. Não responda este email.
                    </p>
                </div>
            </div>
        </div>
        """

        text_body = f"""
        ESTOQUE RÁPIDO - Recuperação de Senha

        Olá! Recebemos uma solicitação para redefinir a senha da sua conta.

        Seus dados de acesso:
        Email: {user_email}
        Senha temporária: {temp_password}

        ⚠️ IMPORTANTE: Por segurança, altere sua senha assim que fizer login!

        Acesse: https://estoque-rapido.com/login

        Se você não solicitou esta alteração, ignore este email.

        --
        Sistema Estoque Rápido - Email automático, não responda.
        """

        return EmailMessage(
            subject="🔐 Estoque Rápido - Sua nova senha temporária",
            recipients=[user_email],
            body_text=text_body,
            body_html=html_body
        )

    async def send_password_email_async(self, user_email: str, temp_password: str) -> Dict[str, Any]:
        """
        Envia email de recuperação de senha de forma assíncrona

        Args:
            user_email: Email do usuário
            temp_password: Senha temporária

        Returns:
            Dict com resultado do envio
        """
        try:
            # Cria configuração do email
            config = create_email_config_from_env()
            email_sender = ModernEmailSender(config)

            # Cria a mensagem
            email_message = self.create_password_reset_email(user_email, temp_password)

            # Envia o email
            await email_sender.send_email_async(email_message)

            logger.info(f"Email de recuperação enviado para: {user_email}")
            return {
                "success": True,
                "message": "Email enviado com sucesso",
                "user_message": "Verifique seu email para obter a nova senha temporária"
            }

        except EmailValidationError as e:
            logger.error(f"Erro de validação no email: {e}")
            if e.field == "email_format":
                return {
                    "success": False,
                    "error": "invalid_email",
                    "user_message": "Email inválido. Verifique o endereço digitado."
                }
            else:
                return {
                    "success": False,
                    "error": "validation_error",
                    "user_message": "Dados inválidos. Tente novamente."
                }

        except EmailAuthenticationError as e:
            logger.error(f"Erro de autenticação no servidor de email: {e}")
            return {
                "success": False,
                "error": "email_config_error",
                "user_message": "Falha temporária no sistema. Tente novamente em alguns minutos."
            }

        except EmailConnectionError as e:
            logger.error(f"Erro de conexão com servidor de email: {e}")
            return {
                "success": False,
                "error": "connection_error",
                "user_message": "Servidor de email indisponível. Tente novamente mais tarde."
            }

        except EmailRecipientError as e:
            logger.error(f"Email do destinatário rejeitado: {e}")
            return {
                "success": False,
                "error": "recipient_rejected",
                "user_message": "Email rejeitado pelo servidor. Verifique se o endereço está correto."
            }

        except EmailSendError as e:
            logger.error(f"Erro no envio de email: {e}")
            if e.error_type == "QUOTA_EXCEEDED":
                return {
                    "success": False,
                    "error": "quota_exceeded",
                    "user_message": "Limite de emails atingido. Tente novamente em 1 hora."
                }
            elif e.error_type == "SPAM_REJECTED":
                return {
                    "success": False,
                    "error": "spam_detected",
                    "user_message": "Email rejeitado por filtro de spam. Entre em contato com suporte."
                }
            else:
                return {
                    "success": False,
                    "error": "send_error",
                    "user_message": "Falha no envio. Tente novamente."
                }

        except Exception as e:
            logger.error(f"Erro inesperado no envio de email: {e}")
            return {
                "success": False,
                "error": "unexpected_error",
                "user_message": "Erro interno do sistema. Entre em contato com suporte."
            }

    def handle_send_password(self, _):
        """
        Manipula o clique no botão de envio de senha

        Analogia: Como um processo de solicitação em um banco -
        valida os dados, gera nova senha e envia por email
        """
        if self.is_sending:
            return  # Evita múltiplos cliques

        # Desabilita o botão e mostra estado de carregamento
        self.is_sending = True
        self.send_button.disabled = True

        # Atualiza texto do botão para mostrar carregamento
        original_text = self.send_button.content.controls[1].value # type: ignore
        self.send_button.content.controls[1].value = "Enviando..." # type: ignore
        self.send_button.update()

        try:
            # Valida o formulário
            error = self.validate_form()
            if error:
                self.error_text.value = error
                self.error_text.visible = True
                self.error_text.update()
                return

            # Remove mensagens de erro anteriores
            self.error_text.visible = False
            self.error_text.update()

            email = self.email_input.value.strip().lower() # type: ignore

            # Verifica se o usuário existe no sistema
            user_result = user_controllers.handle_get_user_by_email(email)

            if user_result["status"] == "error":
                logger.warning(f"Tentativa de recuperação para email inexistente: {email}")
                # Por segurança, não revelamos se o email existe ou não
                message_snackbar(
                    page=self.page,
                    message="Se o email existir em nosso sistema, você receberá as instruções de recuperação.",
                    message_type=MessageType.INFO
                )
                return

            user = user_result["data"]["usuario"]

            # Gera nova senha temporária
            temp_password = self.generate_temporary_password()

            # Atualiza a senha do usuário no banco de dados
            update_result = user_controllers.handle_update_user_password(
                user_id=user.id,
                new_password=temp_password
            )

            if update_result["status"] == "error":
                logger.error(f"Erro ao atualizar senha para usuário {user.id}: {update_result['message']}")
                message_snackbar(
                    page=self.page,
                    message="Erro interno. Tente novamente mais tarde.",
                    message_type=MessageType.ERROR
                )
                return

            # Envia email com nova senha (método síncrono para compatibility com Flet)
            def run_async_email():
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # Se já há um loop rodando, usa thread pool
                        import concurrent.futures
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            future = executor.submit(
                                lambda: asyncio.run(self.send_password_email_async(email, temp_password))
                            )
                            return future.result(timeout=30)  # Timeout de 30 segundos
                    else:
                        return asyncio.run(self.send_password_email_async(email, temp_password))
                except RuntimeError:
                    # Fallback para método síncrono direto
                    return self.send_password_email_sync_direct(email, temp_password)

            email_result = run_async_email()

            if email_result["success"]:
                logger.info(f"Senha temporária enviada com sucesso para: {email}")
                message_snackbar(
                    page=self.page,
                    message=email_result["user_message"],
                    message_type=MessageType.SUCCESS
                )

                # Redireciona para login após sucesso
                self.page.go('/login')

            else:
                logger.error(f"Falha no envio de email: {email_result['error']}")
                message_snackbar(
                    page=self.page,
                    message=email_result["user_message"],
                    message_type=MessageType.ERROR
                )

        except Exception as e:
            logger.error(f"Erro inesperado na recuperação de senha: {e}")
            message_snackbar(
                page=self.page,
                message="Erro interno do sistema. Tente novamente mais tarde.",
                message_type=MessageType.ERROR
            )

        finally:
            # Restaura o estado original do botão
            self.is_sending = False
            self.send_button.disabled = False
            self.send_button.content.controls[1].value = original_text # type: ignore
            self.send_button.update()

    def send_password_email_sync_direct(self, user_email: str, temp_password: str) -> Dict[str, Any]:
        """
        Método de fallback síncrono direto para envio de email

        Args:
            user_email: Email do usuário
            temp_password: Senha temporária

        Returns:
            Dict com resultado do envio
        """
        try:
            config = create_email_config_from_env()
            email_sender = ModernEmailSender(config)

            email_message = self.create_password_reset_email(user_email, temp_password)

            result = email_sender.send_email_sync_direct(email_message)

            logger.info(f"Email de recuperação enviado (sync direct) para: {user_email}")
            return {
                "success": True,
                "message": "Email enviado com sucesso",
                "user_message": "Verifique seu email para obter a nova senha temporária"
            }

        except Exception as e:
            logger.error(f"Erro no envio síncrono direto: {e}")
            return {
                "success": False,
                "error": "sync_send_error",
                "user_message": "Falha no envio. Tente novamente."
            }

    def page_resize(self, e):
        """Manipula o redimensionamento da página"""
        self.page_width: int = session.get_current_page_width(e.page)
        sizes = get_responsive_sizes(self.page_width)

        # Atualiza input de email
        self.email_input.width = sizes["input_width"]
        self.email_input.text_size = sizes["font_size"]

        # Atualiza botão de envio
        icon_control = self.send_button.content.controls[0] # type: ignore
        icon_control.size = sizes["icon_size"]

        text_control = self.send_button.content.controls[1] # type: ignore
        text_control.size = sizes["font_size"]

        self.send_button.content.spacing = sizes["spacing"] # type: ignore
        self.send_button.width = sizes["button_width"]

        self.send_button.style = ft.ButtonStyle(
            color=ft.Colors.WHITE,
            side=ft.BorderSide(
                color=self.app_colors['accent'],
                width=sizes["border_width"]
            ),
            padding=ft.padding.symmetric(
                horizontal=sizes["spacing"] * 2,
                vertical=sizes["spacing"]
            )
        )

        # Atualiza textos
        self.title_text.size = sizes["font_size"] * 2
        self.subtitle_text.size = sizes["font_size"] * 1.2
        self.info_text.size = sizes["font_size"] * 0.9
        self.error_text.size = sizes["font_size"]

        # Atualiza padding do container
        self.form.padding = ft.padding.all(sizes["form_padding"])
        self.form.update()

    def build(self) -> ft.Container:
        """Retorna o formulário construído"""
        return self.form


def show_forgot_pswd_page(page: ft.Page) -> ft.View:
    """
    Cria a página de recuperação de senha

    Args:
        page (ft.Page): Página principal do app

    Returns:
        ft.View: View contendo a tela de recuperação de senha

    Analogia: Como configurar um balcão especializado de atendimento
    para recuperação de senhas em uma empresa
    """
    forgot_password_view = ForgotPasswordView(page)

    stack = ft.Stack(
        alignment=ft.alignment.center,
        controls=[
            # Imagem de fundo (mesma do login)
            ft.Image(
                src="images/estoquerapido_img_123e4567e89b12d3a456426614174000.jpg",
                fit=ft.ImageFit.CONTAIN,
                width=page.width,
                height=page.height
            ),
            # Formulário de recuperação de senha
            ft.Container(
                alignment=ft.alignment.center,
                content=forgot_password_view.build(),
                bgcolor=None,  # Transparente
            )
        ],
        expand=True
    )

    return ft.View(
        route='/forgot-password',
        controls=[stack],
        bgcolor=ft.Colors.BLACK,
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )