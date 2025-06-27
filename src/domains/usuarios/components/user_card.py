# ==========================================
# src/domains/usuarios/components/user_card.py
# ==========================================
import flet as ft
from src.domains.shared import RegistrationStatus
from src.domains.usuarios.models.usuarios_model import Usuario

class UserCard:
    """Componente reutilizável para card de usuario"""

    @staticmethod
    def create(usuario: Usuario, logged_user_id: str, on_action_callback) -> ft.Card:
        """Cria um card individual do usuario"""
        return ft.Card(
            content=ft.Container(
                padding=15,
                content=ft.Column([
                    UserCard._create_card_header(usuario, logged_user_id, on_action_callback),
                    ft.Text(usuario.email,
                           theme_style=ft.TextThemeStyle.BODY_MEDIUM,
                           no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Row(
                        controls=[
                            ft.Text(usuario.profile.value, theme_style=ft.TextThemeStyle.BODY_SMALL),
                            ft.Text(f"{usuario.phone_number}", theme_style=ft.TextThemeStyle.BODY_SMALL),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    UserCard._create_status_row(usuario),
                ])
            ),
            margin=ft.margin.all(5),
            col={"xs": 12, "sm": 6, "md": 4, "lg": 3}
        )

    @staticmethod
    def _create_card_header(usuario: Usuario, logged_user_id: str, on_action_callback) -> ft.Row:
        """Cria o cabeçalho do card com imagem e menu"""
        return ft.Row(
            [
                UserCard._create_user_image(usuario),
                ft.Text(
                    usuario.name.primeiro_e_ultimo_nome,
                    weight=ft.FontWeight.BOLD,
                    theme_style=ft.TextThemeStyle.BODY_LARGE,
                    no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS,
                    # expand=True,
                ),
                ft.Container(expand=True),  # Spacer
                UserCard._create_action_menu(usuario, logged_user_id, on_action_callback),
            ],
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.START
        )

    @staticmethod
    def _create_user_image(usuario: Usuario) -> ft.Container:
        """Cria o container da imagem do usuário"""
        image_content = (
            ft.Image(
                src=usuario.photo_url,
                fit=ft.ImageFit.COVER,
                width=100, height=100,
                border_radius=ft.border_radius.all(10),
                error_content=ft.Icon(ft.Icons.IMAGE_NOT_SUPPORTED_OUTLINED,
                                    size=30, color=ft.Colors.ERROR)
            ) if usuario.photo_url
            else ft.Icon(ft.Icons.CATEGORY_OUTLINED, size=40, opacity=0.5)
        )

        return ft.Container(
            width=100, height=100,
            border_radius=ft.border_radius.all(10),
            border=ft.border.all(1, ft.Colors.OUTLINE) if not usuario.photo_url else None,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            alignment=ft.alignment.center,
            content=image_content
        )

    @staticmethod
    def _create_action_menu(usuario: Usuario, logged_user_id: str, on_action_callback) -> ft.Container:
        """Cria o menu de ações do usuario"""
        return ft.Container(
            content=ft.PopupMenuButton(
                icon=ft.Icons.MORE_VERT,
                tooltip="Mais Ações",
                items=[
                    ft.PopupMenuItem(
                        text="Editar usuário",
                        icon=ft.Icons.EDIT_NOTE_OUTLINED,
                        on_click=lambda e: on_action_callback("EDIT", usuario)
                    ),
                    ft.PopupMenuItem(
                        text="Trocar senha",
                        icon=ft.Icons.PASSWORD,
                        on_click=lambda e: on_action_callback("CHANGE_PASSWORD", usuario),
                        disabled=logged_user_id != usuario.id
                    ),
                    ft.PopupMenuItem(
                        text="Excluir usuário",
                        icon=ft.Icons.DELETE_OUTLINE,
                        on_click=lambda e: on_action_callback("SOFT_DELETE", usuario)
                    ),
                ],
            ),
        )

    @staticmethod
    def _create_status_row(usuario: Usuario) -> ft.Row:
        """Cria a linha com status e informações de status"""
        return ft.Row([
            ft.Text(
                value=usuario.status.value,
                theme_style=ft.TextThemeStyle.BODY_SMALL,
                color=ft.Colors.GREEN if usuario.status == RegistrationStatus.ACTIVE else ft.Colors.RED,
            ),
            # ft.Text(..adicionar outros campos de status se houver)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
