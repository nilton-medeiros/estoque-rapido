import logging
import flet as ft
import asyncio

from src.domains.pedidos.models import Pedido
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
            user = page_ctx.app_state.usuario
            result = order_controllers.handle_delete_pedido(pedido=pedido, usuario_logado=user)

            dlg_modal.open = False  # Fechar diálogo antes de um possível snackbar
            page_ctx.update()

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
                dlg_modal.open = False
            page_ctx.update()
            if not operation_complete_future.done():
                operation_complete_future.set_result(False)
        except Exception as ex:
            logger.error(
                f"Erro durante a operação 'SOFT_DELETED' ao enviar para lixeira: {ex}")
            if dlg_modal:
                dlg_modal.open = False
            page_ctx.update()
            message_snackbar(
                message=f"Erro ao enviar para lixeira: {ex}", message_type=MessageType.ERROR, page=page_ctx)
            if not operation_complete_future.done():
                operation_complete_future.set_result(False)

    def close_dlg(e_close):
        dlg_modal.open = False
        e_close.page.update()
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
    page.overlay.append(dlg_modal)
    dlg_modal.open = True
    page.update()
    return await operation_complete_future


def restore_from_trash(page: ft.Page, pedido: Pedido) -> bool:
    logger.info(f"Restaurando pedido ID: {pedido.id} da lixeira")
    user = page.app_state.usuario # type: ignore  [attr-defined]

    result = order_controllers.handle_restore_pedido_from_trash(pedido, user)

    if result["status"] == "error":
        message_snackbar(
            page=page, message=result["message"], message_type=MessageType.ERROR)
        return False
    message_snackbar(page=page, message="Pedido restaurado com sucesso!")
    return True
