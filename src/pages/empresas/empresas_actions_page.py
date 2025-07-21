import logging
import flet as ft
import asyncio

import src.domains.empresas.controllers.empresas_controllers as company_controllers
from src.domains.shared.context.session import get_current_user
import src.domains.usuarios.controllers.usuarios_controllers as user_controllers
from src.domains.empresas.models.empresas_model import Empresa
from src.domains.shared import RegistrationStatus

from src.shared.utils import MessageType, message_snackbar

logger = logging.getLogger(__name__)


async def send_to_trash(page: ft.Page, empresa: Empresa, status: RegistrationStatus = RegistrationStatus.DELETED) -> bool:
    operation_complete_future = asyncio.Future()
    # Definir dlg_modal ANTES de usá-lo em delete_company

    def send_to_trash_company_async(e_trash):
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

            # OPERAÇÃO SOFT DELETE: Muda o status para excluído a empresa pelo ID
            # ToDo: Verificar se há produtos, pedidos, ou estoque para este empresa_id se a operação for DELETAR
            """
            Aviso: Se houver produtos, pedidos ou estoque vinculados, o status será definido como RegistrationStatus.ARCHIVED.
            Caso contrário, o registro poderá ter o status RegistrationStatus.DELETED.
            Esta aplicação não exclui efetivamente o registro, apenas altera seu status.
            A exclusão definitiva ocorrerá após 90 dias da mudança para RegistrationStatus.DELETED, realizada periodicamente por uma Cloud Function.
            """

            logger.info(
                f"Iniciando operação '{status.name}' para empresa ID: {empresa.id}")
            # Implemente aqui a lógica para buscar produtos, pedidos e estoque vinculados.
            # ...
            # Se não há pedido, produtos ou estoque vinculado a esta empresa, mudar o status para DELETED
            # Caso contrário, muda o status para ARCHIVED
            current_user = get_current_user(page_ctx)
            result = company_controllers.handle_update_status_empresas(empresa=empresa, current_user=current_user, status=status)

            page.close(dlg_modal)  # Fechar diálogo antes de um possível snackbar

            if result["status"] == "error":
                message_snackbar(
                    message=result['message'], message_type=MessageType.WARNING, page=page_ctx)
                if not operation_complete_future.done():
                    operation_complete_future.set_result(False)
                return

            # Se a empresa deletada é a que está logada, limpa do app_state.
            if empresa.id == page_ctx.app_state.empresa.get('id'):
                page_ctx.app_state.clear_empresa_data()

            logger.info(
                f"Operação '{status.name}' para empresa ID: {empresa.id} concluída com sucesso.")
            if not operation_complete_future.done():
                operation_complete_future.set_result(True)

        except IndexError as ie:  # Deveria ser menos provável com referência direta
            # type: ignore
            logger.error(
                f"IndexError em send_to_trash_company_async: {ie}.\
                Controls: {dlg_modal.content.controls if dlg_modal else 'dlg_modal não definido'}")  # type: ignore
            # Ainda assim, fechar o diálogo em caso de erro interno
            if dlg_modal:
                page.close(dlg_modal)
            page_ctx.update()
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

    text = "Aviso: A empresa será movida para a lixeira e permanecerá lá indefinidamente até que você a restaure."
    action_title = "Mover para lixeira?"

    if status == RegistrationStatus.DELETED:
        text = (
            "Aviso: Este registro será excluído permanentemente após 90 dias. "
            "Caso exista estoque ou pedidos vinculados a esta empresa, "
            "ela será arquivada e não poderá ser excluída definitivamente."
        )
    elif status == RegistrationStatus.INACTIVE:
        action_title = "Arquivar empresa?"
        text = "Aviso: A empresa será arquivada e permanecerá assim indefinidamente até que você a restaure ou exclua."

    warning_text = ft.Text(
        value=text,
        theme_style=ft.TextThemeStyle.BODY_MEDIUM,
        selectable=True,
        expand=True,
    )

    status_processing_text = ft.Text(
        "Processando sua solicitação. Aguarde...", visible=False)

    # Um AlertDialog Responsivo com limite de largura para 700 pixels
    dlg_modal = ft.AlertDialog(
        modal=True,
        title=ft.Text(action_title),
        content=ft.Column(
            [
                ft.Text(empresa.corporate_name,
                        weight=ft.FontWeight.BOLD, selectable=True),
                ft.Text(f"ID: {empresa.id}", selectable=True),
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
                              on_click=send_to_trash_company_async),
            ft.OutlinedButton("Não", icon=ft.Icons.CLOSE, on_click=close_dlg),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
        on_dismiss=lambda e_dismiss: close_dlg(e_dismiss) # Garante que a future seja resolvida se descartado
    )
    # Adiciona ao overlay e abre
    # Usar e.control.page garante pegar a página do contexto do clique original
    page.open(dlg_modal)
    # page.update()
    return await operation_complete_future


def restore_from_trash(page: ft.Page, empresa: Empresa) -> bool:
    logger.info(f"Restaurando empresa ID: {empresa.id} da lixeira")
    result = company_controllers.handle_update_status_empresas(
        empresa=empresa,
        current_user=get_current_user(page),
        status=RegistrationStatus.ACTIVE)

    if result["status"] == "error":
        message_snackbar(
            page=page, message=result["message"], message_type=MessageType.ERROR)
        return False
    message_snackbar(page=page, message="Empresa restaurada com sucesso!")
    return True


def user_update(current_user) -> dict:
    return user_controllers.handle_update_user_companies(
        usuario_id=current_user.id,
        empresas=current_user.empresas,
        empresa_ativa_id=current_user.empresa_id
    )
