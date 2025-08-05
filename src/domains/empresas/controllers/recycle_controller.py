import logging
from typing import TYPE_CHECKING, Optional

import flet as ft

import src.domains.empresas.controllers.empresas_controllers as company_controllers
import src.pages.empresas.empresas_actions_page as empresas_actions_page
import src.pages.shared.recycle_bin_helpers as recycle_helpers
from src.domains.shared.context.session import get_current_user

if TYPE_CHECKING:
    from src.domains.empresas.views.empresas_recycle_ui import EmpresasRecycleUI

logger = logging.getLogger(__name__)


class RecycleController:
    def __init__(self, page: ft.Page):
        self.page = page
        self.ui: Optional["EmpresasRecycleUI"] = None
        self._empresas_data = []
        self._empresas_inactivated = 0

    async def load_data_and_update_ui(self):
        if not self.ui:
            return

        self.ui.show_loading()
        set_empresas = get_current_user(self.page).empresas or set()

        try:
            if set_empresas:
                result = company_controllers.handle_get_empresas(ids_empresas=set_empresas, empresas_inativas=True)
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
            logger.error(f"Erro ao carregar empresas inativas: {e}")
            self.ui.show_error(str(e))
        finally:
            self.ui.update_trash_icon(self._empresas_inactivated)
            self.ui.show_content()
            if self.page.client_storage:
                self.page.update()

    async def handle_action_click(self, e):
        action = e.control.data.get('action')
        empresa = e.control.data.get('data')

        if action == "RESTORE":
            is_restored = empresas_actions_page.restore_from_trash(page=self.page, empresa=empresa)
            if is_restored:
                await self.load_data_and_update_ui()

    def handle_info_click(self, e):
        empresa = e.control.data.get('data')
        page_ctx = e.control.page

        info_message = recycle_helpers.get_deleted_info_message(empresa) if empresa.status.name == 'DELETED' else "Esta empresa está arquivada e não será removida automaticamente."

        def close_dialog(e_dialog):
            info_dialog.open = False
            page_ctx.update()

        info_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Informação da Empresa"),
            content=ft.Text(info_message),
            actions=[ft.TextButton("Entendi", on_click=close_dialog)],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        page_ctx.overlay.append(info_dialog)
        info_dialog.open = True
        page_ctx.update()

    def handle_icon_hover(self, e):
        """Muda o bgcolor do container no hover."""
        e.control.bgcolor = ft.Colors.with_opacity(
            0.1, ft.Colors.WHITE) if e.data == "true" else ft.Colors.TRANSPARENT
        e.control.update()