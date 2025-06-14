import logging
import os
import base64
import mimetypes

from datetime import datetime, UTC, timedelta
from typing import Any

import flet as ft

from src.domains.empresas.controllers.empresas_controllers import handle_get_empresas
from src.domains.shared.nome_pessoa import NomePessoa
from src.domains.usuarios.models.usuario_subclass import UsuarioProfile
import src.shared.config.globals as app_globals

import src.controllers.bucket_controllers as bucket_controllers
import src.domains.usuarios.controllers.usuarios_controllers as user_controllers

from src.domains.usuarios.models import Usuario, UsuarioStatus
from src.pages.partials import build_input_field
from src.services import UploadFile
from src.shared.utils import  message_snackbar, get_uuid, gerar_senha, MessageType, ProgressiveMessage
from src.shared.utils.find_project_path import find_project_root
from src.shared.config import get_app_colors

logger = logging.getLogger(__name__)


class UsuarioForm:
    def __init__(self, page: ft.Page):
        self.page = page
        self.empresa_logada = page.app_state.empresa  # type: ignore [attr-defined]
        self.empresas = self._get_logged_user_companies()
        self.data = page.app_state.form_data  # type: ignore [attr-defined]
        # Foto do usuário
        self.photo_url: str | None = None
        self.is_photo_url_web = False
        self.previous_photo_url: str | None = None
        self.local_upload_file: str | None = None
        # Campos de redimencionamento do formulário
        self.font_size = 18
        self.icon_size = 24
        self.padding = 50
        self._usuario_id: str | None = None
        self.app_colors: dict[str, str] = get_app_colors('blue')

        if page.session.get("user_colors"):
            self.app_colors: dict[str, str] = page.session.get(
                "user_colors")  # type: ignore [attr-defined]     ! page.session é um objeto que contém o método .get(), não é um dict

        self.input_width = 400

        # Responsividade
        self._create_form_fields()
        self.empresas_selection = self._create_empresas_selection()
        self.form = self.build_form()
        self.page.on_resized = self._page_resize

    def _get_logged_user_companies(self) -> list:
        logged_user = self.page.app_state.usuario  # type: ignore [attr-defined]
        empresas = logged_user.get("empresas")
        if not empresas:
            return []

        result = handle_get_empresas(ids_empresas=empresas)

        if result["status"] == "error":
            return []

        return result["data"]["empresas"]


    def on_change_status(self, e):
        status = e.control
        status.label = "Usuário Ativo" if e.data == "true" else "Usuário Inativo"
        status.update()

    def _create_form_fields(self):
        """Cria os campos do formulário de Usuário"""
        #--------------------------------------------------------------------------------------
        # Primeiro Nome
        self.first_name = build_input_field(
            page_width=self.page.width,  # type: ignore [attr-defined]
            app_colors=self.app_colors,
            col={'xs': 12, 'md': 6, 'lg': 6},
            label="Nome",
            icon=ft.Icons.FIRST_PAGE,
        )
        # Último nome (sobrenome)
        self.last_name = build_input_field(
            page_width=self.page.width,  # type: ignore [attr-defined]
            app_colors=self.app_colors,
            col={'xs': 12, 'md': 6, 'lg': 6},
            label="Sobrenome",
            icon=ft.Icons.LAST_PAGE,
        )

        #------------------------------------------------------------------------------------------
        # Email do Usuario
        self.email = build_input_field(
            page_width=self.page.width,  # type: ignore [attr-defined]
            app_colors=self.app_colors,
            col={'xs': 12, 'md': 7, 'lg': 7},
            label="Email",
            keyboard_type=ft.KeyboardType.EMAIL,
            icon=ft.Icons.EMAIL_OUTLINED,
        )

        # Celular
        self.phone_number = build_input_field(
            page_width=self.page.width,  # type: ignore [attr-defined]
            app_colors=self.app_colors,
            col={'xs': 12, 'md': 5, 'lg': 5},
            label="Celular",
            hint_text="11987654321",
            capitalization=ft.TextCapitalization.SENTENCES,
            icon=ft.Icons.PHONE_ANDROID,
        )

        #--------------------------------------------------------------------------------------
        # Perfil/Permissões
        self.profile = ft.Dropdown(
            col={'xs': 12, 'md': 8, 'lg': 8},
            label="Perfil",
            text_size=16,
            expanded_insets=ft.padding.all(10),
            expand=True,
            expand_loose=True,
            options=[
                ft.dropdown.Option(key=profile.name, text=profile.value)
                for profile in UsuarioProfile
            ],
            enable_filter=True,
            hint_text="Selecione o perfil do usuário",
            tooltip='Selecione o perfil do usuário',
            filled=True,
            border=ft.InputBorder.OUTLINE,
            border_color=self.app_colors["primary"],
            width=self.input_width,  # type: ignore
        )

        # Switch Ativo/Inativo
        self.status = ft.Switch(
            col={'xs': 12, 'md': 4, 'lg': 4},
            label="Usuario Ativo",
            value=True,
            on_change=self.on_change_status,
        )

        # Imagem do Usuario -------------------------------------------------------------------------------
        def on_hover_image(e):
            color: str = self.app_colors["container"] if e.data == "true" else self.app_colors["primary"]
            icon_container = self.camera_icon.content
            image_container = self.image_frame
            icon_container.color = color  # type: ignore
            image_container.border = ft.border.all(color=color, width=1)
            icon_container.update()  # type: ignore
            image_container.update()

        self.image_frame = ft.Container(
            content=ft.Text(
                "Imagem do Usuario (opcional, mas desejada)", italic=True),
            bgcolor=ft.Colors.TRANSPARENT,
            padding=10,
            alignment=ft.alignment.center,
            width=350,
            height=250,
            border=ft.border.all(color=ft.Colors.GREY_400, width=1),
            border_radius=ft.border_radius.all(20),
            on_click=self._show_image_dialog,
            on_hover=on_hover_image,
            tooltip="Clique aqui para adicionar uma imagem do usuário",
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
            border_radius=ft.border_radius.all(100),
            padding=8,
        )

        self.image_section = ft.Column(
            col={'xs': 12, 'md': 4, 'lg': 4},
            controls=[self.image_frame, self.camera_icon],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0,
            width=1400,
        )

        self.empresas_selection = self._create_empresas_selection()

    async def _show_image_dialog(self, e) -> None:
        self.image_frame.border = ft.border.all(
            color=self.app_colors["primary"], width=1)
        self.image_frame.update()

        upload_file = UploadFile(
            page=self.page,
            title_dialog="Selecionar foto do Usuário",
            allowed_extensions=["png", "jpg", "jpeg", "svg"],
        )

        local_upload_file = await upload_file.open_dialog()

        # O arquivo ou URL do logo foi obtido. Não há erros.
        self.is_photo_url_web = upload_file.is_url_web
        self.photo_url = None

        if upload_file.is_url_web:
            # Obtem a url do arquivo para a imagem, atualiza a tela com a imagem do usuario e termina
            self.photo_url = upload_file.url_file
            self.local_upload_file = None

            usuario_img = ft.Image(
                src=self.photo_url,
                error_content=ft.Text("Erro!"),
                repeat=ft.ImageRepeat.NO_REPEAT,
                fit=ft.ImageFit.CONTAIN,
                border_radius=ft.border_radius.all(20),
            )
            self.image_frame.content = usuario_img
            self.image_section.update()
            return

        """
        O arquivo de Imagem do Usuario está salvo no diretório local do servidor em "uploads/"
        do projeto e está em self.local_upload_file.
        """
        if local_upload_file:
            self.local_upload_file = local_upload_file
            # Obtem o diretório raiz do projeto
            project_root = find_project_root(__file__)
            # O operador / é usado para concatenar partes de caminhos de forma segura e independente do sistema operacional.
            img_file = project_root / self.local_upload_file

            try:
                with open(img_file, "rb") as f_img:
                    img_data = f_img.read()

                base64_data = base64.b64encode(img_data).decode('utf-8')
                mime_type, _ = mimetypes.guess_type(str(img_file))
                if not mime_type:
                    # Tenta inferir pela extensão se mimetypes falhar
                    ext = str(img_file).split('.')[-1].lower()
                    if ext == "jpg" or ext == "jpeg":
                        mime_type = "image/jpeg"
                    elif ext == "png":
                        mime_type = "image/png"
                    elif ext == "svg":
                        mime_type = "image/svg+xml"
                    else:
                        mime_type = "application/octet-stream"  # Fallback genérico

                usuario_img = ft.Image(
                    src_base64=base64_data,
                    error_content=ft.Text("Erro ao carregar (base64)!"),
                    repeat=ft.ImageRepeat.NO_REPEAT,
                    fit=ft.ImageFit.CONTAIN,
                    border_radius=ft.border_radius.all(20),
                )
            except Exception as ex:
                logger.error(
                    f"Erro ao ler arquivo de imagem {img_file} para base64: {ex}")
                usuario_img = ft.Image(
                    error_content=ft.Text(
                        f"Erro crítico ao carregar imagem: {ex}"),
                )
            self.image_frame.content = usuario_img
            self.image_frame.update()

    def _create_empresas_selection(self):
        """Cria o componente de seleção múltipla de empresas"""
        self.empresas_checkboxes = []
        self.selected_empresas = set()  # Armazena IDs das empresas selecionadas

        if not self.empresas:
            # Caso não haja empresas disponíveis
            return ft.Container(
                col={'xs': 12, 'md': 12, 'lg': 12},
                content=ft.Text(
                    "Nenhuma empresa disponível para seleção",
                    italic=True,
                    color=ft.Colors.GREY_600,
                    size=14
                ),
                padding=10,
            )

        def on_empresa_change(e, empresa_id: str):
            """Callback para mudanças nos checkboxes das empresas"""
            if e.data == "true":
                self.selected_empresas.add(empresa_id)
            else:
                self.selected_empresas.discard(empresa_id)

            # Atualiza o texto do contador
            count_text = f"{len(self.selected_empresas)} de {len(self.empresas)} empresas selecionadas"
            self.empresas_counter.value = count_text
            self.empresas_counter.update()

        # Cria checkboxes para cada empresa
        checkbox_controls = []
        for empresa in self.empresas:
            empresa_id = empresa.id
            empresa_nome = empresa.trade_name or empresa.corporate_name

            checkbox = ft.Checkbox(
                label=empresa_nome,
                value=False,
                data=empresa_id,  # Armazena o ID da empresa no data
                on_change=lambda e, eid=empresa_id: on_empresa_change(e, eid),
                label_style=ft.TextStyle(size=14),
            )

            self.empresas_checkboxes.append(checkbox)
            checkbox_controls.append(checkbox)

        # Contador de empresas selecionadas
        self.empresas_counter = ft.Text(
            f"0 de {len(self.empresas)} empresas selecionadas",
            size=12,
            color=self.app_colors["primary"],
            weight=ft.FontWeight.W_500,
        )

        # Botões de ação rápida
        def select_all_empresas(e):
            """Seleciona todas as empresas"""
            for checkbox in self.empresas_checkboxes:
                checkbox.value = True
                self.selected_empresas.add(checkbox.data)

            self.empresas_counter.value = f"{len(self.empresas)} de {len(self.empresas)} empresas selecionadas"
            self._update_empresas_section()

        def deselect_all_empresas(e):
            """Deseleciona todas as empresas"""
            for checkbox in self.empresas_checkboxes:
                checkbox.value = False

            self.selected_empresas.clear()
            self.empresas_counter.value = f"0 de {len(self.empresas)} empresas selecionadas"
            self._update_empresas_section()

        action_buttons = ft.Row(
            controls=[
                ft.TextButton(
                    text="Selecionar Todas",
                    icon=ft.Icons.SELECT_ALL,
                    on_click=select_all_empresas,
                    style=ft.ButtonStyle(
                        color=self.app_colors["primary"],
                        text_style=ft.TextStyle(size=12)
                    )
                ),
                ft.TextButton(
                    text="Limpar Seleção",
                    icon=ft.Icons.CLEAR_ALL,
                    on_click=deselect_all_empresas,
                    style=ft.ButtonStyle(
                        color=ft.Colors.GREY_600,
                        text_style=ft.TextStyle(size=12)
                    )
                ),
            ],
            spacing=10,
        )

        # Container scrollável para os checkboxes
        empresas_list = ft.Container(
            content=ft.Column(
                controls=checkbox_controls,
                spacing=8,
                scroll=ft.ScrollMode.AUTO,
            ),
            height=min(200, len(self.empresas) * 40 + 20),  # Altura dinâmica até 200px
            border=ft.border.all(color=ft.Colors.GREY_300, width=1),
            border_radius=ft.border_radius.all(8),
            padding=10,
        )

        # Container principal do componente
        self.empresas_section = ft.Container(
            col={'xs': 12, 'md': 12, 'lg': 12},
            content=ft.Column(
                controls=[
                    ft.Text(
                        "Empresas Vinculadas",
                        size=16,
                        weight=ft.FontWeight.W_500,
                        color=self.app_colors["primary"]
                    ),
                    ft.Text(
                        "Selecione as empresas que este usuário terá acesso:",
                        size=12,
                        color=ft.Colors.GREY_600,
                        italic=True
                    ),
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    action_buttons,
                    self.empresas_counter,
                    ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
                    empresas_list,
                ],
                spacing=5,
            ),
            padding=15,
            border_radius=ft.border_radius.all(12),
            bgcolor=ft.Colors.with_opacity(0.05, self.app_colors["primary"]),
            border=ft.border.all(color=ft.Colors.with_opacity(0.2, self.app_colors["primary"]), width=1),
        )

        return self.empresas_section

    def _update_empresas_section(self):
        """Atualiza a seção de empresas"""
        if self.empresas_counter.page:  # Verifica se o controle está na página
            self.empresas_counter.update()
        for checkbox in self.empresas_checkboxes:
            if checkbox.page:  # Verifica se o controle está na página
                checkbox.update()

    def build_form(self) -> ft.Container:
        """Constrói o formulário de Categoria de Usuarios"""
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
                ft.Text("Identificação do Usuario", size=16),
                ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
                responsive_row(
                    controls=[
                        self.image_section,
                        ft.Column(
                            controls=[
                                ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
                                responsive_row(controls=[self.first_name, self.last_name]),
                                ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
                                responsive_row(controls=[self.email, self.phone_number]),
                                ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
                                responsive_row(controls=[self.profile, self.status]),
                            ],
                            col={'xs': 12, 'md': 8, 'lg': 8},
                        ),
                    ]
                ),
                ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                ft.Text("Vinculação com Empresas", size=16),
                ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
                responsive_row(controls=[self.empresas_selection]),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.START,
            spacing=5,
            alignment=ft.MainAxisAlignment.SPACE_EVENLY,
        )

        return ft.Container(
            content=build_content,
            padding=self.padding,
            bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
            border_radius=ft.border_radius.all(20),
        )

    def get_selected_empresas_ids(self) -> list[str]:
        """Retorna a lista de IDs das empresas selecionadas"""
        return list(self.selected_empresas)

    def set_selected_empresas(self, empresa_ids: list[str] | set[str]):
        """Define as empresas selecionadas programaticamente"""
        if not self.empresas_checkboxes:
            return

        self.selected_empresas = set(empresa_ids)

        for checkbox in self.empresas_checkboxes:
            checkbox.value = checkbox.data in empresa_ids

        self.empresas_counter.value = f"{len(self.selected_empresas)} de {len(self.empresas)} empresas selecionadas"
        self._update_empresas_section()

    def did_mount(self):
        if self.data and self.data.get('id'):
            # Preenche os campos com os dados fiscais da empresa
            self.populate_form_fields()
        self.page.update()

    def populate_form_fields(self):
        """Preenche os campos do formulário com os dados do usuario"""
        user_name = self.data["name"]
        self.first_name.value = user_name.first_name if user_name.first_name else ""
        self.last_name.value = user_name.last_name if user_name.last_name else ""
        self.email.value = self.data["email"]
        self.phone_number.value = self.data.get("phone_number", "")
        self.profile.value = self.data["profile"]

        status = self.data.get("status", "ACTIVE")

        if status == "ACTIVE":
            self.status.value = True
            self.status.label = "Usuário Ativo"
        else:
            self.status.value = False
            self.status.label = "Usuário Inativo"

        if self.data.get("photo_url"):
            # vars, não são fields do formulário
            self.photo_url = self.data["photo_url"]
            self.previous_photo_url = self.data["photo_url"]

            # Monta a imagem e associa ao campo do formulário
            usuario_img = ft.Image(
                src=self.photo_url,
                error_content=ft.Text("Erro!"),
                repeat=ft.ImageRepeat.NO_REPEAT,
                fit=ft.ImageFit.CONTAIN,
                border_radius=ft.border_radius.all(20),
            )
            self.image_frame.content = usuario_img
        else:
            self.photo_url = None
            self.previous_photo_url = None

        if empresas_usuario := self.data.get("empresas"):
            if isinstance(empresas_usuario, list) or isinstance(empresas_usuario, set):
                self.set_selected_empresas(empresas_usuario)

    def get_form_object_updated(self) -> Usuario:
        """Atualiza self.data com os dados do formulário e o retorna atualizado."""
        user_name = NomePessoa(first_name=self.first_name.value, last_name=self.last_name.value)

        self.data['name'] = user_name
        self.data["email"] = self.email.value
        self.data["phone_number"] = self.phone_number.value
        self.data["profile"] = UsuarioProfile[self.profile.value] if self.profile.value else UsuarioProfile.ADMIN
        self.data["empresas"] = self.get_selected_empresas_ids()
        self.data['status'] = UsuarioStatus.ACTIVE if self.status.value else UsuarioStatus.INACTIVE
        self.data['photo_url'] = self.photo_url

        if not self.data.get("password"):
            self.data["password"] = gerar_senha()
            self.data["temp_password"] = True

        return Usuario.from_dict(self.data)

    def validate_form(self) -> str | None:
        """Valida os campos do formulário. Retorna uma mensagem de erro se algum campo obrigatório não estiver preenchido."""
        if not self.first_name.value:
            return "Por favor, preencha o nome do usuário."
        if not self.email.value:
            return "Por favor, preencha o email do usuário."
        if not self.phone_number.value:
            return "Por favor, preencha o telefone do usuário."
        if not self.profile.value:
            return "Por favor,  selecione o perfil do usuário."
        if len(self.selected_empresas) == 0:
            return "Por favor, selecione pelo menos uma empresa para o usuário."

        return None

    def _page_resize(self, e):
        if self.page.width < 600:  # type: ignore
            self.font_size = 14
            self.icon_size = 16
            self.padding = 20
            self.input_width = 280
        elif self.page.width < 1024:  # type: ignore
            self.font_size = 16
            self.icon_size = 20
            self.padding = 40
            self.input_width = 350
        else:
            self.font_size = 18
            self.icon_size = 24
            self.padding = 50
            self.input_width = 400

        # Atualiza os tamanhos dos campos do formulário
        self.first_name.text_size = self.font_size
        self.last_name.text_size = self.font_size
        self.email.text_size = self.font_size
        self.phone_number.text_size = self.font_size
        self.profile.text_size = self.font_size

        # Atualiza o padding do container
        self.form.padding = self.padding
        self.form.update()

    def send_to_bucket(self):
        # Faz o upload do arquivo de imagem do usuário para o bucket
        if not self.local_upload_file:
            # Não há arquivo local para enviar
            return False

        file_uid = get_uuid()   # Obtem um UUID único para o arquivo
        _, dot_extension = os.path.splitext(self.local_upload_file)
        # Padroniza a extensão para caracteres minúsculos
        dot_extension = dot_extension.lower()
        file_name = f"img_{file_uid}{dot_extension}"

        prefix = "usuarios"

        # A lógica aqui depende do Bucket utilizado, neste caso usamos o S3 da AWS, usamos o CNPJ ou user_id como diretório no bucket.
        file_name_bucket = f"{prefix}/{file_name}"

        try:
            self.photo_url = bucket_controllers.handle_upload_bucket(
                local_path=self.local_upload_file, key=file_name_bucket)

            if self.photo_url:
                # Atualiza logo na tela
                usuario_img = ft.Image(
                    src=self.photo_url,
                    error_content=ft.Text("Erro!"),
                    repeat=ft.ImageRepeat.NO_REPEAT,
                    fit=ft.ImageFit.CONTAIN,
                    border_radius=ft.border_radius.all(20),
                )
                self.image_frame.content = usuario_img
                self.image_frame.update()
                return True

            # A Imagem não é válida, URL não foi gerada, mantém a imagem anterior se houver
            if self.previous_photo_url:
                self.photo_url = self.previous_photo_url

            message_snackbar(
                page=self.page, message="Não foi possível carregar imagem do usuário de usuarios!", message_type=MessageType.ERROR)

            return False
        except ValueError as e:
            msg = f"Erro de validação ao carregar imagem: {str(e)}"
            message_snackbar(page=self.page, message=msg,
                             message_type=MessageType.ERROR)
            logger.error(msg)
        except RuntimeError as e:
            msg = f"Erro ao carregar imagem: {str(e)}"
            message_snackbar(page=self.page, message=msg,
                             message_type=MessageType.ERROR)
            logger.error(msg)
        finally:
            # Independente de sucesso, remove o arquivo de imagem do diretório local uploads/
            try:
                os.remove(self.local_upload_file)
            except:
                pass  # Ignora erros na limpeza do arquivo

    def build(self) -> ft.Container:
        return self.form

    def clear_form(self):
        """Limpa os campos do formulário"""
        for field in self.__dict__.values():
            if isinstance(field, (ft.TextField, ft.Dropdown)):
                field.value = ''
            if isinstance(field, (ft.Switch)):
                field.value = True  # Por default, a categoria sempre é ativa

        self.selected_empresas.clear()
        if hasattr(self, 'empresas_checkboxes'):
            for checkbox in self.empresas_checkboxes:
                checkbox.value = False
            if hasattr(self, 'empresas_counter'):
                self.empresas_counter.value = f"0 de {len(self.empresas)} empresas selecionadas"
        # Limpa o buffer com os dados de categorias carregados
        self.data = {}

# Rota: /home/usuarios/form


def show_user_form(page: ft.Page):
    """Página de cadastro de usuarios."""
    route_title = "home/usuarios/form"
    usuario_data = page.app_state.form_data  # type: ignore

    if id := usuario_data.get("id"):
        route_title += f"/{id}"
    else:
        route_title += "/new"

    def handle_icon_hover(e):
        """Muda o bgcolor do container no hover."""
        e.control.bgcolor = ft.Colors.with_opacity(
            0.1, ft.Colors.WHITE) if e.data == "true" else ft.Colors.TRANSPARENT
        e.control.update()

    appbar = ft.AppBar(
        leading=ft.Container(
            alignment=ft.alignment.center_left,
            padding=ft.padding.only(left=10),
            content=ft.Container(
                width=40,
                height=40,
                border_radius=ft.border_radius.all(100),
                # Aplica ink ao wrapper (ao clicar da um feedback visual para o usuário)
                ink=True,
                bgcolor=ft.Colors.TRANSPARENT,
                alignment=ft.alignment.center,
                on_hover=handle_icon_hover,
                content=ft.Icon(ft.Icons.ARROW_BACK),
                on_click=lambda _: page.go(
                    page.data if page.data else '/home'),
                tooltip="Voltar",
                # Ajuda a garantir que o hover respeite o border_radius
                clip_behavior=ft.ClipBehavior.ANTI_ALIAS
            ),
        ),
        title=ft.Text(route_title, size=18, selectable=True),
        bgcolor=ft.Colors.with_opacity(0.9, ft.Colors.PRIMARY_CONTAINER),
        adaptive=True,
    )

    usuarios_view = UsuarioForm(page=page)
    usuarios_view.did_mount()
    form_container = usuarios_view.build()

    def save_form_usuarios(e):
        # Valida os dados do formulário
        if msg := usuarios_view.validate_form():
            message_snackbar(
                page=page, message=msg, message_type=MessageType.WARNING)
            return

        # Desabilita o botão de salvar para evitar múltiplos cliques
        save_btn.disabled = True

        # Cria o gerenciador de mensagens progressivas
        progress_msg = ProgressiveMessage(page)

        try:
            # Primeira etapa: Salvando usuário
            progress_msg.show_progress("Salvando usuário...")

            # Instância do objeto Usuario com os dados do formulário para enviar para o backend
            usuario: Usuario = usuarios_view.get_form_object_updated()

            if not usuarios_view.is_photo_url_web and usuarios_view.local_upload_file:
                # Atualiza mensagem para upload da imagem
                progress_msg.update_progress("Enviando imagem para o servidor...")

                # Envia o arquivo de imagem para o bucket
                if usuarios_view.send_to_bucket():
                    usuario.photo_url = usuarios_view.photo_url
                else:
                    progress_msg.show_error("Erro ao enviar imagem para o bucket")
                    save_btn.disabled = False
                    return

                # Apaga arquivo do servidor local
                try:
                    os.remove(usuarios_view.local_upload_file)
                except:
                    pass  # Ignora erros na limpeza do arquivo
                usuarios_view.local_upload_file = None

            # Segunda etapa: Salvando no banco
            progress_msg.update_progress("Finalizando cadastro...")

            # Envia os dados para o backend
            result = user_controllers.handle_save(usuario=usuario)

            if result["status"] == "error":
                progress_msg.show_error(result["message"])
                save_btn.disabled = False
                return

            if usuario.temp_password:
                # Terceira etapa: Enviando email
                progress_msg.update_progress(f"Enviando credenciais para {usuario.email}...")

                print(f"Enviando email/credenciais para {usuario.email}...")
                # Envia email para usuário com senha temporária
                result = user_controllers.send_mail_password(usuario=usuario)

                # Mensagem final de sucesso
                if result.get("success") is True: # Verifica a chave "success"
                    # Mensagem de sucesso principal já inclui o status do email
                    progress_msg.show_success(result.get("message", f"Usuário salvo e email enviado para {usuario.email}!"))
                else:
                    # Houve sucesso no salvamento do usuário, mas o envio do email falhou.
                    # A mensagem de erro do email já está em result['user_message'] ou result['error']
                    error_message = result.get("user_message", result.get("error", "Falha no envio do email."))
                    progress_msg.show_warning(f"Usuário salvo com sucesso, mas: {error_message}")
                # Limpa o formulário salvo e volta para a página anterior que a invocou

            usuarios_view.clear_form()
            page.app_state.clear_form_data() # type: ignore [attr-defined]
            page.go(page.data if page.data else '/home')

        except Exception as ex:
            # Em caso de erro inesperado
            progress_msg.show_error(f"Erro inesperado: {str(ex)}")
            save_btn.disabled = False
        finally:
            # Sempre reabilita o botão após um tempo
            def renable_button():
                save_btn.disabled = False
                page.update()

            # Reagenda reabilitação do botão após 3 segundos
            import threading
            timer = threading.Timer(3.0, renable_button)
            timer.start()


    def exit_form_usuarios(e):
        if not usuarios_view.is_photo_url_web and usuarios_view.local_upload_file:
            try:
                os.remove(usuarios_view.local_upload_file)
            except:
                pass  # Ignora erros na limpeza do arquivo
            usuarios_view.local_upload_file = None

        # Limpa o formulário sem salvar e volta para à página anterior que a invocou
        usuarios_view.clear_form()
        page.app_state.clear_form_data()  # type: ignore
        page.go(page.data if page.data else '/home')

    # Adiciona os botões "Salvar" & "Cancelar"
    save_btn = ft.ElevatedButton(
        text="Salvar", col={'xs': 5, 'md': 5, 'lg': 5}, on_click=save_form_usuarios)
    exit_btn = ft.ElevatedButton(
        text="Cancelar", col={'xs': 5, 'md': 5, 'lg': 5}, on_click=exit_form_usuarios)
    space_between = ft.Container(col={'xs': 2, 'md': 2, 'lg': 2})
    return ft.Column(
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
        data=appbar,
    )
