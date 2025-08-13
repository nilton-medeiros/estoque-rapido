import logging

import flet as ft

import src.domains.categorias.controllers.categorias_controllers as category_controllers

from src.domains.shared import RegistrationStatus
from src.domains.categorias.models import ProdutoCategorias

from src.domains.shared.context.session import get_current_user, get_session_colors
from src.pages.partials import build_input_field
from src.pages.partials.app_bars.appbar import create_appbar_back
from src.pages.partials.image_uploader import ImageUploadHandler
from src.shared.utils import message_snackbar, MessageType

logger = logging.getLogger(__name__)


class ProdutoCategoriaForm:
    def __init__(self, page: ft.Page):
        self.page = page
        self.empresa_logada = page.app_state.empresa # type: ignore
        self.data = page.app_state.form_data # type: ignore  # Dados da Categoria (update) ou {} para insert
        # Imagem da categoria
        self.image_url: str | None = None
        self.is_image_url_web = False
        self.previous_image_url: str|None = None
        self.local_upload_file: str|None = None
        # Campos de redimencionamento do formulário
        self.font_size = 18
        self.icon_size = 24
        self.padding = 50
        self.app_colors = get_session_colors(page)
        self.input_width = 400,

        # Responsividade
        self._create_form_fields()
        self.image_uploader = ImageUploadHandler(
            page=self.page,
            image_frame=self.image_frame,
            bucket_prefix=f"empresas/{self.empresa_logada['id']}/categorias"
        )
        self.form = self.build_form()
        self.page.on_resized = self._page_resize

    def on_change_status(self, e):
        status = e.control
        status.label = "Categoria Ativo" if e.data == "true" else "Categoria Inativo (Descontinuado)"
        status.update()

    def _create_form_fields(self):
        """Cria os campos do formulário Categorias de Produto"""
        self.name = build_input_field(
            page_width=self.page.width, # type: ignore
            app_colors=self.app_colors,
            col={'xs': 12, 'md': 12, 'lg': 8},
            label="Nome da Categoria",
            icon=ft.Icons.ASSIGNMENT_OUTLINED,
        )
        # Switch Ativo/Inativo
        self.status = ft.Switch(
            label="Categoria Ativo",
            value=True,
            on_change=self.on_change_status,
            col={'xs': 12, 'md': 12, 'lg': 4})

        # Descrição da categoria
        self.description = build_input_field(
            page_width=self.page.width, # type: ignore
            app_colors=self.app_colors,
            col={'xs': 12, 'md': 12, 'lg': 12},
            label="Descrição (opcional)",
            icon=ft.Icons.ASSIGNMENT_LATE_OUTLINED,
            multiline=True,
            max_lines=5,
        )

        def on_hover_image(e):
            color: str = self.app_colors["container"] if e.data == "true" else self.app_colors["primary"]
            icon_container = self.camera_icon.content
            image_container = self.image_frame
            icon_container.color = color # type: ignore
            image_container.border = ft.border.all(color=color, width=1)
            icon_container.update() # type: ignore
            image_container.update()

        self.image_frame = ft.Container(
            content=ft.Text("Imagem da Categoria (opcional)", italic=True),
            bgcolor=ft.Colors.TRANSPARENT,
            padding=10,
            alignment=ft.alignment.center,
            width=350,
            height=250,
            border=ft.border.all(color=ft.Colors.GREY_400, width=1),
            border_radius=ft.border_radius.all(20),
            on_click=lambda e: self.page.run_task(self.image_uploader.open_dialog, e),
            on_hover=on_hover_image,
            tooltip="Clique aqui para adicionar uma imagem da categoria",
        )
        self.camera_icon = ft.Container(
            content=ft.Icon(
                name=ft.Icons.ADD_A_PHOTO_OUTLINED,
                size=20,
                color=ft.Colors.PRIMARY,
            ),
            margin=ft.margin.only(top=-5),
            ink=True,
            on_hover=on_hover_image,
            on_click=lambda e: self.page.run_task(self.image_uploader.open_dialog, e),
            border_radius=ft.border_radius.all(100),
            padding=8,
        )

        self.image_section = ft.Column(
            controls=[self.image_frame, self.camera_icon],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0,
            width=1400,
        )


    def build_form(self) -> ft.Container:
        """Constrói o formulário de Categoria de Produtos"""
        def responsive_row(controls):
            return ft.ResponsiveRow(
                columns=12,
                expand=True,
                # alignment=ft.MainAxisAlignment.START,
                spacing=20,
                run_spacing=20,
                controls=controls,
            )

        build_content = ft.Column(
            controls=[
                ft.Text("Imagem da categoria de produtos", size=16),
                ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
                responsive_row(controls=[self.image_section]),
                ft.Divider(height=5, color=ft.Colors.TRANSPARENT), # Cria uma linha (espaço vazio) para efeito visual
                ft.Divider(height=10),
                ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
                ft.Text("Dados da Categoria", size=16),
                ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
                responsive_row(controls=[self.name, self.status]),
                ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                responsive_row(controls=[self.description]),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.START,
            spacing=10,
            alignment=ft.MainAxisAlignment.SPACE_EVENLY,
        )

        return ft.Container(
            content=build_content,
            padding=self.padding,
            bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
            border_radius=ft.border_radius.all(20),
        )


    def did_mount(self):
        if self.data and self.data.get('id'):
            # Preenche os campos com os dados fiscais da empresa
            self.populate_form_fields()
        self.page.update()


    def populate_form_fields(self):
        """Preenche os campos do formulário com os dados da categoria"""

        self.name.value = self.data.get('name', '')

        status = self.data.get("status", RegistrationStatus.ACTIVE)

        if status == RegistrationStatus.ACTIVE:
            self.status.value = True
            self.status.label = "Categoria Ativo"
        else:
            self.status.value = False
            self.status.label = "Categoria Inativo (Descontinuado)"

        self.description.value = self.data.get('description', '')

        self.image_uploader.set_initial_image(self.data.get("image_url"))


    def validate_form(self) -> str | None:
        """
        Valida os campos do formulário. Retorna uma mensagem de erro se algum campo obrigatório não estiver preenchido.
        """
        if not self.name.value:
            return "Por favor, preencha o nome da categoria."
        return None


    def _page_resize(self, e):
        if self.page.width < 600:  # type: ignore
            self.font_size = 14
            self.icon_size = 16
            self.padding = 20
            self.input_width = 280,
        elif self.page.width < 1024:  # type: ignore
            self.font_size = 16
            self.icon_size = 20
            self.padding = 40
            self.input_width = 350,
        else:
            self.font_size = 18
            self.icon_size = 24
            self.padding = 50
            self.input_width = 400,

        # Atualiza os tamanhos dos campos do formulário
        self.name.text_size = self.font_size
        self.description.text_size = self.font_size

        # Atualiza o padding do container
        self.form.padding = self.padding
        self.form.update()


    def get_form_object(self) -> ProdutoCategorias:
        """
        Atualiza self.data com os dados do formulário e o retorna atualizado.
        """
        self.data['name'] = self.name.value
        self.data['status'] = RegistrationStatus.ACTIVE if self.status.value else RegistrationStatus.INACTIVE
        self.data['description'] = self.description.value

        self.data['image_url'] = self.image_uploader.get_final_image_url()

        if not self.data.get('empresa_id'):
            self.data["empresa_id"] = self.empresa_logada["id"]

        return ProdutoCategorias.from_dict(self.data)

    def build(self) -> ft.Container:
        return self.form


    def clear_form(self):
        """Limpa os campos do formulário"""
        for field in self.__dict__.values():
            if isinstance(field, ft.TextField):
                field.value = ''
            if isinstance(field, (ft.Switch)):
                field.value = True  # Por default, a categoria sempre é ativa

        # Limpa o buffer com os dados de categorias carregados
        self.data = {}

# Rota: /home/produtos/categorias/form
def show_category_form(page: ft.Page) -> ft.View:
    """Página de cadastro de categorias de produtos."""
    route_title = "home/produtos/categorias/form"
    categoria_data = page.app_state.form_data # type: ignore

    if id := categoria_data.get("id"):
        route_title += f"/{id}"
    else:
        route_title += "/new"

    categorias_view = ProdutoCategoriaForm(page=page)
    categorias_view.did_mount()
    form_container = categorias_view.build()

    def save_form_categorias(e):
        # Valida os dados do formulário
        if msg := categorias_view.validate_form():
            message_snackbar(
                page=page, message=msg, message_type=MessageType.WARNING)
            return

        # Desabilita o botão de salvar para evitar múltiplos cliques
        save_btn.disabled = True

        # Instância do objeto ProdutoCategorias com os dados do formulário para enviar para o backend
        prod_categoria: ProdutoCategorias = categorias_view.get_form_object()

        if categorias_view.image_uploader.local_upload_path:
            if categorias_view.image_uploader.send_to_bucket():
                # A URL da imagem já foi atualizada no handler, agora atualizamos o objeto do modelo
                prod_categoria.image_url = categorias_view.image_uploader.get_final_image_url()
            else:
                # A mensagem de erro já é exibida pelo handler
                save_btn.disabled = False
                return

        # Envia os dados para o backend, as exceptions foram tratadas no controller e result contém
        # o status da operação.
        result = category_controllers.handle_save(
            categoria=prod_categoria,
            current_user=get_current_user(page)
        )

        if result["status"] == "error":
            message_snackbar(
                page=page, message=result["message"], message_type=MessageType.ERROR)
            return

        # Limpa o formulário salvo e volta para a página anterior que a invocou
        categorias_view.clear_form()
        page.back() # type: ignore [attr-defined]

    def exit_form_categorias(e):
        categorias_view.image_uploader.cleanup_local_file()
        # Limpa o formulário sem salvar e volta para à página anterior que a invocou
        categorias_view.clear_form()
        page.back() # type: ignore [attr-defined]

    # Adiciona os botões "Salvar" & "Cancelar"
    save_btn = ft.ElevatedButton(
        text="Salvar", col={'xs': 5, 'md': 5, 'lg': 5}, on_click=save_form_categorias)
    exit_btn = ft.ElevatedButton(
        text="Cancelar", col={'xs': 5, 'md': 5, 'lg': 5}, on_click=exit_form_categorias)
    space_between = ft.Container(col={'xs': 2, 'md': 2, 'lg': 2})

    form_content = ft.Column(
        controls=[
            form_container,
            ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
            ft.Divider(height=10),
            ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
            ft.ResponsiveRow(
                columns=12,
                expand=True,
                spacing=10,
                run_spacing=10,
                controls=[save_btn, space_between, exit_btn],
                alignment=ft.MainAxisAlignment.END,
            ),
        ],
    )

    return ft.View(
        route='home/produtos/categorias/form',
        appbar=create_appbar_back(page=page,
            title=ft.Text(route_title, size=18, selectable=True)),
        controls=[form_content],
        scroll=ft.ScrollMode.AUTO,
        bgcolor=ft.Colors.BLACK,
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )
