# ==========================================
# src/domains/clientes/components/client_card.py
# ==========================================
import flet as ft
from src.domains.shared import RegistrationStatus
from src.domains.clientes.models.clientes_model import Cliente

class ClientCard:
    """Componente reutilizável para card de cliente"""

    @staticmethod
    def create(cliente: Cliente, on_action_callback) -> ft.Card:
        """Cria um card individual do cliente"""
        return ft.Card(
            content=ft.Container(
                padding=15,
                content=ft.Column([
                    ClientCard._create_card_header(cliente, on_action_callback),
                    ft.Text(cliente.email,
                           theme_style=ft.TextThemeStyle.BODY_MEDIUM,
                           no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Row(
                        controls=[
                            ft.Text(f"Aniversário: {cliente.get_birthday()}", theme_style=ft.TextThemeStyle.BODY_SMALL),
                            ft.Text(f"{cliente.phone}", theme_style=ft.TextThemeStyle.BODY_SMALL),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ClientCard._create_status_row(cliente),
                ])
            ),
            margin=ft.margin.all(5),
            col={"xs": 12, "sm": 6, "md": 4, "lg": 3}
        )

    @staticmethod
    def _create_card_header(cliente: Cliente, on_action_callback) -> ft.Row:
        """Cria o cabeçalho do card com imagem e menu"""
        return ft.Row(
            [
                ft.Text(
                    cliente.name.primeiro_e_ultimo_nome,
                    weight=ft.FontWeight.BOLD,
                    theme_style=ft.TextThemeStyle.BODY_LARGE,
                    no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS,
                    # expand=True,
                ),
                ft.Container(expand=True),  # Spacer
                ClientCard._create_action_menu(cliente, on_action_callback),
            ],
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.START
        )

    @staticmethod
    def _create_action_menu(cliente: Cliente, on_action_callback) -> ft.Container:
        """Cria o menu de ações do cliente"""
        return ft.Container(
            content=ft.PopupMenuButton(
                icon=ft.Icons.MORE_VERT,
                tooltip="Mais Ações",
                items=[
                    ft.PopupMenuItem(
                        text="Editar cliente",
                        icon=ft.Icons.EDIT_NOTE_OUTLINED,
                        on_click=lambda e: on_action_callback("EDIT", cliente)
                    ),
                    ft.PopupMenuItem(
                        text="Excluir cliente",
                        icon=ft.Icons.DELETE_OUTLINE,
                        on_click=lambda e: on_action_callback("SOFT_DELETE", cliente)
                    ),
                ],
            ),
        )

    @staticmethod
    def _create_status_row(cliente: Cliente) -> ft.Row:
        """Cria a linha com status e informações de status"""
        return ft.Row([
            ft.Text(
                value=cliente.status.default_label,
                theme_style=ft.TextThemeStyle.BODY_SMALL,
                color=ft.Colors.GREEN if cliente.status == RegistrationStatus.ACTIVE else ft.Colors.RED,
            ),
            # ft.Text(..adicionar outros campos de status se houver)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
