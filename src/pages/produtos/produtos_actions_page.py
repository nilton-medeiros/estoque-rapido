import logging
import flet as ft
import asyncio

from src.domains.produtos.models import Produto, ProdutoStatus
from src.shared import MessageType, message_snackbar

import src.domains.produtos.controllers.produtos_controllers as pro_controllers


logger = logging.getLogger(__name__)

# ToDo: Refatorar este módulo: Não permitir enviar para lixeira produtos vinculados a pedidos, movimento de estoque, etc, retornar False e msg_error

async def send_to_trash(page: ft.Page, produto: Produto) -> bool:
    operation_complete_future = asyncio.Future()
    # Definir dlg_modal ANTES de usá-lo em send_to_trash_product_async
    # Renomear 'e' para evitar conflito com o 'e' de handle_action_click

    status=ProdutoStatus.DELETED

    def send_to_trash_product_async(e_trash):
        # nonlocal status
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

            # OPERAÇÃO SOFT DELETE: Muda o status para excluído o produto pelo ID
            # ToDo: Verificar se há pedidos ou estoque para este produto_id, se houver, alterar para INACTIVE
            """
            Aviso: Se houver pedidos vinculados, o status será definido como ProdutoStatus.INACTIVE. (Obsoleto)
            Caso contrário, o registro poderá ter o status ProdutoStatus.DELETED.
            Esta aplicação não exclui efetivamente o registro, apenas altera seu status.
            A exclusão definitiva ocorrerá após 90 dias da mudança para ProdutoStatus.DELETED, realizada periodicamente por uma Cloud Function.
            if is_linked:
                status = ProdutoStatus.INACTIVE
            """

            logger.info(
                f"Iniciando operação 'DELETED' para produto ID: {produto.id}")
            # Implemente aqui a lógica para buscar produtos, pedidos e estoque vinculados.
            # ...
            # Se não há pedido, produtos ou estoque vinculado a esta produto, mudar o status para DELETED
            # Caso contrário, muda o status para INACTIVE
            user = page_ctx.app_state.usuario
            result = pro_controllers.handle_update_status(produto=produto, usuario=user, status=ProdutoStatus.DELETED)

            dlg_modal.open = False  # Fechar diálogo antes de um possível snackbar
            page_ctx.update()

            if result["status"] == "error":
                message_snackbar(
                    message=result['message'], message_type=MessageType.WARNING, page=page_ctx)
                if not operation_complete_future.done():
                    operation_complete_future.set_result(False)
                return

            logger.info(
                f"Operação '{status.name}' para produto ID: {produto.id} concluída com sucesso.")
            if not operation_complete_future.done():
                operation_complete_future.set_result(True)

        except IndexError as ie:  # Deveria ser menos provável com referência direta
            # type: ignore
            logger.error(
                f"IndexError em send_to_trash_product_async: {ie}.\
                Controls: {dlg_modal.content.controls if dlg_modal else 'dlg_modal não definido'}")  # type: ignore
            # Ainda assim, fechar o diálogo em caso de erro interno
            if dlg_modal:
                dlg_modal.open = False
            page_ctx.update()
            if not operation_complete_future.done():
                operation_complete_future.set_result(False)
        except Exception as ex:
            logger.error(
                f"Erro durante a operação '{status.name}' ao enviar para lixeira: {ex}")
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

    text = (
        "Aviso: Este registro será excluído permanentemente após 90 dias. "
        "Caso exista pedidos vinculados a esta produto, "
        "ficará com o status 'Descontinuado' (INATIVO/OBSOLETO) e não poderá ser excluída definitivamente."
    )

    warning_text = ft.Text(
        value=text,
        theme_style=ft.TextThemeStyle.BODY_MEDIUM,
        selectable=True,
        expand=True,
    )

    action_title = "Mover para lixeira?"
    status_processing_text = ft.Text(
        "Processando sua solicitação. Aguarde...", visible=False)

    # Um AlertDialog Responsivo com limite de largura para 700 pixels
    dlg_modal = ft.AlertDialog(
        modal=True,
        title=ft.Text(action_title),
        content=ft.Column(
            [
                ft.Text(produto.name,
                        weight=ft.FontWeight.BOLD, selectable=True),
                ft.Text(f"ID: {produto.id}", selectable=True),
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
                              on_click=send_to_trash_product_async),
            ft.OutlinedButton("Não", icon=ft.Icons.CLOSE, on_click=close_dlg),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
        on_dismiss=lambda e_dismiss: (
            logger.info(
                f"Modal dialog para produto {produto.id} ({status.name}) foi descartado."),
            # Garante que a future seja resolvida se descartado
            close_dlg(e_dismiss)
        )
    )
    # Adiciona ao overlay e abre
    # Usar e.control.page garante pegar a página do contexto do clique original
    page.overlay.append(dlg_modal)
    dlg_modal.open = True
    page.update()
    return await operation_complete_future


def restore_from_trash(page: ft.Page, produto: Produto) -> bool:
    logger.info(f"Restaurando produto ID: {produto.id} da lixeira")
    user = page.app_state.usuario # type: ignore  [attr-defined]
    result = pro_controllers.handle_update_status(produto=produto, usuario=user, status=ProdutoStatus.ACTIVE)

    if result["status"] == "error":
        message_snackbar(
            page=page, message=result["message"], message_type=MessageType.ERROR)
        return False
    message_snackbar(page=page, message="Produto restaurado com sucesso!")
    return True
