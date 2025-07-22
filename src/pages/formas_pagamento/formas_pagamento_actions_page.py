import logging
import flet as ft
import asyncio

from src.domains.formas_pagamento.models import FormaPagamento
from src.domains.shared.context.session import get_current_user
from src.shared.utils import MessageType, message_snackbar

logger = logging.getLogger(__name__)


async def send_to_trash(page: ft.Page, forma_pagamento: FormaPagamento) -> bool:
    operation_complete_future = asyncio.Future()

    def send_to_trash_async(e_trash):
        # Obter a página a partir do evento é mais seguro em callbacks
        page_ctx = e_trash.page

        # --- Acesso ao controle de texto ---
        try:
            # dlg_modal é acessível aqui devido ao closure
            status_processing_text.visible = True  # Usar referência direta

            # Opcional: Desabilitar botões enquanto processa
            for btn in dlg_modal.actions:
                btn.disabled = True

            # Atualizar a página (ou o diálogo) para mostrar a mudança
            page_ctx.update()

            # OPERAÇÃO SOFT DELETE: Muda o status para excluído o forma_pagamento pelo ID
            """
            Esta aplicação não exclui efetivamente o registro, apenas altera seu status.
            A exclusão definitiva ocorrerá após 90 dias da mudança para status = 'DELETED', realizada periodicamente por uma Cloud Function.
            """

            logger.info(
                f"Iniciando operação 'SOFT_DELETED' para forma_pagamento ID: {forma_pagamento.id}")
            current_user = get_current_user(page_ctx)
            result = handle_delete_pedido(forma_pagamento=forma_pagamento, current_user=current_user)

            page.close(dlg_modal)  # Fechar diálogo antes de um possível snackbar

            if result["status"] == "error":
                message_snackbar(page=page_ctx,
                    message=result['message'], message_type=MessageType.WARNING)
                if not operation_complete_future.done():
                    operation_complete_future.set_result(False)
                return

            message_snackbar(page=page_ctx, message=result['message'], message_type=MessageType.SUCCESS)

            logger.info(
                f"Operação 'SOFT_DELETED' para forma_pagamento ID: {forma_pagamento.id} concluída com sucesso.")
            if not operation_complete_future.done():
                operation_complete_future.set_result(True)

        except IndexError as ie:  # Deveria ser menos provável com referência direta
            logger.error(
                f"IndexError em send_to_trash_async: {ie}.\
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
        value="Aviso: Este forma_pagamento será excluído permanentemente após 90 dias.",
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
                ft.Text(f"FormaPagamento: #{forma_pagamento.order_number}",
                        weight=ft.FontWeight.BOLD, selectable=True),
                ft.Text(f"ID: {forma_pagamento.id}", selectable=True),
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
                              on_click=send_to_trash_async),
            ft.OutlinedButton("Não", icon=ft.Icons.CLOSE, on_click=close_dlg),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
        on_dismiss=lambda e_dismiss: (
            logger.info(
                f"Modal dialog para forma_pagamento {forma_pagamento.id} (SOFT_DELETED) foi descartado."),
            # Garante que a future seja resolvida se descartado
            close_dlg(e_dismiss)
        )
    )
    # Adiciona ao overlay e abre
    page.open(dlg_modal)
    # page.update()
    return await operation_complete_future


def restore_from_trash(page: ft.Page, forma_pagamento: FormaPagamento) -> bool:
    logger.info(f"Restaurando forma_pagamento ID: {forma_pagamento.id} da lixeira")

    result = order_controllers.handle_restore_pedido_from_trash(forma_pagamento, get_current_user(page))

    if result["status"] == "error":
        message_snackbar(
            page=page, message=result["message"], message_type=MessageType.ERROR)
        return False
    message_snackbar(page=page, message="FormaPagamento restaurado com sucesso!")
    return True
