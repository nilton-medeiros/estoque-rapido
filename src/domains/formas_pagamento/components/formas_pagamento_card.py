import flet as ft
from src.domains.formas_pagamento.models.formas_pagamento_model import FormaPagamento, TipoPercentual
from src.domains.shared import RegistrationStatus

class FormasPagamentoCard:
    """Componente reutilizável para card de formas_pagamento"""

    @staticmethod
    def create(formas_pagamento: FormaPagamento, on_action_callback) -> ft.Card:
        """Cria um card individual do formas_pagamento"""
        return ft.Card(
            content=ft.Container(
                padding=15,
                content=ft.Column([
                    FormasPagamentoCard._create_card_header(formas_pagamento, on_action_callback),
                    ft.Text(f"Tipo: {formas_pagamento.payment_type.name}",
                           theme_style=ft.TextThemeStyle.BODY_SMALL,
                           no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Row(
                        [
                            ft.Text(f"Percentual: {formas_pagamento.percentage}%",
                                theme_style=ft.TextThemeStyle.BODY_SMALL),
                            ft.Text(f"{formas_pagamento.percentage_type.value}",
                                theme_style=ft.TextThemeStyle.BODY_SMALL,
                                color=ft.Colors.BLUE_900 if formas_pagamento.percentage_type == TipoPercentual.ACRESCIMO else ft.Colors.AMBER_900),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    FormasPagamentoCard._create_status_row(formas_pagamento),
                ])
            ),
            margin=ft.margin.all(5),
            # width=600,  # Este width é ignorado por causa da responsividade em col abaixo:
            col={"xs": 12, "sm": 12, "md": 6, "lg": 6, "xl": 4, "xxl": 3}
        )

    @staticmethod
    def _create_card_header(formas_pagamento: FormaPagamento, on_action_callback) -> ft.Row:
        """Cria o cabeçalho do card com imagem e menu"""
        return ft.Row(
            [
                ft.Text(formas_pagamento.name, weight=ft.FontWeight.BOLD,
                    theme_style=ft.TextThemeStyle.BODY_LARGE,
                    no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS),
                ft.Container(expand=True),  # Spacer
                FormasPagamentoCard._create_action_menu(formas_pagamento, on_action_callback),
            ],
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )

    @staticmethod
    def _create_action_menu(formas_pagamento: FormaPagamento, on_action_callback) -> ft.Container:
        """Cria o menu de ações do formas_pagamento"""
        return ft.Container(
            content=ft.PopupMenuButton(
                icon=ft.Icons.MORE_VERT,
                tooltip="Mais Ações",
                items=[
                    ft.PopupMenuItem(
                        text="Editar formas de pagamento",
                        icon=ft.Icons.EDIT_NOTE_OUTLINED,
                        on_click=lambda e: on_action_callback("EDIT", formas_pagamento)
                    ),
                    ft.PopupMenuItem(
                        text="Excluir formas de pagamento",
                        icon=ft.Icons.DELETE_OUTLINE,
                        on_click=lambda e: on_action_callback("SOFT_DELETE", formas_pagamento)
                    ),
                ],
            ),
        )

    @staticmethod
    def _create_status_row(formas_pagamento: FormaPagamento) -> ft.Row:
        """Cria a linha com status e informações de estoque"""
        return ft.Row([
            ft.Text(
                value=formas_pagamento.status.produto_label,
                theme_style=ft.TextThemeStyle.BODY_SMALL,
                color=ft.Colors.GREEN if formas_pagamento.status == RegistrationStatus.ACTIVE else ft.Colors.RED,
            ),
            ft.Text(
                value=f"Ordem de apresentação: {formas_pagamento.order}",
                theme_style=ft.TextThemeStyle.BODY_SMALL,
            )
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
