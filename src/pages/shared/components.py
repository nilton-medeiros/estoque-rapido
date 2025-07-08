from typing import Any, Callable, List

import flet as ft


def create_recycle_bin_card(
    entity: Any,
    top_content: ft.Control,
    title_text: str,
    subtitle_controls: List[ft.Control],
    status_icon: ft.Icon,
    date_text_control: ft.Text,
    tooltip_text: str,
    on_action_click: Callable,
    on_info_click: Callable,
    on_icon_hover: Callable,
    col_config: dict = {"xs": 12, "sm": 6, "md": 4, "lg": 3}
) -> ft.Card:
    """
    Cria um ft.Card genérico para itens na lixeira.

    Args:
        entity: O objeto da entidade (necessário para os callbacks).
        top_content: O controle a ser exibido na área superior esquerda (ex: imagem ou ícone).
        title_text: O texto principal do card.
        subtitle_controls: Uma lista de controles para exibir como detalhes.
        status_icon: O ícone que representa o status (ex: DELETED, ARCHIVED).
        date_text_control: O controle de texto para a data de exclusão/arquivamento.
        tooltip_text: O texto a ser exibido no tooltip do card.
        on_action_click: Callback para ações (Restaurar).
        on_info_click: Callback para o botão de informações.
        on_icon_hover: Callback para o evento de hover nos ícones.
        col_config: Configuração de responsividade para o ResponsiveRow.

    Returns:
        Um objeto ft.Card configurado.
    """
    return ft.Card(
        content=ft.Container(
            padding=15,
            content=ft.Column([
                ft.Row(
                    controls=[
                        top_content,
                        ft.Container(expand=True),
                        status_icon,
                        ft.Container(
                            content=ft.PopupMenuButton(
                                icon=ft.Icons.MORE_VERT, tooltip="Mais Ações",
                                items=[
                                    ft.PopupMenuItem(
                                        text="Restaurar",
                                        tooltip="Restaurar item da lixeira",
                                        icon=ft.Icons.RESTORE,
                                        data={'action': 'RESTORE', 'data': entity},
                                        on_click=on_action_click
                                    ),
                                    ft.PopupMenuItem(
                                        text="Informações",
                                        tooltip="Informações sobre o status",
                                        icon=ft.Icons.INFO_OUTLINED,
                                        data={'action': 'INFO', 'data': entity},
                                        on_click=on_info_click
                                    ),
                                ],
                            ),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.START,
                    vertical_alignment=ft.CrossAxisAlignment.START
                ),
                ft.Text(title_text, color=ft.Colors.WHITE70, weight=ft.FontWeight.BOLD),
                *subtitle_controls,
                ft.Row(
                    controls=[
                        date_text_control,
                        ft.Row(
                            controls=[
                                ft.Container(
                                    content=ft.Icon(name=ft.Icons.RESTORE_OUTLINED, color=ft.Colors.PRIMARY),
                                    tooltip="Restaurar",
                                    data={'action': 'RESTORE', 'data': entity},
                                    on_hover=on_icon_hover, on_click=on_action_click,
                                    border_radius=ft.border_radius.all(20), ink=True,
                                    bgcolor=ft.Colors.TRANSPARENT, alignment=ft.alignment.center,
                                    clip_behavior=ft.ClipBehavior.ANTI_ALIAS
                                ),
                                ft.Container(
                                    content=ft.Icon(name=ft.Icons.INFO_OUTLINED, color=ft.Colors.PRIMARY),
                                    tooltip="Informações sobre o status",
                                    data={'action': 'INFO', 'data': entity},
                                    on_hover=on_icon_hover, on_click=on_info_click,
                                    border_radius=ft.border_radius.all(20), ink=True,
                                    bgcolor=ft.Colors.TRANSPARENT, alignment=ft.alignment.center,
                                    clip_behavior=ft.ClipBehavior.ANTI_ALIAS
                                ),
                            ],
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
            ])
        ),
        margin=ft.margin.all(5),
        col=col_config,
        tooltip=tooltip_text,
        expand=True,
    )