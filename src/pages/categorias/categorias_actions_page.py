import logging
import flet as ft
import asyncio

from src.domains.categorias.models import ProdutoCategorias
from src.domains.shared import RegistrationStatus
from src.domains.shared.context.session import get_current_user
from src.shared.utils import MessageType, message_snackbar

import src.domains.categorias.controllers.categorias_controllers as category_controllers

logger = logging.getLogger(__name__)

# ToDo: Refatorar este módulo: Não permitir enviar para lixeira categorias vinculadas a produtos, retornar False e msg_error

async def send_to_trash(page: ft.Page, categoria: ProdutoCategorias) -> bool:
    operation_complete_future = asyncio.Future()
    # Definir dlg_modal ANTES de usá-lo em send_to_trash_category_async

    status=RegistrationStatus.DELETED

    def send_to_trash_category_async(e_trash):
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

            # OPERAÇÃO SOFT DELETE: Muda o status para excluído a categoria pelo ID
            # ToDo: Verificar se há produtos para esta categoria_id, se houver, alterar para INACTIVE
            """
            Aviso: Se houver produtos vinculados, o status será definido como RegistrationStatus.INACTIVE. (Obsoleto)
            Caso contrário, o registro poderá ter o status RegistrationStatus.DELETED.
            Esta aplicação não exclui efetivamente o registro, apenas altera seu status.
            A exclusão definitiva ocorrerá após 90 dias da mudança para RegistrationStatus.DELETED, realizada periodicamente por uma Cloud Function.
            if is_linked:
                status = RegistrationStatus.INACTIVE
            """

            logger.info(
                f"Iniciando operação 'DELETED' para categoria ID: {categoria.id}")
            # Implemente aqui a lógica para buscar produtos, pedidos e estoque vinculados.
            # ...
            # Se não há pedido, produtos ou estoque vinculado a esta categoria, mudar o status para DELETED
            # Caso contrário, muda o status para INACTIVE
            current_user = get_current_user(page_ctx)
            result = category_controllers.handle_update_status(categoria=categoria, current_user=current_user, status=RegistrationStatus.DELETED)

            page.close(dlg_modal)  # Fechar diálogo antes de um possível snackbar

            if result["status"] == "error":
                message_snackbar(page_ctx, result['message'], MessageType.WARNING)
                if not operation_complete_future.done():
                    operation_complete_future.set_result(False)
                return

            logger.info(
                f"Operação '{status.name}' para categoria ID: {categoria.id} concluída com sucesso.")
            if not operation_complete_future.done():
                operation_complete_future.set_result(True)

        except IndexError as ie:  # Deveria ser menos provável com referência direta
            # type: ignore
            logger.error(
                f"IndexError em send_to_trash_category_async: {ie}.\
                Controls: {dlg_modal.content.controls if dlg_modal else 'dlg_modal não definido'}")  # type: ignore
            # Ainda assim, fechar o diálogo em caso de erro interno
            if dlg_modal:
                page.close(dlg_modal)
            if not operation_complete_future.done():
                operation_complete_future.set_result(False)
        except Exception as ex:
            logger.error(
                f"Erro durante a operação '{status.name}' ao enviar para lixeira: {ex}")
            if dlg_modal:
                page.close(dlg_modal)
            page_ctx.update()
            message_snackbar(
                message=f"Erro ao enviar para lixeira: {ex}", message_type=MessageType.ERROR, page=page_ctx)
            if not operation_complete_future.done():
                operation_complete_future.set_result(False)

    def close_dlg(e_close):
        page.close(dlg_modal)
        e_close.page.update()
        if not operation_complete_future.done():
            operation_complete_future.set_result(False)  # Usuário cancelou

    text = (
        "Aviso: Este registro será excluído permanentemente após 90 dias. "
        "Caso exista produtos vinculados a esta categoria, "
        "ficará com o status 'Obsoleto' (INATIVO) e não poderá ser excluída definitivamente."
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
                ft.Text(categoria.name,
                        weight=ft.FontWeight.BOLD, selectable=True),
                ft.Text(f"ID: {categoria.id}", selectable=True),
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
                              on_click=send_to_trash_category_async),
            ft.OutlinedButton("Não", icon=ft.Icons.CLOSE, on_click=close_dlg),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
        on_dismiss=lambda e_dismiss: (
            logger.info(
                f"Modal dialog para categoria {categoria.id} ({status.name}) foi descartado."),
            # Garante que a future seja resolvida se descartado
            close_dlg(e_dismiss)
        )
    )
    # Adiciona ao overlay e abre
    # Usar e.control.page garante pegar a página do contexto do clique original
    page.open(dlg_modal)
    return await operation_complete_future


def restore_from_trash(page: ft.Page, categoria: ProdutoCategorias) -> bool:
    logger.info(f"Restaurando categoria ID: {categoria.id} da lixeira")
    current_user = get_current_user(page)
    result = category_controllers.handle_update_status(categoria=categoria, current_user=current_user, status=RegistrationStatus.ACTIVE)

    if result["status"] == "error":
        message_snackbar(page, result["message"], MessageType.ERROR)
        return False
    message_snackbar(page, message="Categoria restaurada com sucesso!")
    return True
