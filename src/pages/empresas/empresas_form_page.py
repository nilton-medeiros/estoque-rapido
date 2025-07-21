import logging
import os
import base64
import mimetypes

# import asyncio

from enum import Enum  # Certifique-se de importar o módulo 'Enum'

from typing import Optional

import src.controllers.bucket_controllers as bucket_controllers
import src.domains.empresas.controllers.empresas_controllers as company_controllers
from src.domains.shared.context.session import get_current_user, get_session_colors
import src.domains.usuarios.controllers.usuarios_controllers as user_controllers
from src.pages.partials.app_bars.appbar import create_appbar_back
import src.shared.utils.tools as tools

from src.domains.empresas.models.cnpj import CNPJ
from src.domains.empresas import EmpresaSize
from src.domains.empresas.models.empresas_model import Empresa

from src.pages.partials import build_input_field
from src.shared.utils import validate_email, get_uuid, MessageType, message_snackbar
from src.shared.utils.find_project_path import find_project_root

from src.services import UploadFile, consult_cnpj_api

import flet as ft

logger = logging.getLogger(__name__)


class EmpresaView:
    def __init__(self, page: ft.Page):
        self.page = page
        self.data = page.app_state.form_data # type: ignore
        # Vars propiedades
        self.logo_url: str|None = None
        self.is_logo_url_web = False
        self.previous_logo_url: str|None = None
        self.local_upload_file: str|None = None
        self.initials_corporate_name = "Logo"
        self.font_size = 18
        self.icon_size = 24
        self.padding = 50
        self.app_colors = get_session_colors(page)
        self._empresa_id = None

        # Responsividade
        self._create_form_fields()
        self.form = self.build_form()
        self.page.on_resized = self._page_resize


    def _create_form_fields(self):
        """Cria os campos do formulário Principal"""

        # Por causa do on_change do self.cnpj, não funciona se usar a função build_input_field
        # para criar o campo CNPJ
        # Adiciona o campo CNPJ e o botão de consulta

        self.cnpj = ft.TextField(
            col={'xs': 10, 'md': 10, 'lg': 3},
            label="CNPJ",
            prefix=ft.Container(
                content=ft.Icon(
                    name=ft.Icons.WARNING,
                    color=self.app_colors['accent'],
                    size=self.icon_size,
                ),
                padding=ft.padding.only(right=10),
            ),
            text_size=self.font_size,
            border_color=self.app_colors["primary"],
            focused_border_color=self.app_colors["container"],
            text_align=ft.TextAlign.LEFT,
            bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
            label_style=ft.TextStyle(
                color=self.app_colors["primary"],  # Cor do label igual à borda # type: ignore
                weight=ft.FontWeight.W_500  # Label um pouco mais grosso
            ),
            hint_style=ft.TextStyle(
                color=ft.Colors.GREY_500,  # Cor do placeholder mais visível
                weight=ft.FontWeight.W_300  # Placeholder um pouco mais fino
            ),
            # Duração do fade do placeholder
            cursor_color=self.app_colors["primary"],
            focused_color=ft.Colors.GREY_500,
            text_style=ft.TextStyle(                        # Estilo do texto digitado
                color=ft.Colors.WHITE,
                weight=ft.FontWeight.W_400
            ),
            on_change=self._handle_cnpj_change,
        )

        self.consult_cnpj_button = ft.IconButton(
            col={'xs': 2, 'md': 2, 'lg': 1},
            icon=ft.Icons.SEARCH,
            icon_size=self.icon_size,
            # selected_icon_color=self.app_colors["container"],
            tooltip="Consultar CNPJ",
            # hover_color=self.app_colors["container"],
            disabled=True,
            on_click=self._consult_cnpj
        )

        # Razão Social
        self.corporate_name = build_input_field(
            page_width=self.page.width, # type: ignore
            app_colors=self.app_colors,
            col={'xs': 12, 'md': 12, 'lg': 8},
            label="Razão Social",
            icon=ft.Icons.CORPORATE_FARE,
        )
        # Nome Fantasia
        self.trade_name = build_input_field(
            page_width=self.page.width, # type: ignore
            app_colors=self.app_colors,
            col={'xs': 12, 'md': 6, 'lg': 4},
            label="Nome Fantasia",
            icon=ft.Icons.STORE,
        )
        # Nome da loja
        self.store_name = build_input_field(
            page_width=self.page.width, # type: ignore
            app_colors=self.app_colors,
            col={'xs': 12, 'md': 6, 'lg': 4},
            label="Nome da Loja",
            icon=ft.Icons.STORE_MALL_DIRECTORY,
            hint_text="Ex.: Loja Moema",
            hint_fade_duration=5,
        )

        self.ie = build_input_field(
            page_width=self.page.width, # type: ignore
            app_colors=self.app_colors,
            col={'xs': 12, 'md': 6, 'lg': 2},
            label="Inscrição Estadual",
            icon=ft.Icons.REAL_ESTATE_AGENT,
        )
        self.im = build_input_field(
            page_width=self.page.width, # type: ignore
            app_colors=self.app_colors,
            col={'xs': 12, 'md': 6, 'lg': 2},
            label="Inscrição Municipal",
            icon=ft.Icons.REAL_ESTATE_AGENT,
        )

        # Informações de Contato
        self.email = build_input_field(
            page_width=self.page.width, # type: ignore
            app_colors=self.app_colors,
            col={'xs': 12, 'md': 8, 'lg': 6},
            label="Email",
            icon=ft.Icons.EMAIL,
            keyboard_type=ft.KeyboardType.EMAIL,
        )
        self.phone = build_input_field(
            page_width=self.page.width, # type: ignore
            app_colors=self.app_colors,
            col={'xs': 12, 'md': 4, 'lg': 6},
            label="Telefone",
            icon=ft.Icons.PHONE,
            keyboard_type=ft.KeyboardType.PHONE,
            hint_text="(11) 99999-9999",
            hint_fade_duration=5,
        )

        # Endereço
        self.street = build_input_field(
            page_width=self.page.width, # type: ignore
            app_colors=self.app_colors,
            col={'xs': 12, 'md': 12, 'lg': 6},
            label="Rua",
            icon=ft.Icons.LOCATION_ON,
        )
        self.number = build_input_field(
            page_width=self.page.width, # type: ignore
            app_colors=self.app_colors,
            col={'xs': 12, 'md': 6, 'lg': 2},
            label="Número",
            icon=ft.Icons.NUMBERS,
        )
        self.complement = build_input_field(
            page_width=self.page.width, # type: ignore
            app_colors=self.app_colors,
            col={'xs': 12, 'md': 6, 'lg': 4},
            label="Complemento",
            icon=ft.Icons.ADD_LOCATION,
            hint_text="Apto 101",
            hint_fade_duration=5,
        )
        self.neighborhood = build_input_field(
            page_width=self.page.width, # type: ignore
            app_colors=self.app_colors,
            col={'xs': 12, 'md': 6, 'lg': 5},
            label="Bairro",
            icon=ft.Icons.LOCATION_CITY,
        )
        self.city = build_input_field(
            page_width=self.page.width, # type: ignore
            app_colors=self.app_colors,
            col={'xs': 12, 'md': 6, 'lg': 4},
            label="Cidade",
            icon=ft.Icons.LOCATION_CITY,
            hint_text="São Paulo",
            hint_fade_duration=5,
        )
        self.state = build_input_field(
            page_width=self.page.width, # type: ignore
            app_colors=self.app_colors,
            col={'xs': 12, 'md': 2, 'lg': 3},
            label="Estado",
            icon=ft.Icons.LOCATION_CITY,
            hint_text="SP",
            hint_fade_duration=5,
            keyboard_type=ft.KeyboardType.TEXT,
            max_length=2,
        )
        self.postal_code = build_input_field(
            page_width=self.page.width, # type: ignore
            app_colors=self.app_colors,
            col={'xs': 12, 'md': 10, 'lg': 12},
            label="CEP",
            icon=ft.Icons.LOCATION_CITY,
            hint_text="00000-000",
            hint_fade_duration=5,
        )

        # Porte da Empresa. Campo oculto ao usuário neste momento, auto preenchido pela consulta ao CNPJ
        self.size_cia = ft.Dropdown(
            col={'xs': 12, 'md': 8, 'lg': 5},
            label="Porte da Empresa",
            width=400,
            options=[
                ft.dropdown.Option(key=size.name, text=size.value)
                for size in EmpresaSize
            ],
        )

        def on_hover_logo(e):
            color:str = self.app_colors["container"] if e.data == "true" else self.app_colors["primary"]
            icon_container = self.camera_icon.content
            logo_container = self.logo_frame
            icon_container.color = color # type: ignore
            logo_container.border = ft.border.all(color=color, width=1)
            icon_container.update() # type: ignore
            logo_container.update()

        self.logo_frame = ft.Container(
            content=ft.Text("Logo", italic=True),
            bgcolor=ft.Colors.TRANSPARENT,
            padding=10,
            alignment=ft.alignment.center,
            width=350,
            height=250,
            border=ft.border.all(color=ft.Colors.GREY_400, width=1),
            border_radius=ft.border_radius.all(20),
            on_click=self._show_logo_dialog,  # Também
            on_hover=on_hover_logo,
            disabled=self.consult_cnpj_button.disabled,
        )
        # Campo Logo do emitente de NFCe
        self.camera_icon = ft.Container(
            content=ft.Icon(
                name=ft.Icons.ADD_A_PHOTO_OUTLINED,
                size=20,
                color=ft.Colors.GREY_400,  # Cor padrão quando disabled
            ),
            margin=ft.margin.only(top=-5),
            ink=True,
            on_hover=on_hover_logo,
            on_click=self._show_logo_dialog,
            border_radius=ft.border_radius.all(100),
            padding=8,
            disabled=self.consult_cnpj_button.disabled,
        )

        self.logo_section = ft.Column(
            controls=[self.logo_frame, self.camera_icon],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0,
        )


    async def _show_logo_dialog(self, e) -> None:
        cnpj_clean = ''.join(filter(str.isdigit, self.cnpj.value)) # type: ignore
        if len(cnpj_clean) < 14:
            message_snackbar(
                page=self.page, message="Preencha corretamente o CNPJ da empresa", message_type=MessageType.WARNING)
            return

        self.logo_frame.border = ft.border.all(
            color=self.app_colors["primary"], width=1)
        self.logo_frame.update()

        upload_file = UploadFile(
            page=self.page,
            title_dialog="Selecionar imagem do Logo",
            allowed_extensions=["png", "jpg", "jpeg", "svg"],
        )

        local_upload_file = await upload_file.open_dialog()

        # O arquivo ou URL do logo foi obtido. Não há erros.
        self.is_logo_url_web = upload_file.is_url_web
        self.logo_url = None

        corp_name: str = self.corporate_name.value if self.corporate_name.value else ''
        if corporate_name := corp_name.strip():
            self.initials_corporate_name = tools.initials(corporate_name)

        if upload_file.is_url_web:
            # Obtem a url do arquivo para o logo, atualiza a tela com o logo e termina
            self.logo_url = upload_file.url_file
            self.local_upload_file = None

            logo_img = ft.Image(
                src=self.logo_url,
                error_content=ft.Text(self.initials_corporate_name),
                repeat=ft.ImageRepeat.NO_REPEAT,
                fit=ft.ImageFit.CONTAIN,
                border_radius=ft.border_radius.all(20),
            )
            self.logo_frame.content = logo_img
            self.logo_section.update()
            message_snackbar(
                page=self.page, message="Logo carregado com sucesso!", duration=3000)
            return

        """
        O arquivo Logo está salvo no diretório local do servidor em "uploads/"
        do projeto e está em self.local_upload_file.
        """
        if local_upload_file:
            self.local_upload_file = local_upload_file
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
                        mime_type = "application/octet-stream" # Fallback genérico

                logo_img = ft.Image(
                    src_base64=base64_data,
                    error_content=ft.Text("Erro ao carregar (base64)!"),
                    repeat=ft.ImageRepeat.NO_REPEAT,
                    fit=ft.ImageFit.CONTAIN,
                    border_radius=ft.border_radius.all(20),
                )
            except Exception as ex:
                logger.error(f"Erro ao ler arquivo de imagem {img_file} para base64: {ex}")
                logo_img = ft.Image(
                    error_content=ft.Text(f"Erro crítico ao carregar imagem: {ex}"),
                )
            self.logo_frame.content = logo_img
            self.logo_frame.update()


    def _handle_cnpj_change(self, e = None):
        """Atualiza o estado do botão de consulta baseado no valor do CNPJ"""
        cnpj_clean = ''.join(filter(str.isdigit, self.cnpj.value)) # type: ignore
        cnpj_button = self.consult_cnpj_button
        logo_container = self.logo_frame
        icon_container = self.camera_icon

        if len(cnpj_clean) < 14:
            self.cnpj.prefix.content.name = ft.Icons.WARNING # type: ignore
            cnpj_button.disabled = True
            logo_container.disabled = True
            icon_container.disabled = True
            logo_container.border = ft.border.all(
                color=ft.Colors.GREY_400, width=1)
            icon_container.content.color = ft.Colors.GREY_400 # type: ignore
        elif len(cnpj_clean) == 14:
            # CNPJ válido, ativa o botão de consulta ao dados da empresa pelo CNPJ
            self.cnpj.value = cnpj_clean
            self.cnpj.prefix.content.name = ft.Icons.CHECK_CIRCLE # type: ignore
            cnpj_button.disabled = False
            logo_container.disabled = False
            icon_container.disabled = False
            logo_container.border = ft.border.all(
                color=self.app_colors["primary"], width=1)
            icon_container.content.color = self.app_colors["primary"] # type: ignore
        if e:
            e.control.update()
            cnpj_button.update()
            logo_container.update()
            icon_container.update()

    async def _consult_cnpj(self, e):
        """Consulta o CNPJ na API da Receita"""
        try:
            # Mostra loading no botão
            self.consult_cnpj_button.icon = ft.Icons.PENDING
            self.consult_cnpj_button.disabled = True
            self.consult_cnpj_button.update()

            result = await consult_cnpj_api(self.cnpj.value)

            if result['is_error']:
                # Mostra erro
                message_snackbar(
                    page=self.page,
                    message="Erro ao consultar CNPJ. Verifique o número e tente novamente.",
                    message_type=MessageType.ERROR
                )
                return

            data = result['data']
            response = result['response']

            if response.status in (200, 304):
                # Preenche os campos com os dados retornados
                self.trade_name.value = data.get('nome_fantasia', '')
                self.corporate_name.value = data.get('razao_social', '')
                self.phone.value = data.get('ddd_telefone_1', '')

                # Endereço
                self.street.value = data.get('logradouro', '')
                self.number.value = data.get('numero', '')
                self.complement.value = data.get('complemento', '')
                self.neighborhood.value = data.get('bairro', '')
                self.city.value = data.get('municipio', '')
                self.state.value = data.get('uf', '')
                self.postal_code.value = data.get('cep', '')

                # Fiscal
                porte = data.get('codigo_porte', 0)

                match porte:
                    case 1:
                        self.size_cia.value = EmpresaSize.MICRO # type: ignore
                    case 3:
                        self.size_cia.value = EmpresaSize.SMALL # type: ignore
                    case 5:
                        self.size_cia.value = EmpresaSize.OTHER # type: ignore

                # Mostra mensagem de sucesso
                message_snackbar(
                    page=self.page, message="Dados do CNPJ carregados com sucesso!", message_type=MessageType.SUCCESS)
            elif response.status == 400:
                message_snackbar(
                    page=self.page,
                    message=f"Erro ao consultar CNPJ: CNPJ inválido",
                    message_type=MessageType.WARNING
                )
            else:
                # Mostra erro
                message_snackbar(
                    page=self.page,
                    message=f"Erro ao consultar CNPJ. Status: {response.status}",
                    message_type=MessageType.ERROR
                )
                logger.error(
                    f"Erro ao consultar CNPJ: {response.status} - {response.reason}")

        except Exception as error:
            # Mostra erro genérico
            logger.error(str(error))
            message_snackbar(
                page=self.page,
                message=str(error),
                message_type=MessageType.ERROR
            )

        finally:
            # Restaura o botão
            self.consult_cnpj_button.icon = ft.Icons.SEARCH
            self.consult_cnpj_button.disabled = not bool(self.cnpj.value)
            self.consult_cnpj_button.update()


    def build_form(self) -> ft.Container:
        """Constrói o formulário de cadastro de empresa"""
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
                ft.Text("Dados da Empresa", size=16),
                ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
                responsive_row(
                    controls=[self.cnpj, self.consult_cnpj_button, self.corporate_name]),
                ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
                responsive_row(
                    controls=[self.trade_name, self.store_name, self.ie, self.im]),
                ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
                responsive_row(controls=[self.email, self.phone]),
                ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
                ft.Divider(height=5),
                ft.Text("Endereço", size=16),
                responsive_row(
                    controls=[self.street, self.number, self.complement]),
                ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
                responsive_row(
                    controls=[self.neighborhood, self.city, self.state, self.postal_code]),
                ft.Divider(height=5),
                ft.Text("Logo da Empresa", size=16),
                ft.Row(col=12, alignment=ft.MainAxisAlignment.CENTER,
                       controls=[self.logo_section]),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.START,
            spacing=10
        )

        return ft.Container(
            content=build_content,
            padding=self.padding,
            bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
            border_radius=ft.border_radius.all(10),
        )


    def did_mount(self):
        if self.data and self.data.get('id'):
            # Preenche os campos com os dados da empresa
            self.populate_form_fields()
        self.page.update()


    def populate_form_fields(self):
        """Preenche os campos do formulário com os dados da empresa"""
        if cnpj := self.data.get('cnpj'):
            self.cnpj.value = cnpj.raw_cnpj
        else:
            self.cnpj.value = ''

        self._handle_cnpj_change()

        self.corporate_name.value = self.data.get('corporate_name', '')
        self.trade_name.value = self.data.get('trade_name', '')
        self.store_name.value = self.data.get('store_name', '')
        self.ie.value = self.data.get('ie', '')
        self.im.value = self.data.get('im', '')
        self.email.value = self.data.get('email', '')

        if phone := self.data.get('phone'):
            self.phone.value = str(phone)
        else:
            self.phone.value = ''

        # Dicionário de endereço
        address = self.data.get('address')
        if address:
            self.street.value = address.get('street', '')
            self.number.value = address.get('number', '')
            self.complement.value = address.get('complement', '')
            self.neighborhood.value = address.get('neighborhood', '')
            self.city.value = address.get('city', '')
            self.state.value = address.get('state', '')
            self.postal_code.value = address.get('postal_code', '')


        if size_enum := self.data.get('size'):
            self.size_cia.value = size_enum
        else:
            self.size_cia.value = ''

        if self.data.get('logo_url'):
            # Vars, não é um field do formulário
            self.logo_url = self.data.get('logo_url')
            self.previous_logo_url = self.data.get('logo_url')

            logo_img = ft.Image(
                src=self.logo_url,
                error_content=ft.Text("Logo"),
                repeat=ft.ImageRepeat.NO_REPEAT,
                fit=ft.ImageFit.CONTAIN,
                border_radius=ft.border_radius.all(20),
            )
            self.logo_frame.content = logo_img
        else:
            self.logo_url = None
            self.previous_logo_url = None


    def validate_form(self) -> Optional[str]:
        """
        Valida os campos do formulário. Retorna uma mensagem de erro se algum campo obrigatório não estiver preenchido.
        """
        if not self.corporate_name.value:
            return "Razão Social é obrigatória"

        email = self.email.value
        email = email.strip().lower() if email else ''
        if not email:
            return "Email é obrigatório"
        if not validate_email(email):
            return "Email inválido"
        self.email.value = email

        cnpj = None
        if self.cnpj.value:
            try:
                cnpj = CNPJ(self.cnpj.value)
            except ValueError as e:
                return str(e)

        # Para salvar o logo_url no bucket, é preciso do cnpj como prefix do arquivo
        if not cnpj and self.logo_url:
            return "É preciso CNPJ válido para salvar o logo da empresa"

        # Se todos os campos obrigatórios estão preenchidos, retorna None
        return None

    def _page_resize(self, e):
        if self.page.width < 600: # type: ignore
            self.font_size = 14
            self.icon_size = 16
            self.padding = 20
        elif self.page.width < 1024: # type: ignore
            self.font_size = 16
            self.icon_size = 20
            self.padding = 40
        else:
            self.font_size = 18
            self.icon_size = 24
            self.padding = 50

        # Atualiza os tamanhos dos campos do formulário
        self.cnpj.text_size = self.font_size
        self.corporate_name.text_size = self.font_size
        self.trade_name.text_size = self.font_size
        self.store_name.text_size = self.font_size
        self.ie.text_size = self.font_size
        self.im.text_size = self.font_size
        self.email.text_size = self.font_size
        self.phone.text_size = self.font_size
        self.street.text_size = self.font_size
        self.number.text_size = self.font_size
        self.complement.text_size = self.font_size
        self.neighborhood.text_size = self.font_size
        self.city.text_size = self.font_size
        self.state.text_size = self.font_size
        self.postal_code.text_size = self.font_size
        self.size_cia.text_size = self.font_size

        # Atualiza o padding do container
        self.form.padding = self.padding
        self.form.update()


    def get_form_object(self) -> Empresa:
        """
        Retorna um objeto Empresa com os dados do formulário.
        """
        from src.domains.empresas import CodigoRegimeTributario, Environment, FiscalData
        from src.domains.empresas.models.certificate_a1 import CertificateA1
        from src.domains.empresas.models.empresas_model import Empresa
        from src.domains.shared import Address, Password, PhoneNumber
        from src.services import AsaasPaymentGateway

        address = None
        if self.street.value and self.postal_code.value:
            address = Address(
                street=self.street.value,
                number=self.number.value if self.number.value else 'S/N',
                complement=self.complement.value,
                neighborhood=self.neighborhood.value,
                city=self.city.value if self.city.value else 'São Paulo',
                state=self.state.value if self.state.value else 'SP',
                postal_code=self.postal_code.value,
            )

        size_info = None
        if self.size_cia.value:
            size_info = self.size_cia.value

        cnpj = None
        if self.cnpj.value:
            try:
                cnpj = CNPJ(self.cnpj.value)
            except ValueError as e:
                cnpj = None

        phone = None
        if self.phone.value:
            phone = PhoneNumber(self.phone.value)

        logo = None
        if self.logo_url:
            logo = self.logo_url
        elif self.previous_logo_url:
            logo = self.previous_logo_url

        fiscal_info = None
        certificate_a1 = None
        payment = None

        if self.data and self.data.get('id'):
            # Se já existe um ID, mescla os dados de origem com o novo objeto
            self._empresa_id = self.data.get("id")

            # Dados fiscais
            if fiscal := self.data.get('fiscal'):
                # Obtem o enum CodigoRegimeTributario correspondente ao código crt_code
                crt_enum = None
                amb_enum = None

                # Obtem o 'name' do enum correspondente ao código crt_name
                if fiscal.get('crt_name'):
                    crt_enum = CodigoRegimeTributario(fiscal['crt_name'])

                # Obtem o 'name' do enum correspondente ao código environment_name
                if fiscal.get('environment_name'):
                    amb_enum = Environment(fiscal['environment_name'])

                fiscal_info = FiscalData(
                    crt=crt_enum,
                    environment=amb_enum,
                    nfce_series=fiscal.get('nfce_series'),
                    nfce_number=fiscal.get('nfce_number'),
                    nfce_sefaz_id_csc=fiscal.get('nfce_sefaz_id_csc'),
                    nfce_sefaz_csc=fiscal.get('nfce_sefaz_csc'),
                    nfce_api_enabled=fiscal.get('nfce_api_enabled'),
                )

            # Certificado A1
            if certificate := self.data.get('certificate_a1'):
                password = Password.from_encrypted(certificate.get('password'))
                certificate_a1 = CertificateA1(
                    password=password,
                    serial_number=certificate.get('serial_number'),
                    not_valid_before=certificate.get('not_valid_before'),
                    not_valid_after=certificate.get('not_valid_after'),
                    subject_name=certificate.get('subject_name'),
                    file_name=certificate.get('file_name'),
                    cpf_cnpj=certificate.get('cpf_cnpj'),
                    nome_razao_social=certificate.get('nome_razao_social'),
                    storage_path=certificate.get('storage_path'),
                )

            # Gateway de pagamento
            if pg := self.data.get('payment_gateway'):
                payment = AsaasPaymentGateway(
                    customer_id=pg.get('customer_id'),
                    nextDueDate=pg.get('nextDueDate'),
                    billingType=pg.get('billingType'),
                    dateCreated=pg.get('dateCreated'),
                )

        if not self._empresa_id:
            self._empresa_id = 'emp_' + get_uuid()

        return Empresa.from_dict({
            "id": self._empresa_id,
            "corporate_name": self.corporate_name.value,
            "trade_name": self.trade_name.value,
            "store_name": self.store_name.value,
            "cnpj": cnpj,
            "email": self.email.value,
            "ie": self.ie.value,
            "im": self.im.value,
            "phone": phone,
            "address": address,
            "size": size_info,
            "fiscal": fiscal_info,
            "certificate_a1": certificate_a1,
            "logo_url": logo,
            "payment_gateway": payment,
        })


    def send_to_bucket(self):
        # Faz o upload do arquivo de logo para o bucket
        if not self.local_upload_file or not self.cnpj.value:
            # Não há arquivo local para enviar
            return False

        prefix = f"empresas/{self._empresa_id}/logo"
        file_uid = get_uuid()   # Obtem um UUID único para o arquivo

        _, dot_extension = os.path.splitext(self.local_upload_file)
        # Padroniza a extensão para caracteres minúsculos
        dot_extension = dot_extension.lower()

        # A lógica aqui depende do Bucket utilizado, neste caso é o S3 da AWS, usamos o empresa_id como diretório no bucket.
        file_name_bucket = f"{prefix}/img_{file_uid}{dot_extension}"

        try:
            self.logo_url = bucket_controllers.handle_upload_bucket(
                local_path=self.local_upload_file, key=file_name_bucket)

            if self.logo_url:
                # Atualiza logo na tela
                logo_img = ft.Image(
                    src=self.logo_url,
                    error_content=ft.Text(self.initials_corporate_name),
                    repeat=ft.ImageRepeat.NO_REPEAT,
                    fit=ft.ImageFit.CONTAIN,
                    border_radius=ft.border_radius.all(20),
                )
                self.logo_frame.content = logo_img
                self.logo_frame.update()
                message_snackbar(
                    page=self.page, message="Logo carregado com sucesso!", duration=3000)
                return True

            # O Logo não é válido, URL não foi gerada, mantém o logo anterior se houver
            if self.previous_logo_url:
                self.logo_url = self.previous_logo_url

            message_snackbar(
                page=self.page, message="Não foi possível carregar Logo!", message_type=MessageType.ERROR)

            return False
        except ValueError as e:
            msg = f"Erro de validação ao carregar o logo: {str(e)}"
            message_snackbar(page=self.page, message=msg,
                             message_type=MessageType.ERROR)
            logger.error(msg)
        except RuntimeError as e:
            msg = f"Erro ao carregar o logo: {str(e)}"
            message_snackbar(page=self.page, message=msg,
                             message_type=MessageType.ERROR)
            logger.error(msg)
        finally:
            # Independente de sucesso, remove o arquivo de logo do diretório local uploads/
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

        # Limpa o logo
        if logo := self.logo_frame.content:
            if isinstance(logo, ft.Image):
                logo.src = None
                logo.error_content.text = "Logo" # type: ignore
                logo.update()

        # Limpa os dados de empresa carregados no buffer
        self.data = {}

# Rota: /home/empresas/form/principal
def show_company_main_form(page: ft.Page):
    """Página de cadastro de empresas"""

    route_title = "home/empresas/form"
    empresa_form = page.app_state.form_data # type: ignore

    if id := empresa_form.get('id'):
        route_title += f"/{id}"
    else:
        route_title += "/new"

    def handle_icon_hover(e):
        """Muda o bgcolor do container no hover."""
        e.control.bgcolor = ft.Colors.with_opacity(0.1, ft.Colors.WHITE) if e.data == "true" else ft.Colors.TRANSPARENT
        e.control.update()

    appbar = create_appbar_back(
        page=page,
        title=ft.Text(route_title, size=18, selectable=True),
    )

    empresa_view = EmpresaView(page)
    empresa_view.did_mount()
    form_container = empresa_view.build()

    def save_form_empresa(e):
        # Valida os dados do formulário
        if msg_warning := empresa_view.validate_form():
            message_snackbar(page=page, message=msg_warning,
                             message_type=MessageType.WARNING)
            return

        # Desabilita o botão de salvar para evitar múltiplos cliques
        save_btn.disabled = True

        """
        ! O método .get_form_object() deve ser executado antes do envio do logo para o bucket.
        ! Ele garantirá a criação de um ID para a empresa, caso ainda não exista, permitindo sua identificação no bucket.
        """
        # Cria o objeto Empresa com os dados do formulário para enviar para o backend
        empresa: Empresa = empresa_view.get_form_object()

        if not empresa_view.is_logo_url_web and empresa_view.local_upload_file:
            # Envia o arquivo de logo para o bucket
            if empresa_view.send_to_bucket():
                empresa.logo_url = empresa_view.logo_url
            else:
                message_snackbar(
                    page=page, message="Erro ao enviar o logo para o bucket", message_type=MessageType.WARNING)

            # Apaga arquivo do servidor local
            try:
                os.remove(empresa_view.local_upload_file)
            except:
                pass  # Ignora erros na limpeza do arquivo
            empresa_view.local_upload_file = None

        # Envia os dados para o backend, os exceptions foram tratadas no controller e result contém
        # o status da operação.
        current_user = get_current_user(page)
        result: dict = company_controllers.handle_save_empresas(empresa=empresa, current_user=current_user)

        if result["status"] == "error":
            message_snackbar(
                page=page, message=result["message"], message_type=MessageType.ERROR)
            return

        if not page.app_state.empresa:  # type: ignore [attr-defined]
            # Atualiza o estado do app com o nova empresa antes da navegação se não existir
            page.app_state.set_empresa(empresa.to_dict()) # type: ignore

        # Associa a empresa a lista de empresas do usuário
        current_user.empresas.add(empresa.id)  # Atributo 'empresas' é do tipo set, não permite duplicidade

        if not current_user.empresa_id:
            # Se o usuário não tem empresa associada e selecionada, associa a nova empresa
            current_user.empresa_id = empresa.id

        # Atualiza usuário no banco de dados
        result = user_controllers.handle_update_user_companies(
            usuario_id=current_user.id,
            empresas=current_user.empresas,
            empresa_ativa_id=current_user.empresa_id,
        )

        if result["status"] == "error":
            message_snackbar(
                page=page, message=result["message"], message_type=MessageType.ERROR)
            return

        # Limpa o formulário salvo e volta para a página inicial do usuário
        empresa_view.clear_form()
        page.app_state.clear_form_data() # type: ignore
        page.back() # type: ignore [attr-defined]

    def exit_form_empresa(e):
        if not empresa_view.is_logo_url_web and empresa_view.local_upload_file:
            try:
                os.remove(empresa_view.local_upload_file)
            except:
                pass  # Ignora erros na limpeza do arquivo
            empresa_view.local_upload_file = None

        # Limpa o formulário sem salvar e volta para a página inicial do usuário
        empresa_view.clear_form()
        page.app_state.clear_form_data() # type: ignore
        page.back() # type: ignore [attr-defined]

    # Adiciona os botões "Salvar" & "Cancelar"
    save_btn = ft.ElevatedButton(
        text="Salvar", col={'xs': 6, 'md': 6, 'lg': 6}, on_click=save_form_empresa)
    exit_btn = ft.ElevatedButton(
        text="Cancelar", col={'xs': 6, 'md': 6, 'lg': 6}, on_click=exit_form_empresa)

    return ft.Column(
        controls=[
            form_container,
            ft.Divider(height=5),
            ft.ResponsiveRow(
                columns=12,
                expand=True,
                spacing=20,
                run_spacing=20,
                controls=[save_btn, exit_btn],
                alignment=ft.MainAxisAlignment.END,
            ),
        ],
        data=appbar,
    )
