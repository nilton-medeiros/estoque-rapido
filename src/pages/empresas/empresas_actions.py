import logging
import flet as ft

import src.domains.empresas.controllers.empresas_controllers as empresas_controllers
import src.domains.usuarios.controllers.usuarios_controllers as usuarios_controllers

from src.shared import MessageType, message_snackbar

logger = logging.getLogger(__name__)

def delete(empresa, page: ft.Page) -> None:
    # Definir dlg_modal ANTES de usá-lo em delete_company
        # Renomear 'e' para evitar conflito com o 'e' de handle_action_click
    async def delete_company(e_delete):
        print('Deletando empresa...')

        # --- Acesso ao controle de texto ---
        try:
            # dlg_modal é acessível aqui devido ao closure
            status_text_control = dlg_modal.content.controls[2]
            status_text_control.visible = True

            # Opcional: Desabilitar botões enquanto processa
            for btn in dlg_modal.actions:
                btn.disabled = True

            # Atualizar a página (ou o diálogo) para mostrar a mudança
            # Usar e_delete.page garante que estamos atualizando a página correta
            e_delete.page.update()

            # print(f"Lógica de exclusão para {empresa.id} executada.")
            result = await empresas_controllers.handle_delete_empresas(empresa.id)
            # --- Após a exclusão ---
            # Se empresa excluída com sucesso, atualiza empresas do usuário

            page = e_delete.page  # Obter a instância da página a partir do evento

            if result.get('is_error'):
                # Fechar o diálogo
                dlg_modal.open = False
                e_delete.page.update()
                message_snackbar(
                    message=result['message'], message_type=MessageType.WARNING, page=page)
                return False

        except IndexError:
            logger.debug(
                "Erro: Não foi possível encontrar o controle de texto de status (índice 2).")
            print(
                "Debug: Erro: Não foi possível encontrar o controle de texto de status (índice 2).")
            # Ainda assim, fechar o diálogo em caso de erro interno
            dlg_modal.open = False
            e_delete.page.update()
            return False
        except Exception as ex:
            print(f"Erro durante a exclusão: {ex}")
            dlg_modal.open = False
            e_delete.page.update()
            message_snackbar(
                message=f"Erro ao excluir empresa: {ex}", message_type=MessageType.ERROR, page=e_delete.page)
            return False

        try:
            # Busca e atualiza todos os usuários da empresa excluída
            response = await usuarios_controllers.handle_find_all_usuarios(empresa.id)

            if response.get('is_error'):
                # Fechar o diálogo
                dlg_modal.open = False
                e_delete.page.update()
                message_snackbar(
                    message=response['message'], message_type=MessageType.WARNING, page=page)
                return False
        except Exception as ex:
            msg = f"Erro ao consultar todos os usuários da empresa {empresa.id}: {ex}"
            print(msg)
            dlg_modal.open = False
            e_delete.page.update()
            message_snackbar(message=msg, message_type=MessageType.ERROR, page=e_delete.page)
            return False

        usuarios = response['usuarios']

        if not response['usuarios']:
            dlg_modal.open = False
            e_delete.page.update()
            return True

        # Atualiza as empresas dos usuários
        for usuario in usuarios:
            # Atualiza o set de empresas no usuário
            # Discard: Não da erro se a empresa já não existe mais no set de empresas
            usuario.empresas.discard(empresa.id)

            try:
                response = await usuarios_controllers.handle_update_empresas_usuarios(
                    usuario_id=usuario.id, empresas=usuario.empresas, empresa_ativa_id=usuario.empresa_id)

                if response.get('is_error'):
                    logger.warning(
                        f"Erro ao atualizar empresas do usuário {usuario.id}: {response['message']}")

                # Se usuario for o usuário logado, atualiza o estado do usuário na aplicação
                if usuario.id == page.app_state.usuario.get('id'):
                    if usuario.empresa_id not in usuario.empresas:
                        usuario.empresa_id = usuario.empresas[0] if usuario.empresas else None
                    page.app_state.set_usuario(usuario.to_dict())
                    # ToDo: Buscar empresa_data no db para empresa usuario.empresa_id
                    # Seta a empresa logada
                    # page.app_state.set_empresa(empresa_data.to_dict())
            except Exception as ex:
                msg = f"Erro ao atualizar empresas do usuário {usuario.id}: {ex}"
                logger.error(msg)
                print(msg)
                dlg_modal.open = False
                e_delete.page.update()
                message_snackbar(message=msg, message_type=MessageType.ERROR, page=e_delete.page)
                return False

        # Se a empresa deletada é a que está logada, limpa do app_state.
        if empresa.id == page.app_state.empresa.get('id'):
            page.app_state.clear_empresa_data()

        # Fechar o diálogo
        dlg_modal.open = False
        return True

    def close_dlg(e_close):  # Renomear 'e'
        dlg_modal.open = False
        e_close.page.update()

    dlg_modal = ft.AlertDialog(
        modal=True,
        title=ft.Text("Por favor confirme"),
        content=ft.Column([
            ft.Text(empresa.corporate_name),
            ft.Text("Você realmente deseja excluir esta empresa?"),
            ft.Text("Excluindo empresa. Aguarde...", visible=False),
        ],
            # É bom definir tight=True se você fixa a altura
            # ou ajustar a altura para caber o novo texto
            height=100, tight=True),
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