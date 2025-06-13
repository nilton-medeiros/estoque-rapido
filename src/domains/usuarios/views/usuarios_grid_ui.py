# ==========================================
# src/domains/usuarios/views/usuarios_grid_ui.py
# ==========================================
from typing import TYPE_CHECKING
import flet as ft
from src.domains.usuarios.models.usuario_model import Usuario
from src.domains.usuarios.models.grid_models import FilterType
from src.domains.usuarios.components.user_card import UserCard
from src.domains.usuarios.components.filter_components import FilterComponents

if TYPE_CHECKING:
    from src.domains.usuarios.controllers.grid_controller import UsuarioGridController
class UsuarioGridUI:
    """Componente UI principal do grid de usuarios"""

    def __init__(self, controller: 'UsuarioGridController'):
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
        self.search_field = FilterComponents.create_search_field(self._on_search_clicked)

        return ft.AppBar(
            leading=self._create_back_button(),
            title=ft.Text("Usuarios", size=18),
            bgcolor=ft.Colors.with_opacity(0.9, ft.Colors.PRIMARY_CONTAINER),
            adaptive=True,
            actions=[
                ft.Container(content=self.filter_radio, margin=ft.margin.only(left=10, right=10)),
                ft.Container(content=self.search_field, margin=ft.margin.only(left=10, right=10)),
            ],
        )

    def _create_back_button(self) -> ft.Container:
        return ft.Container(
            alignment=ft.alignment.center_left,
            padding=ft.padding.only(left=10),
            content=ft.Container(
                width=40, height=40,
                border_radius=ft.border_radius.all(20),
                content=ft.Icon(ft.Icons.ARROW_BACK),
                on_click=lambda _: self.controller.page.go("/home"),
                tooltip="Voltar",
            ),
        )

    def _create_fab_buttons(self) -> ft.Column:
        self.fab_add = ft.FloatingActionButton(
            tooltip="Adicionar usuario",
            icon=ft.Icons.ADD,
            on_click=self._on_add_clicked
        )

        self.fab_trash = ft.FloatingActionButton(
            content=ft.Image(
                src="icons/recycle_empy_1771.png",
                fit=ft.ImageFit.CONTAIN,
                error_content=ft.Text("Erro"),
            ),
            on_click=lambda _: self.controller.page.go("/home/usuarios/grid/lixeira"),
            tooltip="Usuarios inativos: 0",
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

    def render_grid(self, usuarios: list[Usuario]):
        """Renderiza o grid com os usuarios filtrados"""
        self.content_area.controls.clear()

        if not usuarios:
            self.content_area.controls.append(self._create_empty_content())
        else:
            grid = self._create_users_grid(usuarios)
            self.content_area.controls.append(grid)

        self._update_fab_trash_state()

        if self.controller.page.client_storage:
            self.controller.page.update()

    def _create_empty_content(self) -> ft.Container:
        return ft.Container(
            content=ft.Image(
                src="images/empty_folder.png",
                error_content=ft.Text("Nenhum usuario cadastrado"),
                width=300, height=300,
                fit=ft.ImageFit.CONTAIN,
            ),
            margin=ft.margin.only(top=100),
            alignment=ft.alignment.center,
        )

    def _create_users_grid(self, usuarios: list[Usuario]) -> ft.ResponsiveRow:
        """Cria o grid responsivo de usuarios"""
        cards = []
        for usuario in usuarios:
            # Passar o novo método do controller que lida com page.run_task
            card = UserCard.create(usuario, self.controller.execute_action_async)
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
            self.fab_trash.tooltip = f"Usuarios inativos: {self.controller.state.inactive_count}"

    # Event Handlers
    def _on_radio_changed(self, e):
        self.controller.state.filter_type = FilterType(e.control.value)
        self._apply_filters()

    def _on_search_clicked(self, e):
        if self.search_field.value:
            if e.control.icon in [ft.Icons.FILTER_ALT_OFF, ft.Icons.FILTER_ALT_OFF_OUTLINED]:
                self.search_field.value = ""
        self._apply_filters()

    def _on_add_clicked(self, e):
        self.controller.execute_action_async("INSERT", None)

    def _apply_filters(self):
        """Aplica filtros e atualiza a UI"""
        self.controller.state.search_text = self.search_field.value or ""
        filtered_usuarios = self.controller.filter_usuarios()

        # Atualiza visual do campo de busca
        self._update_search_field_visual(filtered_usuarios)

        self.render_grid(filtered_usuarios)

    def _update_search_field_visual(self, filtered_usuarios: list[Usuario]):
        """Atualiza o visual do campo de busca baseado nos resultados"""
        suffix = self.search_field.suffix
        if not isinstance(suffix, ft.IconButton):
            return

        search_text = self.controller.state.search_text.strip()

        if search_text:
            if filtered_usuarios:
                self.search_field.color = ft.Colors.GREEN
                suffix.icon = ft.Icons.FILTER_ALT_OFF
                suffix.icon_color = ft.Colors.GREEN
            else:
                self.search_field.color = ft.Colors.RED
                suffix.icon = ft.Icons.FILTER_ALT_OFF_OUTLINED
                suffix.icon_color = ft.Colors.RED
        else:
            self.search_field.color = ft.Colors.WHITE
            suffix.icon = ft.Icons.FILTER_ALT_OUTLINED
            suffix.icon_color = ft.Colors.PRIMARY
