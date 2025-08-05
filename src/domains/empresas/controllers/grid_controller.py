import logging
from typing import Optional
import flet as ft

import src.domains.empresas.controllers.empresas_controllers as company_controllers
from src.domains.empresas.views.empresas_grid_ui import EmpresasGridUI
import src.pages.empresas.empresas_actions_page as empresas_actions_page
from src.domains.shared import RegistrationStatus
from src.domains.shared.context.session import get_current_user
from src.shared.utils import MessageType, message_snackbar, show_banner

logger = logging.getLogger(__name__)


class GridController:
    def __init__(self, page: ft.Page):
        self.page = page
        self.ui: Optional["EmpresasGridUI"] = None  # Será injetado depois
        self._empresas_data = []
        self._empresas_inactivated = 0

    async def load_data_and_update_ui(self):
        if not self.ui:
            return

        self.ui.show_loading()

        set_empresas = get_current_user(self.page).empresas or set()

        try:
            if set_empresas:
                result = company_controllers.handle_get_empresas(ids_empresas=set_empresas)
                if result["status"] == "success":
                    self._empresas_data = result['data']['empresas']
                    self._empresas_inactivated = result['data']['inactivated']
                else:
                    self._empresas_data = []
                    self._empresas_inactivated = 0
            else:
                self._empresas_data = []
                self._empresas_inactivated = 0

            self.ui.render_grid(self._empresas_data)

        except Exception as e:
            logger.error(f"Erro ao carregar empresas: {e}")
            self.ui.show_error(str(e))
        finally:
            self.ui.update_trash_fab(self._empresas_inactivated)
            self.ui.show_content()
            if self.page.client_storage:
                self.page.update()

    async def handle_action_click(self, e):
        action = e.control.data.get('action')
        empresa = e.control.data.get('data')

        match action:
            case "INSERT":
                self.page.app_state.clear_form_data()  # type: ignore
                self.page.go('/home/empresas/form/principal')
            case "SELECT":
                self.page.app_state.set_empresa(empresa.to_dict())  # type: ignore
                result = empresas_actions_page.user_update(get_current_user(self.page))

                if result['status'] == 'error':
                    logger.warning(result['message'])
                    message_snackbar(message=result['message'], message_type=MessageType.WARNING, page=self.page)
                    return
                self.page.go('/home')
            case "MAIN_DATA":
                self.page.app_state.set_form_data(empresa.to_dict())  # type: ignore
                self.page.go('/home/empresas/form/principal')
            case "TAX_DATA":
                if empresa.cnpj:
                    self.page.app_state.set_form_data(empresa.to_dict())  # type: ignore
                    self.page.go('/home/empresas/form/dados-fiscais')
                else:
                    show_banner(page=self.page, message="É preciso definir o CNPJ da empresa em Dados Principais antes de definir os dados fiscais")
            case "DIGITAL_CERTIFICATE":
                logger.info(f"Aguardando implementação: Certificado digital {empresa.id}")
            case "SOFT_DELETE":
                is_deleted = await empresas_actions_page.send_to_trash(page=self.page, empresa=empresa, status=RegistrationStatus.DELETED)
                if is_deleted:
                    await self.load_data_and_update_ui()
            case "ARCHIVE":
                is_archived = await empresas_actions_page.send_to_trash(page=self.page, empresa=empresa, status=RegistrationStatus.INACTIVE)
                if is_archived:
                    await self.load_data_and_update_ui()

    def handle_info_click(self, e):
        empresa = e.control.data.get('data')
        page_ctx = e.control.page

        info_messages_list = []
        if not empresa.cnpj:
            info_messages_list.append("CNPJ: Não informado para emissão de NFCe.")
        if not empresa.certificate_a1:
            info_messages_list.append("A1: Certificado A1 não informado para emissão de NFCe.")
        if empresa.get_complete_address() == "Endereço não informado":
            info_messages_list.append("Endereço: Não informado.")
        if not empresa.is_nfce_enabled():
            info_messages_list.append("NFCe: Não configurado.")

        final_info_message = "\n".join(info_messages_list)
        if not final_info_message:
            final_info_message = "Esta empresa está configurada para emitir NFCe."

        def close_dialog(e_dialog):
            info_dialog.open = False
            page_ctx.update()

        info_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Status da Empresa"),
            content=ft.Text(final_info_message),
            actions=[ft.TextButton("Entendi", on_click=close_dialog)],
            actions_alignment=ft.MainAxisAlignment.END,
            on_dismiss=lambda _: logger.info(f"Dialog de informação para {empresa.id} dispensado.")
        )

        page_ctx.overlay.append(info_dialog)
        info_dialog.open = True
        page_ctx.update()

    def handle_icon_hover(self, e):
        e.control.bgcolor = ft.Colors.with_opacity(0.1, ft.Colors.WHITE) if e.data == "true" else ft.Colors.TRANSPARENT
        e.control.update()