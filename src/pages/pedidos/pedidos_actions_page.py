import logging
import flet as ft
import asyncio

from src.domains.pedidos.models import Pedido
from src.domains.pedidos.models.pedidos_model import PedidoItem
from src.domains.shared.context.session import get_current_user
from src.shared.utils import MessageType, message_snackbar

from src.domains.pedidos.controllers import pedidos_controllers as order_controllers


logger = logging.getLogger(__name__)


async def send_to_trash(page: ft.Page, pedido: Pedido) -> bool:
    operation_complete_future = asyncio.Future()

    def send_to_trash_client_async(e_trash):
        # Obter a página a partir do evento é mais seguro em callbacks
        page_ctx = e_trash.page

        # --- Acesso ao controle de texto ---
        try:
            # dlg_modal é acessível aqui devido ao closure
            # status_text_control = dlg_modal.content.controls[3] # Originalmente [2], que era um erro
            # status_text_control.visible = True
            status_processing_text.visible = True  # Usar referência direta

            # Opcional: Desabilitar botões enquanto processa
            for btn in dlg_modal.actions:
                btn.disabled = True

            # Atualizar a página (ou o diálogo) para mostrar a mudança
            page_ctx.update()

            # OPERAÇÃO SOFT DELETE: Muda o status para excluído o pedido pelo ID
            """
            Esta aplicação não exclui efetivamente o registro, apenas altera seu status.
            A exclusão definitiva ocorrerá após 90 dias da mudança para status = 'DELETED', realizada periodicamente por uma Cloud Function.
            """

            logger.info(
                f"Iniciando operação 'SOFT_DELETED' para o pedido ID: {pedido.id}")
            current_user = get_current_user(page_ctx)
            result = order_controllers.handle_delete_pedido(pedido=pedido, current_user=current_user)

            page.close(dlg_modal)  # Fechar diálogo antes de um possível snackbar

            if result["status"] == "error":
                message_snackbar(page=page_ctx,
                    message=result['message'], message_type=MessageType.WARNING)
                if not operation_complete_future.done():
                    operation_complete_future.set_result(False)
                return

            message_snackbar(page=page_ctx, message=result['message'], message_type=MessageType.SUCCESS)

            logger.info(
                f"Operação 'SOFT_DELETED' para pedido ID: {pedido.id} concluída com sucesso.")
            if not operation_complete_future.done():
                operation_complete_future.set_result(True)

        except IndexError as ie:  # Deveria ser menos provável com referência direta
            logger.error(
                f"IndexError em send_to_trash_client_async: {ie}.\
                Controls: {dlg_modal.content.controls if dlg_modal else 'dlg_modal não definido'}")  # type: ignore [attr-defined]
            # Ainda assim, fechar o diálogo em caso de erro interno
            if dlg_modal:
                page.close(dlg_modal)
            page_ctx.update()
            if not operation_complete_future.done():
                operation_complete_future.set_result(False)
        except Exception as ex:
            logger.error(
                f"Erro durante a operação 'SOFT_DELETED' ao enviar para lixeira: {ex}")
            if dlg_modal:
                page.close(dlg_modal)
            page_ctx.update()
            message_snackbar(
                message=f"Erro ao enviar para lixeira: {ex}", message_type=MessageType.ERROR, page=page_ctx)
            if not operation_complete_future.done():
                operation_complete_future.set_result(False)

    def close_dlg(e_close):
        page.close(dlg_modal)
        if not operation_complete_future.done():
            operation_complete_future.set_result(False)  # Usuário cancelou

    warning_text = ft.Text(
        value="Aviso: Este pedido será excluído permanentemente após 90 dias.",
        theme_style=ft.TextThemeStyle.BODY_MEDIUM,
        selectable=True,
        expand=True,
    )

    status_processing_text = ft.Text(
        "Processando sua solicitação. Aguarde...", visible=False)

    # Um AlertDialog Responsivo com limite de largura para 700 pixels
    dlg_modal = ft.AlertDialog(
        modal=True,
        title=ft.Text("Mover para lixeira?"),
        content=ft.Column(
            [
                ft.Text(f"Pedido: #{pedido.order_number}",
                        weight=ft.FontWeight.BOLD, selectable=True),
                ft.Text(f"ID: {pedido.id}", selectable=True),
                ft.Row([ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED), warning_text]),
                status_processing_text,  # Controle referenciado
            ],
            # tight = True: É bom definir tight=True se você fixa a altura com o conteúdo
            # tight = False: Estica a altura até o limite da altura da página
            tight=True,
            width=700,
            spacing=10,
        ),
        actions=[
            # Passa a função delete_company como callback
            ft.ElevatedButton("Sim", icon=ft.Icons.CHECK_CIRCLE_OUTLINE,
                              on_click=send_to_trash_client_async),
            ft.OutlinedButton("Não", icon=ft.Icons.CLOSE, on_click=close_dlg),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
        on_dismiss=lambda e_dismiss: (
            logger.info(
                f"Modal dialog para pedido {pedido.id} (SOFT_DELETED) foi descartado."),
            # Garante que a future seja resolvida se descartado
            close_dlg(e_dismiss)
        )
    )
    # Adiciona ao overlay e abre
    page.open(dlg_modal)
    # page.update()
    return await operation_complete_future


def restore_from_trash(page: ft.Page, pedido: Pedido) -> bool:
    logger.info(f"Restaurando pedido ID: {pedido.id} da lixeira")

    result = order_controllers.handle_restore_pedido_from_trash(pedido, get_current_user(page))

    if result["status"] == "error":
        message_snackbar(
            page=page, message=result["message"], message_type=MessageType.ERROR)
        return False
    message_snackbar(page=page, message="Pedido restaurado com sucesso!")
    return True

def show_orders_items_grid(page: ft.Page, items: list[PedidoItem]):
    """
    Exibe a lista de itens de um pedido em uma interface responsiva com DataTable.

    Args:
        page: Instância da página Flet
        items: Lista de itens do pedido (PedidoItem)
    """

    def close_dialog(e):
        """Fecha o diálogo de itens do pedido"""
        page.close(items_dialog)

    def create_data_table():
        """Cria o DataTable com os itens do pedido"""

        # Cabeçalhos das colunas
        columns = [
            ft.DataColumn(
                label=ft.Text("Produto", weight=ft.FontWeight.BOLD, size=14)
            ),
            ft.DataColumn(
                label=ft.Text("Qtd", weight=ft.FontWeight.BOLD, size=14),
                numeric=True
            ),
            ft.DataColumn(
                label=ft.Text("Unidade", weight=ft.FontWeight.BOLD, size=14)
            ),
            ft.DataColumn(
                label=ft.Text("Valor Unit.", weight=ft.FontWeight.BOLD, size=14),
                numeric=True
            ),
            ft.DataColumn(
                label=ft.Text("Total", weight=ft.FontWeight.BOLD, size=14),
                numeric=True
            ),
        ]

        # Linhas de dados
        rows = []
        for item in items:
            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(
                            ft.Container(
                                content=ft.Text(
                                    item.description,
                                    size=13,
                                    selectable=True,
                                    max_lines=2,
                                    overflow=ft.TextOverflow.ELLIPSIS
                                ),
                                padding=ft.padding.symmetric(vertical=8),
                                width=200  # Largura fixa para consistência
                            )
                        ),
                        ft.DataCell(
                            ft.Text(
                                str(item.quantity),
                                size=13,
                                text_align=ft.TextAlign.CENTER,
                                weight=ft.FontWeight.W_500
                            )
                        ),
                        ft.DataCell(
                            ft.Text(
                                item.unit_of_measure,
                                size=13,
                                text_align=ft.TextAlign.CENTER
                            )
                        ),
                        ft.DataCell(
                            ft.Text(
                                str(item.unit_price),
                                size=13,
                                text_align=ft.TextAlign.RIGHT,
                                color=ft.colors.GREEN_700
                            )
                        ),
                        ft.DataCell(
                            ft.Text(
                                str(item.total),
                                size=13,
                                text_align=ft.TextAlign.RIGHT,
                                weight=ft.FontWeight.BOLD,
                                color=ft.colors.GREEN_800
                            )
                        ),
                    ],
                    selected=False,
                )
            )

        return ft.DataTable(
            columns=columns,
            rows=rows,
            border=ft.border.all(1, ft.colors.OUTLINE),
            border_radius=10,
            vertical_lines=ft.border.BorderSide(1, ft.colors.OUTLINE_VARIANT),
            horizontal_lines=ft.border.BorderSide(1, ft.colors.OUTLINE_VARIANT),
            heading_row_color=ft.colors.SURFACE_VARIANT,
            heading_row_height=50,
            data_row_min_height=60,
            data_row_max_height=80,
            column_spacing=20,
        )

    def create_summary_card():
        """Cria um card com resumo dos totais"""
        total_items = len(items)
        total_quantity = sum(item.quantity for item in items)

        # Calcula o total geral (assumindo que o primeiro item tem a moeda correta)
        if items:
            zero_money = items[0].total.__class__.mint("0.00", currency_symbol=items[0].total.currency_symbol)
            total_amount = sum((item.total for item in items), zero_money)
        else:
            total_amount = "R$ 0,00"

        return ft.Card(
            content=ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Column(
                            controls=[
                                ft.Text(
                                    "Total de Itens",
                                    size=12,
                                    color=ft.colors.ON_SURFACE_VARIANT,
                                    weight=ft.FontWeight.W_500
                                ),
                                ft.Text(
                                    str(total_items),
                                    size=20,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.colors.PRIMARY
                                ),
                            ],
                            spacing=2,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            expand=True
                        ),
                        ft.VerticalDivider(width=1),
                        ft.Column(
                            controls=[
                                ft.Text(
                                    "Quantidade Total",
                                    size=12,
                                    color=ft.colors.ON_SURFACE_VARIANT,
                                    weight=ft.FontWeight.W_500
                                ),
                                ft.Text(
                                    str(total_quantity),
                                    size=20,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.colors.SECONDARY
                                ),
                            ],
                            spacing=2,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            expand=True
                        ),
                        ft.VerticalDivider(width=1),
                        ft.Column(
                            controls=[
                                ft.Text(
                                    "Valor Total",
                                    size=12,
                                    color=ft.colors.ON_SURFACE_VARIANT,
                                    weight=ft.FontWeight.W_500
                                ),
                                ft.Text(
                                    str(total_amount),
                                    size=20,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.colors.GREEN_700
                                ),
                            ],
                            spacing=2,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            expand=True
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_AROUND,
                ),
                padding=ft.padding.all(20),
            ),
            elevation=2,
        )

    def create_empty_state():
        """Cria o estado vazio quando não há itens"""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(
                        ft.icons.INVENTORY_2_OUTLINED,
                        size=64,
                        color=ft.colors.ON_SURFACE_VARIANT
                    ),
                    ft.Text(
                        "Nenhum item encontrado",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        color=ft.colors.ON_SURFACE_VARIANT
                    ),
                    ft.Text(
                        "Este pedido não possui itens cadastrados.",
                        size=14,
                        color=ft.colors.ON_SURFACE_VARIANT,
                        text_align=ft.TextAlign.CENTER
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10
            ),
            alignment=ft.alignment.center,
            padding=ft.padding.all(40)
        )

    # Constrói o conteúdo baseado na existência de itens
    if not items:
        content_controls = [create_empty_state()]
    else:
        content_controls = [
            create_summary_card(),
            ft.Divider(height=1, color=ft.colors.OUTLINE_VARIANT),
            ft.Container(
                content=create_data_table(),
                padding=ft.padding.all(10)
            )
        ]

    # Container principal com scroll
    content_container = ft.Container(
        content=ft.Column(
            controls=content_controls,
            spacing=20,
            scroll=ft.ScrollMode.AUTO,
            expand=True
        ),
        width=900,  # Largura fixa para o diálogo
        height=600,  # Altura fixa para o diálogo
        padding=ft.padding.all(20)
    )

    # Cria o diálogo modal
    items_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Row(
            controls=[
                ft.Icon(ft.icons.LIST_ALT, color=ft.colors.PRIMARY),
                ft.Text(
                    "Itens do Pedido",
                    size=20,
                    weight=ft.FontWeight.BOLD
                )
            ],
            spacing=10
        ),
        content=content_container,
        actions=[
            ft.TextButton(
                "Fechar",
                icon=ft.icons.CLOSE,
                on_click=close_dialog,
                style=ft.ButtonStyle(
                    color=ft.colors.PRIMARY,
                )
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
        on_dismiss=lambda e: logger.info("Diálogo de itens do pedido foi fechado")
    )

    # Abre o diálogo
    page.open(items_dialog)

    logger.info(f"Exibindo {len(items)} itens do pedido")
