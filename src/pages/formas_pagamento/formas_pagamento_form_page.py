import logging
import flet as ft

from src.domains.formas_pagamento.controllers import FormasPagamentoController
from src.domains.formas_pagamento.models import FormaPagamento, TipoPagamento, TipoPercentual
from src.domains.formas_pagamento.repositories.implementations import FirebaseFormasPagamentoRepository
from src.domains.formas_pagamento.services import FormasPagamentoService
import src.domains.shared.context.session as session
#from src.domains.shared.context.session import get_current_company, get_current_data_form, get_current_page_width, get_current_user, get_session_colors
from src.domains.shared.models.registration_status import RegistrationStatus
from src.pages.partials import build_input_field
from src.pages.partials.app_bars.appbar import create_appbar_back
from src.pages.partials.monetary_field import MonetaryTextField
from src.pages.partials.responsive_sizes import get_responsive_sizes
from src.shared.utils.messages import MessageType, message_snackbar

logger = logging.getLogger(__name__)


class FormasPagamentoForm:
    def __init__(self, page: ft.Page):
        self.page = page
        self.current_company: dict = session.get_current_company(page)
        self.data: dict = session.get_current_data_form(page)
        self.app_colors: dict[str, str] = session.get_session_colors(page)

        # Campos de redimencionamento do formulário
        self.page_width: int | float = page.width if page.width else 0
        self.responsive_sizes: dict = get_responsive_sizes(page.width)
        self.page_width = session.get_current_page_width(page)
        # Referências a variáveis de campos para redimencionamento
        self.title_ref = ft.Ref[ft.Text]()

        # Responsividade
        self._create_form_fields()
        self.form = self.build_form()
        self.page.on_resized = self._page_resized

    def _on_change_status(self, e: ft.ControlEvent):
        status = e.control
        status.label = "Forma de Pagamento Ativo" if e.data == "true" else "Forma de Pagamento Inativo"
        status.update()

    def _update_dropdwon_tooltip(self, e: ft.ControlEvent):
        """Atualiza o tooltip do dropdown com o texto da opção selecionada."""
        dropdown = e.control
        selected_option = next(
            (opt for opt in dropdown.options if opt.key == dropdown.value), None)
        if selected_option:
            dropdown.tooltip = selected_option.text
            self.name_input.value = selected_option.text
            self.name_input.update()
        else:
            dropdown.tooltip = dropdown.data

        dropdown.update()

    def _on_change_percentage_type(self, e):
        percentage_index = e.control.selected_index

        match percentage_index:
            case 0:
                e.control.thumb_color = ft.Colors.BLUE_900
            case 1:
                e.control.thumb_color = ft.Colors.AMBER_900
            case _:
                e.control.thumb_color = ft.Colors.AMBER_900

        e.control.update()

    def _on_change_order(self, e: ft.ControlEvent):
        digits_only = ''.join(filter(str.isdigit, e.control.value))
        # Limita a 2 dígitos numéricos
        digits_only = digits_only[:2]

        if e.control.value != digits_only:
            e.control.value = digits_only
            e.control.update()

    def _create_form_fields(self):
        """Cria os campos do formulário"""

        self.payment_type_input = ft.Dropdown(
            col={'xs': 12, 'sm': 12, 'md': 6, 'lg': 4, 'xl': 4},
            label="Tipo da Forma de Pagamento",
            expanded_insets=ft.padding.all(10),
            options=[
                ft.dropdown.Option(key=tipo.name, text=tipo.value)
                for tipo in TipoPagamento
            ],
            tooltip="Selecione o tipo da Forma de Pagamento",
            data="Selecione o tipo da Forma de Pagamento",
            on_change=self._update_dropdwon_tooltip,
            filled=True,
            border=ft.InputBorder.OUTLINE,
            border_color=self.app_colors["primary"],
            width=self.responsive_sizes["input_width"],
            text_size=self.responsive_sizes["font_size"],
        )
        self.name_input = build_input_field(
            page_width=self.page_width,
            app_colors=self.app_colors,
            col={'xs': 12, 'sm': 12, 'md': 6, 'lg': 4, 'xl': 4},
            label='Nome',
            icon=ft.Icons.CREDIT_CARD,
        )
        # Status da Forma de Pagamento: Switch Ativo/Inativo
        self.status_input = ft.Switch(
            col={'xs': 12, 'sm': 12, 'md': 12, 'lg': 4, 'xl': 4},
            label="Forma de Pagamento Ativo",
            value=True,
            on_change=self._on_change_status,
        )
        # Percentual de Desconto
        self.percentage_input = MonetaryTextField(
            label="Percentual Desconto/Acréscimo",
            col={'xs': 12, 'sm': 12, 'md': 6, 'lg': 4, 'xl': 4},
            page_width=self.page_width,
            app_colors=self.app_colors,
            prefix_text="%",
        )
        # Tipo de Percentual (Desconto/Acréscimo)
        self.percentage_type_input = ft.CupertinoSlidingSegmentedButton(
            selected_index=1,
            col={'xs': 12, 'sm': 12, 'md': 6, 'lg': 4, 'xl': 4},
            thumb_color=ft.Colors.AMBER_900,
            padding=ft.padding.symmetric(0, 10),
            controls=[ft.Text(percentage.value)
                      for percentage in TipoPercentual],
            on_change=self._on_change_percentage_type,
        )
        # Ordem de apresentação em grid, dropdowns, etc.
        self.order_input = build_input_field(
            label='Ordem de apresentação',
            col={'xs': 12, 'sm': 12, 'md': 12, 'lg': 4, 'xl': 4},
            page_width=self.page_width,
            app_colors=self.app_colors,
            icon=ft.Icons.FORMAT_LIST_NUMBERED_ROUNDED,
            keyboard_type=ft.KeyboardType.NUMBER,
            rtl=True,
            text_align=ft.TextAlign.RIGHT,
            on_change=self._on_change_order,
        )

    def build_form(self) -> ft.Container:
        """Constrói o formulário"""
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
                ft.Text(ref=self.title_ref, value="Formas de Pagamento",
                        size=self.responsive_sizes["title_size"], weight=ft.FontWeight.BOLD),
                ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
                responsive_row(
                    controls=[self.payment_type_input, self.name_input, self.status_input,]),
                ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
                responsive_row(
                    controls=[self.percentage_input.text_field, self.percentage_type_input, self.order_input,]
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.START,
            spacing=20,
            alignment=ft.MainAxisAlignment.SPACE_EVENLY,
        )

        return ft.Container(
            content=build_content,
            padding=self.responsive_sizes["form_padding"],
            bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
            border_radius=ft.border_radius.all(20),
        )

    def did_mount(self):
        if self.data and self.data.get("id"):
            self.populate_form_fields()
        self.page.update()

    def populate_form_fields(self):
        self.payment_type_input.value = self.data["payment_type"].name
        self.name_input.value = self.data["name"]
        is_active = self.data["status"] == RegistrationStatus.ACTIVE
        self.status_input.value = is_active
        self.status_input.label = "Forma de Pagamento Ativo" if is_active else "Forma de Pagamento Inativo"
        self.percentage_input.set(self.data.get("percentage", 0.0))

        index_percentage_type = {
            'DESCONTO': 0,
            'ACRESCIMO': 1,
        }
        per_type = self.data.get("percentage_type", TipoPercentual.DESCONTO)
        self.percentage_type_input.selected_index = index_percentage_type[per_type.name]

        self.order_input.value = str(self.data.get("order", 99))

    def _page_resized(self, e: ft.ControlEvent):
        self.responsive_sizes: dict = get_responsive_sizes(self.page.width)

        width = self.responsive_sizes["input_width"]
        size = self.responsive_sizes["font_size"]

        self.payment_type_input.width = width
        self.payment_type_input.text_size = size
        self.name_input.width = width
        self.name_input.text_size = size
        self.status_input.width = width
        self.status_input.label_style = ft.TextStyle(size=size)
        self.percentage_input.text_field.width = width
        self.percentage_input.text_field.text_size = size
        self.order_input.width = width
        self.order_input.text_size = size
        self.title_ref.current.size = self.responsive_sizes["title_size"]
        self.form.padding = self.responsive_sizes["form_padding"]

    def validate_form(self) -> str | None:
        if not self.payment_type_input.value:
            return "Selecione o tipo da Forma de Pagamento"
        if not self.name_input.value:
            return "Informe o nome da Forma de Pagamento"
        return None

    def get_form_object_updated(self) -> FormaPagamento:
        payment_type = self.payment_type_input.value or "OUTRO"
        self.data["payment_type"] = TipoPagamento[payment_type]
        self.data["name"] = self.name_input.value
        self.data["status"] = RegistrationStatus.ACTIVE if self.status_input.value else RegistrationStatus.INACTIVE
        self.data["percentage"] = float(self.percentage_input.get_numeric_value())

        index_percentage_type = {
            0: TipoPercentual.ACRESCIMO,
            1: TipoPercentual.DESCONTO,
        }

        self.data["percentage_type"] = index_percentage_type.get(self.percentage_type_input.selected_index, TipoPercentual.ACRESCIMO)

        order_int = int(self.order_input.value) if self.order_input.value else 99
        self.data["order"] = int(order_int)
        self.data["empresa_id"] = self.current_company["id"]

        return FormaPagamento(**self.data)

    def build(self) -> ft.Container:
        return self.form

    def clear_form(self):
        """Limpa os campos do formulário"""
        for field in self.__dict__.values():
            if isinstance(field, (ft.TextField, ft.Dropdown)):
                field.value = ""
            if isinstance(field, ft.Switch):
                field.value = True  # Por default, o status é ativo
            if isinstance(field, ft.Checkbox):
                field.value = False  # Por default, o "tem whatsapp" é False
            if isinstance(field, ft.CupertinoSlidingSegmentedButton):
                field.selected_index = 1  # Por default, o tipo de percentual é ACRESCIMO

        if hasattr(self, 'percentage_input') and isinstance(self.percentage_input, MonetaryTextField):
            self.percentage_input.set(0.0)

        # Limpa o buffer com os dados de pedidos carregados
        self.data = {}


def show_formas_pagamento_form(page: ft.Page) -> ft.View:
    """Página de Formas de Pagamento."""
    route_title = "/home/formasdepagamento/form"
    forma_pagamento_data = session.get_current_data_form(page)

    if id := forma_pagamento_data.get("id"):
        route_title += f"/{id}"
    else:
        route_title += "/new"

    forma_pagamento_view = FormasPagamentoForm(page)
    forma_pagamento_view.did_mount()
    form_container = forma_pagamento_view.build()

    def save_form_forma_pagamento(e):
        # Valida dados do formulário
        if msg := forma_pagamento_view.validate_form():
            message_snackbar(page, msg, MessageType.WARNING)
            return

        save_btn.disabled = True
        forma_pagamento: FormaPagamento = forma_pagamento_view.get_form_object_updated()
        repository = FirebaseFormasPagamentoRepository()
        services = FormasPagamentoService(repository)
        controllers = FormasPagamentoController(services)
        current_user = session.get_current_user(page)
        result = controllers.save_forma_pagamento(forma_pagamento, current_user)

        if result["status"] == "error":
            message_snackbar(page=page, message=result["message"], message_type=MessageType.ERROR, center=True)
            save_btn.disabled = False
            return

        message_snackbar(page=page, message=result["message"], message_type=MessageType.SUCCESS, center=True)
        # Limpa o formulário salvo e volta para a página anterior que a invocou
        forma_pagamento_view.clear_form()
        page.back() # type: ignore [attr-defined]

    def exit_form_forma_pagamento(e):
        # Limpa o formulário salvo e volta para a página anterior que a invocou
        forma_pagamento_view.clear_form()
        page.back() # type: ignore [attr-defined]

    # Cria os botões "Salvar" & "Cancelar"
    save_btn = ft.ElevatedButton(
        text="Salvar", col={'xs': 5, 'md': 5, 'lg': 5}, on_click=save_form_forma_pagamento)
    exit_btn = ft.ElevatedButton(
        text="Cancelar", col={'xs': 5, 'md': 5, 'lg': 5}, on_click=exit_form_forma_pagamento)
    space_between = ft.Container(col={'xs': 2, 'md': 2, 'lg': 2})

    appbar = create_appbar_back(page=page, title=ft.Text(route_title, size=18, selectable=True))

    form = ft.Column(
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
        route="/home/formasdepagamento/form",
        controls=[form],
        appbar=appbar,
        drawer=page.drawer,
        scroll=ft.ScrollMode.AUTO,
        bgcolor=ft.Colors.BLACK,
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        padding=ft.padding.all(10)
    )
