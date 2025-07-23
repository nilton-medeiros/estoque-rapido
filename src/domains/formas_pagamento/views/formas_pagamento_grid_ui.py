from typing import TYPE_CHECKING
import flet as ft
from src.domains.formas_pagamento.components.filter_components import FilterComponents
from src.domains.formas_pagamento.components.formas_pagamento_card import FormasPagamentoCard
from src.domains.formas_pagamento.models.formas_pagamento_model import FormaPagamento
from src.domains.shared.models.filter_type import FilterType
from src.pages.partials.app_bars.appbar import create_appbar_menu

if TYPE_CHECKING:
    from src.domains.formas_pagamento.controllers.grid_controller import FormaPagamentoGridController

class FormasPagamentoGridUI:
    """Componente UI principal do grid de formas de pagamento"""

    def __init__(self, controller: 'FormaPagamentoGridController'):
        self.controller = controller
        self.controller.ui_components = self

        # Componentes da UI
        self.loading_container = self._create_loading_container()
        self.content_area = self._create_content_area()
        self.appbar = self._create_appbar()
        self.fab_buttons = self._create_fab_buttons()

    def _create_loading_container(self) -> ft.Container:
        return ft.Container(
            content=ft.ProgressRing(width=32, height=32, stroke_width=3),
            alignment=ft.alignment.center,
            expand=True,
            visible=True
        )

    def _create_content_area(self) -> ft.Column:
        return ft.Column(
            controls=[],
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True,
            visible=False,
            scroll=ft.ScrollMode.ADAPTIVE
        )

    def _create_appbar(self) -> ft.AppBar:
        """Cria a AppBar com filtros"""
        self.filter_radio = FilterComponents.create_radio_filter(self._on_radio_changed)

        return create_appbar_menu(
            page=self.controller.page,
            title=ft.Text("Formas de Pagamento", size=18),
            actions=[
                ft.Container(content=self.filter_radio, margin=ft.margin.only(left=10, right=10)),
            ]
        )

    def _create_fab_buttons(self) -> ft.Column:
        self.fab_add = ft.FloatingActionButton(
            tooltip="Adicionar formas de pagamento",
            icon=ft.Icons.ADD,
            on_click=self._on_add_clicked
        )

        self.fab_trash = ft.FloatingActionButton(
            content=ft.Image(
                src="icons/recycle_empy_1771.png",
                fit=ft.ImageFit.CONTAIN,
                error_content=ft.Text("Erro"),
            ),
            on_click=lambda _: self.controller.page.go("/home/formasdepagamento/grid/lixeira"),
            tooltip="Formas de Pagamento inativas: 0",
            bgcolor=ft.Colors.TRANSPARENT,
        )

        return ft.Column(
            controls=[self.fab_add, self.fab_trash],
            alignment=ft.MainAxisAlignment.END,
        )

    def update_loading_state(self, is_loading: bool):
        """Atualiza estado de carregamento"""
        self.loading_container.visible = is_loading
        self.content_area.visible = not is_loading
        if self.controller.page.client_storage:
            self.controller.page.update()

    def render_grid(self, formas_pagamentos: list[FormaPagamento]):
        """Renderiza a grid com as formas de pagamentos filtrados"""
        self.content_area.controls.clear()

        if not formas_pagamentos:
            self.content_area.controls.append(self._create_empty_content())
        else:
            grid = self._create_formas_pagamento_grid(formas_pagamentos)
            self.content_area.controls.append(grid)

        self._update_fab_trash_state()

        if self.controller.page.client_storage:
            self.controller.page.update()

    def _create_empty_content(self) -> ft.Container:
        return ft.Container(
            content=ft.Image(
                src=f"images/steel_cabinets_documents_empty.png",
                error_content=ft.Text("Nenhuma forma de pagamento cadastrada"),
                width=300, height=300,
                fit=ft.ImageFit.CONTAIN,
            ),
            margin=ft.margin.only(top=100),
            alignment=ft.alignment.center,
        )

    def _create_formas_pagamento_grid(self, formas_pagamentos: list[FormaPagamento]) -> ft.ResponsiveRow:
        """Cria a grid responsivo de formas de pagamentos"""
        cards = []
        for fp in formas_pagamentos:
            card = FormasPagamentoCard.create(fp, self.controller.execute_action_async)
            cards.append(card)

        return ft.ResponsiveRow(
            controls=cards,
            columns=12,
            spacing=10,
            run_spacing=10
        )

    def _update_fab_trash_state(self):
        """Atualiza o estado do FAB da lixeira"""
        icon_filename = "recycle_full_1771.png" if self.controller.state.inactive_count else "recycle_empy_1771.png"

        if isinstance(self.fab_trash.content, ft.Image):
            self.fab_trash.content.src = f"icons/{icon_filename}"
            self.fab_trash.tooltip = f"Formas de Pagamento inativos: {self.controller.state.inactive_count}"

    # Event Handlers
    def _on_radio_changed(self, e):
        self.controller.state.filter_type = FilterType(e.control.value)
        self._apply_filters()

    def _on_add_clicked(self, e):
        self.controller.execute_action_async("INSERT", None)

    def _apply_filters(self):
        """Aplica filtros e atualiza a UI"""
        filtered_formas_pagamento = self.controller.filter_formas_pagamento()
        self.render_grid(filtered_formas_pagamento)
