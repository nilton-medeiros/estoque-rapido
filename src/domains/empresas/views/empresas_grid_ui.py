import flet as ft
from typing import TYPE_CHECKING

from src.pages.partials.app_bars.appbar import create_appbar_menu

if TYPE_CHECKING:
    from src.domains.empresas.controllers.grid_controller import GridController


class EmpresasGridUI:
    def __init__(self, page: ft.Page, controller: "GridController"):
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
                src=f"images/steel_cabinets_documents_empty.png",
                error_content=ft.Text("Nenhuma empresa cadastrada"),
                width=300,
                height=300,
                fit=ft.ImageFit.COVER,
                border_radius=ft.border_radius.all(10),
            ),
            margin=ft.margin.only(top=100),
            alignment=ft.alignment.center,
        )

        self.fab_add = ft.FloatingActionButton(
            tooltip="Adicionar empresa",
            icon=ft.Icons.ADD,
            data={'action': 'INSERT', 'data': None},
            on_click=self.controller.handle_action_click
        )

        self.fab_trash = ft.FloatingActionButton(
            content=ft.Image(
                src=f"icons/recycle_empy_1771.png",
                fit=ft.ImageFit.CONTAIN,
                error_content=ft.Text("Erro"),
            ),
            on_click=lambda _: self.page.go("/home/empresas/grid/lixeira"),
            tooltip="Empresas inativas: 0",
            bgcolor=ft.Colors.TRANSPARENT,
        )

    def build(self):
        return ft.View(
            route="/home/empresas/grid",
            controls=[
                self.loading_container,
                self.content_area
            ],
            appbar=create_appbar_menu(page=self.page, title=ft.Text("Empresas", size=18)),
            drawer=self.page.drawer,
            floating_action_button=ft.Column(
                controls=[self.fab_add, self.fab_trash],
                alignment=ft.MainAxisAlignment.END,
            ), # type: ignore
            vertical_alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            padding=ft.padding.all(10)
        )

    def create_company_card(self, empresa):
        return ft.Card(
            content=ft.Container(
                padding=15,
                content=ft.Column([
                    ft.Row(
                        controls=[
                            ft.Text(f"{empresa.corporate_name}", weight=ft.FontWeight.BOLD),
                            ft.Container(
                                content=ft.PopupMenuButton(
                                    icon=ft.Icons.MORE_VERT, tooltip="Mais Ações",
                                    items=[
                                        ft.PopupMenuItem(text="Selecionar empresa", tooltip="Escolha esta empresa para trabalhar com ela", icon=ft.Icons.SELECT_ALL, data={'action': 'SELECT', 'data': empresa}, on_click=self.controller.handle_action_click),
                                        ft.PopupMenuItem(text="Dados principais", tooltip="Ver ou editar dados principais da empresa", icon=ft.Icons.EDIT_NOTE_OUTLINED, data={'action': 'MAIN_DATA', 'data': empresa}, on_click=self.controller.handle_action_click),
                                        ft.PopupMenuItem(text="Dados fiscais", tooltip="Ver ou editar dados fiscais da empresa", icon=ft.Icons.RECEIPT_LONG_OUTLINED, data={'action': 'TAX_DATA', 'data': empresa}, on_click=self.controller.handle_action_click),
                                        ft.PopupMenuItem(text="Certificado digital", tooltip="Informações e upload do certificado digital", icon=ft.Icons.SECURITY_OUTLINED, data={'action': 'DIGITAL_CERTIFICATE', 'data': empresa}, on_click=self.controller.handle_action_click),
                                        ft.PopupMenuItem(text="Excluir empresa", tooltip="Move empresa para a lixeira, após 90 dias remove do banco de dados", icon=ft.Icons.DELETE_OUTLINE, data={'action': 'SOFT_DELETE', 'data': empresa}, on_click=self.controller.handle_action_click),
                                        ft.PopupMenuItem(text="Arquivar empresa", tooltip="A empresa será movida para a lixeira e permanecerá lá indefinidamente até que você a restaure.", icon=ft.Icons.INVENTORY_2_OUTLINED, data={'action': 'ARCHIVE', 'data': empresa}, on_click=self.controller.handle_action_click),
                                    ],
                                ),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Text(f"{empresa.trade_name if empresa.trade_name else 'Nome fantasia N/A'}", theme_style=ft.TextThemeStyle.BODY_MEDIUM),
                    ft.Text(f"{empresa.store_name if empresa.store_name else 'Loja N/A'}  {str(empresa.phone) if empresa.phone else ''}", theme_style=ft.TextThemeStyle.BODY_MEDIUM),
                    ft.Text(f"CNPJ: {empresa.cnpj if empresa.cnpj else 'N/A'}", theme_style=ft.TextThemeStyle.BODY_MEDIUM),
                    ft.Row(
                        controls=[
                            ft.Text(f"Email: {empresa.email}", theme_style=ft.TextThemeStyle.BODY_SMALL),
                            ft.Container(
                                content=ft.Icon(name=ft.Icons.INFO_OUTLINED, color=ft.Colors.PRIMARY),
                                margin=ft.margin.only(right=10),
                                tooltip="Informações sobre o status",
                                data={'action': 'INFO', 'data': empresa},
                                on_hover=self.controller.handle_icon_hover,
                                on_click=self.controller.handle_info_click,
                                border_radius=ft.border_radius.all(20),
                                ink=True,
                                bgcolor=ft.Colors.TRANSPARENT,
                                alignment=ft.alignment.center,
                                clip_behavior=ft.ClipBehavior.ANTI_ALIAS
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                ])
            ),
            margin=ft.margin.all(5),
            col={"xs": 12, "sm": 6, "md": 4, "lg": 3}
        )

    def render_grid(self, empresas_data):
        self.content_area.controls.clear()
        if not empresas_data:
            self.content_area.controls.append(self.empty_content_display)
        else:
            grid = ft.ResponsiveRow(
                controls=[self.create_company_card(empresa) for empresa in empresas_data],
                columns=12,
                spacing=10,
                run_spacing=10
            )
            self.content_area.controls.append(grid)

    def show_loading(self):
        self.loading_container.visible = True
        self.content_area.visible = False
        if self.page.client_storage:
            self.page.update()

    def show_content(self):
        self.loading_container.visible = False
        self.content_area.visible = True

    def update_trash_fab(self, count):
        current_trash_icon_filename = "recycle_full_1771.png" if count else "recycle_empy_1771.png"
        if self.fab_trash.content and isinstance(self.fab_trash.content, ft.Image):
            self.fab_trash.content.src = f"icons/{current_trash_icon_filename}"
            self.fab_trash.tooltip = f"Empresas inativas: {count}"

    def show_error(self, message: str):
        self.content_area.controls.clear()
        self.content_area.controls.append(
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.ERROR_OUTLINE, color=ft.Colors.RED, size=50),
                    ft.Text("Ocorreu um erro ao carregar as empresas.", color=ft.Colors.RED),
                    ft.Text(f"Detalhes: {message}", color=ft.Colors.RED, size=10),
                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.alignment.center,
                margin=ft.margin.only(top=50),
                expand=True
            )
        )