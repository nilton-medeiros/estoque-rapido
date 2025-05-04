import logging
import flet as ft

import src.domains.empresas.controllers.empresas_controllers as empresas_controllers
from src.domains.empresas.models.empresa_subclass import Status
import src.domains.usuarios.controllers.usuarios_controllers as usuarios_controllers

from src.shared import MessageType, message_snackbar

logger = logging.getLogger(__name__)


async def delete(empresa, page: ft.Page) -> None:
    # Definir dlg_modal ANTES de usá-lo em delete_company
    # Renomear 'e' para evitar conflito com o 'e' de handle_action_click

    async def delete_company(e_delete):
        # Obter a página a partir do evento é mais seguro em callbacks
        page = e_delete.page

        # --- Acesso ao controle de texto ---
        try:
            # dlg_modal é acessível aqui devido ao closure
            status_text_control = dlg_modal.content.controls[2]
            status_text_control.visible = True  # Mostra o texto de 'Aguarde...'

            # Opcional: Desabilitar botões enquanto processa
            for btn in dlg_modal.actions:
                btn.disabled = True

            # Atualizar a página (ou o diálogo) para mostrar a mudança
            # Usar e_delete.page garante que estamos atualizando a página correta
            page.update()

            # OPERAÇÃO SOFT DELETE: Muda o status para excluído a empresa pelo ID
            # ToDo: Verificar se há produtos, pedidos, ou estoque para este empresa_id
            """
            Aviso: Se houver produtos, pedidos ou estoque vinculados, o status será definido como Status.ARCHIVED.
            Caso contrário, o registro poderá ter o status Status.DELETED.
            Esta aplicação não exclui efetivamente o registro, apenas altera seu status.
            A exclusão definitiva ocorrerá após 90 dias da mudança para Status.DELETED, realizada periodicamente por uma Cloud Function.
            """

            print(f"Lógica de exclusão para {empresa.id} em execução...")
            # Implemente aqui a lógica para buscar produtos, pedidos e estoque vinculados.
            # ...
            # Se não há pedido, produtos ou estoque vinculado a esta empresa, mudar o status para DELETED
            # Caso contrário, muda o status para ARCHIVED
            status = Status.DELETED  # Até implementar pesquisa de vínculo, assume que não há vínculo
            result = await empresas_controllers.handle_status_empresas(empresa.id, status=status)

            if result.get('is_error'):
                # Fechar o diálogo
                dlg_modal.open = False
                page.update()
                message_snackbar(
                    message=result['message'], message_type=MessageType.WARNING, page=page)
                return False

            empresa.set_status(status)
        except IndexError:
            logger.debug(
                "Erro: Não foi possível encontrar o controle de texto de status (índice 2).")
            print(
                "Debug: Erro: Não foi possível encontrar o controle de texto de status (índice 2).")
            # Ainda assim, fechar o diálogo em caso de erro interno
            dlg_modal.open = False
            page.update()
            return False
        except Exception as ex:
            print(f"Erro durante a exclusão: {ex}")
            dlg_modal.open = False
            page.update()
            message_snackbar(
                message=f"Erro ao excluir empresa: {ex}", message_type=MessageType.ERROR, page=page)
            return False

        # Se a empresa deletada é a que está logada, limpa do app_state.
        if empresa.id == page.app_state.empresa.get('id'):
            page.app_state.clear_empresa_data()

        print(
            f"Debug  ->  empresa_id: {empresa.id}, state.empresa.id: {page.app_state.empresa.get('id')}")
        print("Debug:  ->  Empresa excluída com sucesso! Fechando dialog dlg_modal")
        # Fim do for: Fechar o diálogo
        dlg_modal.open = False
        page.update()
        return True

    def close_dlg(e_close):
        dlg_modal.open = False
        e_close.page.update()

    warning_text = ft.Text(
        "Aviso: Este registro será excluído permanentemente após 90 dias. "
        "Caso exista estoque ou pedidos vinculados a esta empresa, "
        "a empresa será apenas arquivada e não poderá ser excluída definitivamente.",
        theme_style=ft.TextThemeStyle.BODY_MEDIUM,
        selectable=True,
        expand=True,
    )

    # Um AlertDialog Responsivo com limite de largura para 700 pixels
    dlg_modal = ft.AlertDialog(
        modal=True,
        title=ft.Text("Mover para lixeira?"),
        content=ft.Column(
            [
                ft.Text(empresa.corporate_name,
                        weight=ft.FontWeight.BOLD, selectable=True),
                ft.Text(f"ID: {empresa.id}", selectable=True),
                ft.Row([ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED), warning_text]),
                ft.Text("Movendo empresa para a lixeira. Aguarde...",
                        visible=False),
            ],
            # tight = True: É bom definir tight=True se você fixa a altura com o conteúdo
            # tight = False: Estica a altura até o limite da altura da página
            tight=True,
            width=700,
            spacing=10,
        ),
        actions=[
            # Passa a função delete_company como callback
            ft.TextButton("Sim", on_click=delete_company),
            ft.TextButton("Não", on_click=close_dlg),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
        on_dismiss=lambda e_dismiss: print("Modal dialog descartado!"),
    )
    # Adiciona ao overlay e abre
    # Usar e.control.page garante pegar a página do contexto do clique original
    page.overlay.append(dlg_modal)
    dlg_modal.open = True
    page.update()


async def user_update(usuario_id: str, empresa_id: str, empresas: set) -> None:
    return await usuarios_controllers.handle_update_empresas_usuarios(
        usuario_id=usuario_id,
        empresas=empresas,
        empresa_ativa_id=empresa_id
    )


async def show_banner(page: ft.Page, message) -> None:
    def close_banner(e):
        banner.open = False
        e.control.page.update()

    banner = ft.Banner(
        bgcolor=ft.Colors.PRIMARY,
        leading=ft.Icon(ft.Icons.WARNING_AMBER, color=ft.Colors.ON_PRIMARY, size=40),
        content=ft.Text(message, color=ft.Colors.ON_PRIMARY),
        actions=[ft.ElevatedButton(
            text="Entendi",
            style=ft.ButtonStyle(
                color=ft.Colors.ON_PRIMARY_CONTAINER,
                bgcolor=ft.Colors.PRIMARY_CONTAINER,
            ),
            on_click=close_banner
        )],
    )

    page.overlay.append(banner)
    banner.open = True
    page.update()
