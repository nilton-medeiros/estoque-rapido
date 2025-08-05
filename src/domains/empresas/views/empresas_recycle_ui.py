import flet as ft
from typing import TYPE_CHECKING

from src.pages.partials.app_bars.appbar import create_appbar_back
from src.pages.shared.components import create_recycle_bin_card
from src.shared.utils import format_datetime_to_utc_minus_3

if TYPE_CHECKING:
    from src.domains.empresas.controllers.recycle_controller import RecycleController


class EmpresasRecycleUI:
    def __init__(self, page: ft.Page, controller: "RecycleController"):
        self.page = page
        self.controller = controller

        self.loading_container = ft.Container(
            content=ft.ProgressRing(width=32, height=32, stroke_width=3),
            alignment=ft.alignment.center,
            expand=True,
            visible=True
        )

        self.content_area = ft.Column(
            controls=[],
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True,
            visible=False,
            scroll=ft.ScrollMode.ADAPTIVE
        )

        self.empty_content_display = ft.Container(
            content=ft.Image(
                src="icons/recycle_empy_1772.png",
                error_content=ft.Text("Vazio"),
                width=300, height=300,
                fit=ft.ImageFit.COVER,
                border_radius=ft.border_radius.all(10),
            ),
            margin=ft.margin.only(top=100),
            alignment=ft.alignment.center,
        )

        self.trash_icon_image = ft.Image(
            src="icons/recycle_empy_1771.png",
            fit=ft.ImageFit.CONTAIN,
            error_content=ft.Text("Erro"),
        )

    def build(self):
        return ft.View(
            route="/home/empresas/grid/lixeira",
            controls=[self.loading_container, self.content_area],
            appbar=create_appbar_back(
                page=self.page,
                title=ft.Text("Empresas excluídas ou arquivadas", size=18),
                actions=[
                    ft.Container(
                        width=43, height=43,
                        border_radius=ft.border_radius.all(20),
                        ink=True,
                        bgcolor=ft.Colors.TRANSPARENT,
                        alignment=ft.alignment.center,
                        content=self.trash_icon_image,
                        margin=ft.margin.only(right=10),
                        clip_behavior=ft.ClipBehavior.ANTI_ALIAS
                    ),
                ],
            ),
            drawer=self.page.drawer,
            vertical_alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            padding=ft.padding.all(10)
        )

    def create_card_for_recycled_company(self, empresa):
        return create_recycle_bin_card(
            entity=empresa,
            top_content=ft.Text(f"{empresa.corporate_name}", color=ft.Colors.WHITE70, weight=ft.FontWeight.BOLD),
            title_text=f"{empresa.store_name if empresa.store_name else 'Loja N/A'}",
            subtitle_controls=[
                ft.Text(f"CNPJ: {empresa.cnpj if empresa.cnpj else 'N/A'}", color=ft.Colors.WHITE54, theme_style=ft.TextThemeStyle.BODY_MEDIUM),
                ft.Text(f"{str(empresa.phone) if empresa.phone else ''}", color=ft.Colors.WHITE54, theme_style=ft.TextThemeStyle.BODY_MEDIUM),
            ],
            status_icon=ft.Icon(
                name=ft.Icons.INVENTORY_2_OUTLINED if empresa.status.name == 'ARCHIVED' else ft.Icons.DELETE_FOREVER_OUTLINED,
                color=ft.Colors.BLUE if empresa.status.name == 'ARCHIVED' else ft.Colors.RED
            ),
            date_text_control=ft.Text(
                value=(f"Arquivado em: {format_datetime_to_utc_minus_3(empresa.archived_at)}" if empresa.status.name == 'ARCHIVED' else f"Excluído em: {format_datetime_to_utc_minus_3(empresa.deleted_at)}"),
                color=ft.Colors.WHITE54 if empresa.status.name == 'ARCHIVED' else ft.Colors.RED,
                theme_style=ft.TextThemeStyle.BODY_SMALL,
            ),
            tooltip_text=('Empresa arquivada não será removida!' if empresa.status.name == 'ARCHIVED' else 'Exclusão permanente após 90 dias'),
            on_action_click=self.controller.handle_action_click,
            on_info_click=self.controller.handle_info_click,
            on_icon_hover=self.controller.handle_icon_hover,
        )

    def render_grid(self, empresas_data):
        self.content_area.controls.clear()
        if not empresas_data:
            self.content_area.controls.append(self.empty_content_display)
        else:
            grid = ft.ResponsiveRow(
                controls=[self.create_card_for_recycled_company(empresa) for empresa in empresas_data],
                columns=12, spacing=10, run_spacing=10
            )
            self.content_area.controls.append(grid)

    def show_loading(self):
        self.loading_container.visible = True
        self.content_area.visible = False

    def show_content(self):
        self.loading_container.visible = False
        self.content_area.visible = True

    def update_trash_icon(self, count):
        self.trash_icon_image.src = f"icons/{'recycle_full_1771.png' if count else 'recycle_empy_1771.png'}"

    def show_error(self, message: str):
        self.content_area.controls.clear()
        self.content_area.controls.append(ft.Text(f"Erro: {message}", color=ft.Colors.RED))