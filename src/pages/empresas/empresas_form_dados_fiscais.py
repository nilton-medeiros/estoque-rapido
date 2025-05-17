import logging
# import os
# import asyncio

from enum import Enum  # Certifique-se de importar o módulo 'Enum'
from typing import Optional

import flet as ft

from src.domains.empresas.controllers import empresas_controllers
from src.domains.empresas.models.empresa_model import Empresa
from src.domains.empresas.models.empresa_subclass import CodigoRegimeTributario, EmpresaSize, Environment
from src.domains.usuarios.models.usuario_model import Usuario
from src.pages.partials.build_input_responsive import build_input_field
from src.shared import MessageType, message_snackbar

logger = logging.getLogger(__name__)


class EmpresaViewDadosFiscais:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page_width: int|float = page.width if page.width else 0
        self.data = page.app_state.form_data # type: ignore
        # Vars propiedades
        self.font_size = 18
        self.icon_size = 24
        self.padding = 50
        self.input_width = 400,
        self.app_colors: dict = page.session.get("user_colors")  # type: ignore

        # Responsividade
        self._create_form_fields()
        self.form = self.build_form()
        self.page.on_resized = self._page_resize

    def _update_dropdown_tooltip(self, e: ft.ControlEvent):
        """Atualiza o tooltip do Dropdown com o texto da opção selecionada."""
        dropdown = e.control
        selected_option = next((opt for opt in dropdown.options if opt.key == dropdown.value), None)
        if selected_option:
            dropdown.tooltip = selected_option.text
        else:
            dropdown.tooltip = dropdown.data
        dropdown.update()


    def _create_form_fields(self):
        """Cria os campos do formulário Dados Fiscais"""

        """Cabeçalho com dados de identificação da empresa"""

        # CNPJ: Somente leitura
        self.cnpj = build_input_field(
            page_width=self.page_width,
            app_colors=self.app_colors,
            col={'xs': 12, 'md': 5, 'lg': 3},
            label="CNPJ",
            icon=ft.Icons.ASSURED_WORKLOAD_OUTLINED,
            # icon=ft.Icons.ACCOUNT_BALANCE_OUTLINED,
            read_only=True,
        )
        # Nome da loja
        self.store_name = build_input_field(
            page_width=self.page_width,
            app_colors=self.app_colors,
            col={'xs': 12, 'md': 7, 'lg': 4},
            label="Nome da Loja",
            icon=ft.Icons.STORE_MALL_DIRECTORY,
            read_only=True,
        )
        # Razão Social: Somente leitura
        self.corporate_name = build_input_field(
            page_width=self.page_width,
            app_colors=self.app_colors,
            col={'xs': 12, 'md': 12, 'lg': 5},
            label="Razão Social",
            icon=ft.Icons.CORPORATE_FARE,
            read_only=True,
        )

        """Dados Fiscais"""

        # Porte da Empresa
        self.size_cia = ft.Dropdown(
            col={'xs': 12, 'md': 6, 'lg': 5},
            label="Porte da Empresa",
            text_size=16,
            # expand=True,
            expanded_insets=ft.padding.all(10),
            options=[
                ft.dropdown.Option(key=size.name, text=size.value)
                for size in EmpresaSize
            ],
            tooltip='Selecione o porte da empresa',
            data='Selecione o porte da empresa',
            on_change=self._update_dropdown_tooltip,
            filled=True,
            border=ft.InputBorder.OUTLINE,
            border_color=self.app_colors["primary"],
            width=self.input_width, # type: ignore
        )

        # CRT: Regime Tributário
        self.crt = ft.Dropdown(
            col={'xs': 12, 'md': 6, 'lg': 4},
            label="Regime Tributário",
            text_size=16,
            # expand=True,
            expanded_insets=ft.padding.all(10),
            options=[
                ft.dropdown.Option(key=regime.name,  text=regime.value[1])
                for regime in CodigoRegimeTributario
            ],
            tooltip='Selecione o regime tributário',
            data='Selecione o regime tributário',
            on_change=self._update_dropdown_tooltip,
            filled=True,
            border=ft.InputBorder.OUTLINE,
            border_color=self.app_colors["primary"],
            width=self.input_width, # type: ignore
        )
        # Tipo de Ambiente
        self.environment = ft.Dropdown(
            col={'xs': 12, 'md': 12, 'lg': 3},
            label="Ambiente",
            text_size=16,
            expanded_insets=ft.padding.all(10),
            options=[
                ft.dropdown.Option(key=ambiente.name, text=ambiente.value)
                for ambiente in Environment
            ],
            tooltip='Selecione o tipo de ambiente',
            data='Selecione o tipo de ambiente',
            on_change=self._update_dropdown_tooltip,
            filled=True,
            border=ft.InputBorder.OUTLINE,
            border_color=self.app_colors["primary"],
            width=self.input_width, # type: ignore
        )
        # Próximo Número de Série da Nota Fiscal
        self.nfce_series = build_input_field(
            page_width=self.page_width,
            app_colors=self.app_colors,
            col={'xs': 12, 'md': 6, 'lg': 6},
            label="Série NFC-e",
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        # Próximo Número da Nota Fiscal
        self.nfce_number = build_input_field(
            page_width=self.page_width,
            app_colors=self.app_colors,
            col={'xs': 12, 'md': 6, 'lg': 6},
            label="Número NFC-e",
            hint_text="Próximo número a ser emitido",
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        # Credenciais Sefaz concedido ao emissor de NFCe
        self.nfce_sefaz_id_csc = build_input_field(
            page_width=self.page_width,
            app_colors=self.app_colors,
            col={'xs': 12, 'md': 6, 'lg': 6},
            label="Identificação do CSC",
            hint_text="Id. Código Segurança do Contribuínte",
            tooltip="Identificação do Código Segurança do Contribuínte",
            helper_text="Para obter o CSC, o contribuinte precisa se credenciar na SEFAZ do seu estado. Fale com seu contador.",
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        self.nfce_sefaz_csc = build_input_field(
            page_width=self.page_width,
            app_colors=self.app_colors,
            col={'xs': 12, 'md': 6, 'lg': 6},
            label="Código do CSC",
            hint_text="Código Segurança do Contribuínte",
            tooltip="Código Segurança do Contribuínte",
        )


    def build_form(self) -> ft.Container:
        """Constrói o formulário de dados fiscais"""
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
                ft.Text("Identificação da Empresa", size=16),
                ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
                # Campos de identificação da empresa: Somente leitura
                responsive_row(controls=[self.cnpj, self.store_name, self.corporate_name]),
                ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
                ft.Divider(height=10),
                ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
                ft.Text("Dados Fiscais", size=16),
                ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
                responsive_row(controls=[self.size_cia, self.crt, self.environment]),
                ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                responsive_row(controls=[self.nfce_series, self.nfce_number]),
                ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                responsive_row(controls=[self.nfce_sefaz_id_csc, self.nfce_sefaz_csc]),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.START,
            spacing=20,
            alignment=ft.MainAxisAlignment.SPACE_EVENLY,
        )

        return ft.Container(
            content=build_content,
            padding=self.padding,
            bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
            border_radius=ft.border_radius.all(10),
        )


    def did_mount(self):
        if self.data and self.data.get('id'):
            # Preenche os campos com os dados fiscais da empresa
            self.populate_form_fields()
        self.page.update()


    def populate_form_fields(self):
        """Preenche os campos do formulário com os dados da empresa"""
        if cnpj := self.data.get('cnpj'):
            self.cnpj.value = str(cnpj)
        else:
            self.cnpj.value = ''

        self.corporate_name.value = self.data.get('corporate_name', '')
        self.store_name.value = self.data.get('store_name', '')

        if size_enum := self.data.get('size'):
            self.size_cia.value = size_enum.name
        else:
            self.size_cia.value = ''

        self.crt.value = ''
        self.environment.value = ''
        self.nfce_series.value = ''
        self.nfce_number.value = ''
        self.nfce_sefaz_id_csc.value = ''
        self.nfce_sefaz_csc.value = ''

        if fiscal := self.data.get("fiscal"):
            if crt_name := fiscal.get('crt_name'):
                self.crt.value = crt_name
            if emvironment_name := fiscal.get('environment_name'):
                self.environment.value = emvironment_name
            else:
                self.environment.value = 'HOMOLOGACAO'
            self.nfce_series.value = fiscal.get('nfce_series', '')
            self.nfce_number.value = fiscal.get('nfce_number', '')
            self.nfce_sefaz_id_csc.value = fiscal.get('nfce_sefaz_id_csc', '')
            self.nfce_sefaz_csc.value = fiscal.get('nfce_sefaz_csc', '')


    def validate_form(self) -> Optional[str]:
        """
        Valida os campos do formulário. Retorna uma mensagem de erro se algum campo obrigatório não estiver preenchido.
        """
        if not self.size_cia.value:
            return "Por favor, selecione o porte da empresa."
        if not self.crt.value:
            return "Por favor, selecione o regime tributário."
        if not self.nfce_series.value:
            return "Por favor, preencha a série da nota fiscal."
        if not self.nfce_number.value:
            return "Por favor, preencha o número da nota fiscal."
        if not self.environment.value:
            return "Por favor, selecione o ambiente."
        if not self.nfce_sefaz_id_csc.value:
            return "Por favor, preencha a identificação do CSC. (Código de Segurança do Contribuínte)"
        if not self.nfce_sefaz_csc.value:
            return "Por favor, preencha o código do CSC. (Código de Segurança do Contribuínte)"
        return None


    def _page_resize(self, e):
        if self.page_width < 600:
            self.font_size = 14
            self.icon_size = 16
            self.padding = 20
            self.input_width = 280,
        elif self.page_width < 1024:
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
        self.cnpj.text_size = self.font_size
        self.corporate_name.text_size = self.font_size
        self.store_name.text_size = self.font_size
        self.size_cia.text_size = self.font_size
        self.crt.text_size = self.font_size
        self.nfce_series.text_size = self.font_size
        self.nfce_number.text_size = self.font_size
        self.environment.text_size = self.font_size
        self.nfce_sefaz_id_csc.text_size = self.font_size
        self.nfce_sefaz_csc.text_size = self.font_size

        # Atualiza o padding do container
        self.form.padding = self.padding
        self.form.update()


    def get_form_object(self) -> Empresa:
        """
        Atualiza self.data com os dados do formulário e o retorna atualizado.
        Garante que a chave 'fiscal' exista antes de atualizá-la.
        """

        # Garante que 'fiscal' exista como um dicionário.
        # Se 'fiscal' não existir, cria como {}. Se existir, retorna o dict existente.
        fiscal_data = self.data.setdefault('fiscal', {})

        # Caso 'fiscal' existisse mas fosse None, resetamos para um dict vazio
        if fiscal_data is None:
            fiscal_data = {}
            self.data['fiscal'] = fiscal_data

        # Atualiza 'size' diretamente
        self.data['size'] = EmpresaSize[self.size_cia.value] # type: ignore

        # Atualiza os dados dentro do dicionário 'fiscal'
        fiscal_data['crt_name'] = self.crt.value
        fiscal_data['environment_name'] = self.environment.value
        fiscal_data['nfce_series'] = self.nfce_series.value
        fiscal_data['nfce_number'] = self.nfce_number.value
        fiscal_data['nfce_sefaz_id_csc'] = self.nfce_sefaz_id_csc.value
        fiscal_data['nfce_sefaz_csc'] = self.nfce_sefaz_csc.value

        return Empresa.from_dict(self.data)


    def build(self) -> ft.Container:
        return self.form


    def clear_form(self):
        """Limpa os campos do formulário"""
        for field in self.__dict__.values():
            if isinstance(field, (ft.TextField, ft.Dropdown)):
                field.value = ''


# Rota: /home/empresas/form/dados-fiscais
def form_dados_fiscais(page: ft.Page):
    """Página de cadstro dos dados fiscais da empresa"""

    route_title = "home/empresas/form/dados-fiscais"
    empresa_form = page.app_state.form_data # type: ignore

    if id := empresa_form.get('id'):
        route_title += f"/{id}"
    else:
        message_snackbar(page=page, message="Empresa não definida", message_type=MessageType.WARNING)
        page.go(page.data if page.data else '/home')

    if not empresa_form.get('cnpj'):
        message_snackbar(page=page, message="CNPJ não definido", message_type=MessageType.WARNING)
        page.go(page.data if page.data else '/home')


    def handle_icon_hover(e):
        """Muda o bgcolor do container no hover."""
        e.control.bgcolor = ft.Colors.with_opacity(0.1, ft.Colors.WHITE) if e.data == "true" else ft.Colors.TRANSPARENT
        e.control.update()

    appbar = ft.AppBar(
        leading=ft.Container(
            alignment=ft.alignment.center_left,
            padding=ft.padding.only(left=10),
            content=ft.Container(
                width=40,
                height=40,
                border_radius=ft.border_radius.all(20),
                ink=True,  # Aplica ink ao wrapper (ao clicar da um feedback visual para o usuário)
                bgcolor=ft.Colors.TRANSPARENT,
                alignment=ft.alignment.center,
                on_hover=handle_icon_hover,
                content=ft.Icon(ft.Icons.ARROW_BACK),
                on_click=lambda _: page.go(page.data if page.data else '/home'),
                tooltip="Voltar",
                # clip_behavior: O conteúdo será recortado (ou não) de acordo com esta opção.
                clip_behavior=ft.ClipBehavior.ANTI_ALIAS # Ajuda a garantir que o hover respeite o border_radius
            ),
        ),
        title=ft.Text(route_title, size=18),
        bgcolor=ft.Colors.with_opacity(0.9, ft.Colors.PRIMARY_CONTAINER), # Exemplo com opacidade
        adaptive=True,
    )

    empresa_view = EmpresaViewDadosFiscais(page)
    empresa_view.did_mount()
    form_container = empresa_view.build()

    async def save_form_empresa(e):
        # Valida os dados do formulário
        if msg_warning := empresa_view.validate_form():
            message_snackbar(page=page, message=msg_warning,
                             message_type=MessageType.WARNING)
            return

        # Desabilita o botão de salvar para evitar múltiplos cliques
        save_btn.disabled = True

        # Cria o objeto Empresa com os dados do formulário para enviar para o backend
        empresa: Empresa = empresa_view.get_form_object()

        # Envia os dados para o backend, os exceptions foram tratadas no controller e result contém
        # o status da operação.
        user: dict = page.app_state.usuario # type: ignore
        result: dict = await empresas_controllers.handle_save_empresas(empresa=empresa, usuario=user)

        if result["is_error"]:
            message_snackbar(
                page=page, message=result["message"], message_type=MessageType.ERROR)
            return

        # Atualiza o estado do app com o nova empresa antes da navegação se não existir
        page.app_state.set_empresa(empresa.to_dict()) # type: ignore

        # Limpa o formulário salvo e limpa a empresa do app state: form_data e volta para a página inicial do usuário
        empresa_view.clear_form()
        page.app_state.clear_form_data() # type: ignore
        message_snackbar(page=page, message=result["message"],
                         message_type=MessageType.SUCCESS)
        page.go(page.data if page.data else '/home')

    def exit_form_empresa(e):
        # Limpa o formulário sem salvar e volta para a página inicial do usuário
        empresa_view.clear_form()
        page.app_state.clear_form_data() # type: ignore
        page.go(page.data if page.data else '/home')

    # Adiciona os botões "Salvar" & "Cancelar"
    save_btn = ft.ElevatedButton(
        text="Salvar", col={'xs': 6, 'md': 6, 'lg': 6}, on_click=save_form_empresa)
    exit_btn = ft.ElevatedButton(
        text="Cancelar", col={'xs': 6, 'md': 6, 'lg': 6}, on_click=exit_form_empresa)

    return ft.Column(
        controls=[
            form_container,
            ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
            ft.Divider(height=10),
            ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
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
