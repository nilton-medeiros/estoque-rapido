import logging
import flet as ft
import asyncio

from src.domains.formas_pagamento.controllers import FormasPagamentoController
from src.domains.formas_pagamento.models import FormaPagamento
from src.domains.formas_pagamento.repositories.implementations import FirebaseFormasPagamentoRepository
from src.domains.formas_pagamento.services import FormasPagamentoService
from src.domains.shared.context.session import get_current_user
from src.shared.utils import MessageType, message_snackbar

logger = logging.getLogger(__name__)


async def send_to_trash(page: ft.Page, forma_pagamento: FormaPagamento) -> bool:
    operation_complete_future = asyncio.Future()

    def send_to_trash_async(e_trash):
        # Obter a página a partir do evento é mais seguro em callbacks
        page_ctx = e_trash.page

        status_processing_text.visible = True  # Usar referência direta

        # dlg_modal é acessível aqui devido ao closure
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
            f"Iniciando operação 'SOFT_DELETE' para forma_pagamento ID: {forma_pagamento.id}")

        repository = FirebaseFormasPagamentoRepository()
        services = FormasPagamentoService(repository)
        controllers = FormasPagamentoController(services)
        current_user = get_current_user(page_ctx)

        result = controllers.delete_forma_pagamento(
            forma_pagamento, current_user)

        # Fechar diálogo antes de um possível snackbar
        page.close(dlg_modal)

        if result["status"] == "error":
            message_snackbar(page=page_ctx, message=result["message"],
                                message_type=MessageType.WARNING, center=True)
            if not operation_complete_future.done():
                operation_complete_future.set_result(False)
            return

        message_snackbar(page=page_ctx, message=result["message"],
                            message_type=MessageType.SUCCESS, center=True)

        logger.info(
            f"Operação 'SOFT_DELETE' para forma_pagamento ID: {forma_pagamento.id} concluída com sucesso.")

        if not operation_complete_future.done():
            operation_complete_future.set_result(True)

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
                ft.Text(f"FormaPagamento: #{forma_pagamento.name}",
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
                f"Modal dialog para forma_pagamento {forma_pagamento.id} (SOFT_DELETE) foi descartado."),
            # Garante que a future seja resolvida se descartado
            close_dlg(e_dismiss)
        )
    )
    page.open(dlg_modal)
    return await operation_complete_future

def restore_from_trash(page: ft.Page, forma_pagamento: FormaPagamento) -> bool:
    logger.info(
        f"Restaurando forma_pagamento ID: {forma_pagamento.id} da lixeira")

    repository = FirebaseFormasPagamentoRepository()
    services = FormasPagamentoService(repository)
    controllers = FormasPagamentoController(services)
    current_user = get_current_user(page)

    result = controllers.restore_from_trash_forma_pagamento(
        forma_pagamento, current_user)

    if result["status"] == "error":
        message_snackbar(
            page=page, message=result["message"], message_type=MessageType.ERROR)
        return False
    message_snackbar(
        page=page, message="Forma de Pagamento restaurado com sucesso!")
    return True
