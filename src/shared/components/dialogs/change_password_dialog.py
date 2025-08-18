from typing import Any
import flet as ft

from src.domains.shared.context.session import get_session_colors
from src.domains.usuarios.controllers import usuarios_controllers as user_controllers
from src.domains.usuarios.models import Usuario

class ChangePasswordDialog:
    def __init__(self, page: ft.Page, user: Usuario):
        self.page = page
        self.colors = get_session_colors(page)
        self.dialog = None
        self.user = user

        self._create_dialog()

    def _create_dialog(self):
        # Campos de entrada
        self.current_password_field = ft.TextField(
            label="Senha Atual",
            password=True,
            can_reveal_password=True,
            width=300,
            border_color=self.colors['primary'],
            focused_border_color=self.colors['accent'],
            cursor_color=self.colors['primary'],
            selection_color=self.colors['container'],
            prefix_icon=ft.Icons.LOCK_OUTLINE,
            helper_text="Digite sua senha atual para confirmar",
            helper_style=ft.TextStyle(color=self.colors['primary'], size=12),
        )

        self.new_password_field = ft.TextField(
            label="Nova Senha",
            password=True,
            can_reveal_password=True,
            width=300,
            border_color=self.colors['primary'],
            focused_border_color=self.colors['accent'],
            cursor_color=self.colors['primary'],
            selection_color=self.colors['container'],
            prefix_icon=ft.Icons.LOCK,
            helper_text="Mínimo 8 caracteres",
            helper_style=ft.TextStyle(color=self.colors['primary'], size=12),
            enable_suggestions=False,
            autocorrect=False,
            autofill_hints=ft.AutofillHint.NEW_PASSWORD,
        )

        self.confirm_password_field = ft.TextField(
            label="Confirmar Nova Senha",
            password=True,
            can_reveal_password=True,
            width=300,
            border_color=self.colors['primary'],
            focused_border_color=self.colors['accent'],
            cursor_color=self.colors['primary'],
            selection_color=self.colors['container'],
            prefix_icon=ft.Icons.LOCK_RESET,
            helper_text="Digite novamente a nova senha",
            helper_style=ft.TextStyle(color=self.colors['primary'], size=12),
            autofill_hints=ft.AutofillHint.NEW_PASSWORD,
        )

        # Mensagem de erro/sucesso
        self.message_text = ft.Text(
            "",
            color=ft.Colors.RED_400,
            size=12,
            visible=False,
        )

        # Botões de ação
        save_button = ft.ElevatedButton(
            text="Salvar",
            icon=ft.Icons.SAVE,
            bgcolor=self.colors['primary'],
            color=ft.Colors.WHITE,
            on_click=self._save_password,
            style=ft.ButtonStyle(
                elevation=2,
                animation_duration=200,
            )
        )

        cancel_button = ft.TextButton(
            text="Cancelar",
            icon=ft.Icons.CANCEL,
            on_click=self._cancel_dialog,
            style=ft.ButtonStyle(
                color=self.colors['primary'],
                overlay_color=self.colors['container'],
            )
        )

        # Criação do dialog
        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.SECURITY, color=self.colors['primary']),
                ft.Text(
                    "Alterar Senha",
                    weight=ft.FontWeight.BOLD,
                    color=self.colors['primary'],
                ),
            ]),
            content=ft.Container(
                content=ft.Column([
                    self.current_password_field,
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    self.new_password_field,
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    self.confirm_password_field,
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    self.message_text,
                ],
                spacing=5,
                tight=True),
                width=350,
                padding=ft.padding.all(10),
            ),
            actions=[
                cancel_button,
                save_button,
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            shape=ft.RoundedRectangleBorder(radius=12),
            bgcolor="#1B1B21",
            elevation=8,
        )

    def _validate_passwords(self) -> tuple[bool, str]:
        """Valida os campos de senha e retorna (é_válido, mensagem_erro)"""
        current_password = self.current_password_field.value
        new_password = self.new_password_field.value
        confirm_password = self.confirm_password_field.value

        # Verificar se todos os campos estão preenchidos
        if not current_password:
            return False, "Por favor, digite sua senha atual"

        if not new_password:
            return False, "Por favor, digite a nova senha"

        if not confirm_password:
            return False, "Por favor, confirme a nova senha"

        # Verificar tamanho mínimo da nova senha
        if len(new_password) < 8:
            return False, "A nova senha deve ter pelo menos 8 caracteres"

        # Verificar se as novas senhas coincidem
        if new_password != confirm_password:
            return False, "As senhas não coincidem"

        # Verificar se a nova senha é diferente da atual
        if current_password == new_password:
            return False, "A nova senha deve ser diferente da atual"

        return True, ""

    def _show_message(self, message: str, is_error: bool = True):
        """Exibe uma mensagem no dialog"""
        self.message_text.value = message
        self.message_text.color = ft.Colors.RED_400 if is_error else ft.Colors.GREEN_400
        self.message_text.visible = True
        self.page.update()

    def _clear_fields(self):
        """Limpa todos os campos do formulário"""
        self.current_password_field.value = ""
        self.new_password_field.value = ""
        self.confirm_password_field.value = ""
        self.message_text.visible = False
        self.page.update()

    def _save_password(self, e):
        """Processa a alteração da senha"""
        is_valid, error_message = self._validate_passwords()

        if not is_valid:
            self._show_message(error_message, is_error=True)
            return

        # Aqui você implementaria a lógica real de alteração de senha
        # Por exemplo: verificar senha atual no banco de dados, criptografar nova senha, etc.

        try:
            current_password = self.current_password_field.value if self.current_password_field.value else ""
            if not self._verify_current_password(current_password):
                self._show_message("Senha atual incorreta", is_error=True)
                return

            new_password = self.new_password_field.value if self.new_password_field.value else ""
            result = self._save_new_password(new_password)

            if result['status'] == 'success':
                self._show_message("Senha alterada com sucesso!", is_error=False)
                # Fechar o dialog após 1.5 segundos
                self.page.run_task(self._close_after_success)
            else:
                self._show_message("Erro ao salvar nova senha", is_error=True)

        except Exception as ex:
            self._show_message(f"Erro inesperado: {str(ex)}", is_error=True)

    async def _close_after_success(self):
        """Fecha o dialog após sucesso"""
        import asyncio
        await asyncio.sleep(1.5)
        self._cancel_dialog(None)

    def _verify_current_password(self, password: str) -> bool:
        """
        Método placeholder para verificar a senha atual
        """
        current_password = self.user.password
        return password == current_password.decrypted

    def _save_new_password(self, new_password: str) -> dict[str, Any]:
        """
        Método placeholder para salvar a nova senha
        Implemente aqui a lógica real de salvamento (hash, banco de dados, etc.)
        """
        # Simulação - implemente a lógica real aqui
        user_id = self.user.id if self.user.id else ""
        response = user_controllers.handle_update_user_password(user_id=user_id, new_password=new_password)
        return response

    def _cancel_dialog(self, e):
        """Cancela e fecha o dialog"""
        self._clear_fields()
        if isinstance(self.dialog, ft.AlertDialog):
            self.page.close(self.dialog)
        self.page.update()

    def show(self):
        """Exibe o dialog de alteração de senha"""
        self._clear_fields()
        if isinstance(self.dialog, ft.AlertDialog):
            self.page.open(self.dialog)
        self.page.update()
        # Foco no primeiro campo
        self.current_password_field.focus()
