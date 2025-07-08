import logging
import os
import base64
import mimetypes
import re  # Adicionado para expressões regulares

import flet as ft
from datetime import datetime  # Adicionado para validação de data

from src.domains.shared import NomePessoa, RegistrationStatus

import src.domains.clientes.controllers.clientes_controllers as client_controllers

from src.domains.clientes.models import Cliente
from src.domains.shared.models.address import Address
from src.pages.partials import build_input_field
from src.pages.partials.responsive_sizes import get_responsive_sizes
from src.shared.utils import message_snackbar, MessageType, ProgressiveMessage
from src.shared.config import get_app_colors

logger = logging.getLogger(__name__)


class ClienteForm:
    def __init__(self, page: ft.Page):
        self.page = page
        self.empresa_logada = page.app_state.empresa  # type: ignore [attr-defined]
        self.data = page.app_state.form_data  # type: ignore [attr-defined]
        # Campos de redimencionamento do formulário
        self.font_size = 18
        self.icon_size = 24
        self.padding = 50
        self.app_colors: dict[str, str] = get_app_colors('blue')

        # ! page.session é um objeto que contém o método .get(), não confundir com um dict
        if page.session.get("user_colors"):
            self.app_colors: dict[str, str] = page.session.get(
                "user_colors")  # type: ignore [attr-defined]

        self.input_width = 400

        # Responsividade
        self._create_form_fields()
        self.form = self.build_form()
        self.page.on_resized = self._page_resize

    def on_change_status(self, e):
        status = e.control
        status.label = "Cliente Ativo" if e.data == "true" else "Cliente Inativo"
        status.update()

    def _create_form_fields(self):
        """Cria os campos do formulário de Cliente"""

        # Primeiro grupo ResponsiveRow --------------------------------------------------------------------------------------
        # Primeiro Nome
        self.first_name = build_input_field(
            page_width=self.page.width,  # type: ignore [attr-defined]
            app_colors=self.app_colors,
            col={'xs': 12, 'md': 12, 'lg': 4},
            label="Nome",
            icon=ft.Icons.FIRST_PAGE,
        )
        # Último nome (sobrenome)
        self.last_name = build_input_field(
            page_width=self.page.width,  # type: ignore [attr-defined]
            app_colors=self.app_colors,
            col={'xs': 12, 'md': 12, 'lg': 4},
            label="Sobrenome",
            icon=ft.Icons.LAST_PAGE,
        )
        # Email do Cliente
        self.email = build_input_field(
            page_width=self.page.width,  # type: ignore [attr-defined]
            app_colors=self.app_colors,
            col={'xs': 12, 'md': 12, 'lg': 4},
            label="Email",
            keyboard_type=ft.KeyboardType.EMAIL,
            icon=ft.Icons.EMAIL_OUTLINED,
        )

        # Segundo grupo ResponsiveRow --------------------------------------------------------------------------------------
        # CPF
        self.cpf = build_input_field(
            page_width=self.page.width,  # type: ignore [attr-defined]
            app_colors=self.app_colors,
            col={'xs': 12, 'md': 6, 'lg': 4},
            label="CPF",
            hint_text="123.456.789-00",
            keyboard_type=ft.KeyboardType.NUMBER,
            max_length=14,  # 11 dígitos + 2 pontos + 1 traço
            icon=ft.Icons.BADGE_OUTLINED,
            counter_text="Opcional CPF na Nota",
            on_change=self._handle_cpf_change,
        )
        # Celular
        self.phone = build_input_field(
            page_width=self.page.width,  # type: ignore [attr-defined]
            app_colors=self.app_colors,
            col={'xs': 12, 'md': 6, 'lg': 4},
            label="Celular",
            hint_text="(11) 98765-4321",  # Atualizado para refletir a máscara
            keyboard_type=ft.KeyboardType.NUMBER,  # Define o teclado numérico
            max_length=15,  # (XX) XXXXX-XXXX tem 15 caracteres
            icon=ft.Icons.PHONE_ANDROID,
            on_change=self._handle_phone_change,  # Adiciona o handler de mudança
        )
        self.is_whatsapp_check = ft.Checkbox(
            col={'xs': 12, 'md': 6, 'lg': 2},
            label="WhatsApp",
        )

        # Aniversário
        # self.birthday_dtpicker = ft.DatePicker(
        #     cancel_text="Cancelar",
        #     confirm_text="Confirmar",
        #     error_format_text="Data inválida",
        #     field_hint_text="MM/DD/AAAA",
        #     field_label_text="Data de Nascimento",
        #     switch_to_calendar_icon=ft.Icons.CALENDAR_MONTH,
        #     date_picker_entry_mode=ft.DatePickerEntryMode.INPUT,
        #     keyboard_type=ft.KeyboardType.NUMBER,
        # )

        sizes = get_responsive_sizes(self.page.width)

        self.birthday = ft.TextField(
            col={'xs': 12, 'md': 6, 'lg': 2},
            label="Aniversário",
            text_size=self.font_size,
            border_color=self.app_colors["primary"],
            focused_border_color=self.app_colors["container"],
            hint_text="DD/MM",
            prefix=ft.Container(
                content=ft.Icon(
                    name=ft.Icons.CAKE, color=self.app_colors["primary"], size=sizes["icon_size"]),
                padding=ft.padding.only(right=10),
            ),
            keyboard_type=ft.KeyboardType.NUMBER,
            bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
            label_style=ft.TextStyle(
                # Cor do label igual à borda # type: ignore
                color=self.app_colors["primary"],
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
            on_change=self._handle_birthday_change,
        )

        # Terceiro grupo ResponsiveRow --------------------------------------------------------------------------------------
        # Endereço
        self.street = build_input_field(
            page_width=self.page.width,  # type: ignore
            app_colors=self.app_colors,
            col={'xs': 12, 'md': 12, 'lg': 6},
            label="Rua",
            icon=ft.Icons.LOCATION_ON,
        )
        self.number = build_input_field(
            page_width=self.page.width,  # type: ignore
            app_colors=self.app_colors,
            col={'xs': 12, 'md': 6, 'lg': 2},
            label="Número",
            icon=ft.Icons.NUMBERS,
        )
        self.complement = build_input_field(
            page_width=self.page.width,  # type: ignore
            app_colors=self.app_colors,
            col={'xs': 12, 'md': 6, 'lg': 4},
            label="Complemento",
            icon=ft.Icons.ADD_LOCATION,
            hint_text="Apto 101",
            hint_fade_duration=5,
        )

        # Quarto grupo ResponsiveRow --------------------------------------------------------------------------------------
        self.neighborhood = build_input_field(
            page_width=self.page.width,  # type: ignore
            app_colors=self.app_colors,
            col={'xs': 12, 'md': 6, 'lg': 4},
            label="Bairro",
            icon=ft.Icons.LOCATION_CITY,
        )
        self.city = build_input_field(
            page_width=self.page.width,  # type: ignore
            app_colors=self.app_colors,
            col={'xs': 12, 'md': 6, 'lg': 3},
            label="Cidade",
            icon=ft.Icons.LOCATION_CITY,
            hint_text="São Paulo",
            hint_fade_duration=5,
        )
        self.state = build_input_field(
            page_width=self.page.width,  # type: ignore
            app_colors=self.app_colors,
            col={'xs': 12, 'md': 6, 'lg': 2},
            label="Estado",
            icon=ft.Icons.LOCATION_CITY,
            hint_text="SP",
            hint_fade_duration=5,
            keyboard_type=ft.KeyboardType.TEXT,
            max_length=2,
        )
        self.postal_code = build_input_field(
            page_width=self.page.width,  # type: ignore
            app_colors=self.app_colors,
            col={'xs': 12, 'md': 6, 'lg': 3},
            label="CEP",
            icon=ft.Icons.LOCATION_CITY,
            hint_text="00000-000",
            hint_fade_duration=5,
        )

        # Quinto grupo ResponsiveRow --------------------------------------------------------------------------------------
        # Switch Ativo/Inativo
        self.status = ft.Switch(
            col={'xs': 12, 'md': 12, 'lg': 12},
            label="Cliente Ativo",
            value=True,
            on_change=self.on_change_status,
        )

    def _apply_cpf_mask(self, cpf_str: str) -> str:
        """Aplica a máscara de CPF (XXX.XXX.XXX-XX) a uma string."""
        if not cpf_str:
            return ""

        # Remove qualquer caractere que não seja dígito
        digits_only = re.sub(r'\D', '', cpf_str)

        # Limita a 11 dígitos
        digits_only = digits_only[:11]

        # Aplica a máscara gradualmente
        if len(digits_only) > 9:
            return f"{digits_only[:3]}.{digits_only[3:6]}.{digits_only[6:9]}-{digits_only[9:]}"
        elif len(digits_only) > 6:
            return f"{digits_only[:3]}.{digits_only[3:6]}.{digits_only[6:]}"
        elif len(digits_only) > 3:
            return f"{digits_only[:3]}.{digits_only[3:]}"
        else:
            return digits_only

    def _handle_cpf_change(self, e):
        """Formata a entrada do campo de CPF para XXX.XXX.XXX-XX enquanto o usuário digita."""
        formatted_value = self._apply_cpf_mask(e.control.value)

        if e.control.value != formatted_value:
            e.control.value = formatted_value
            e.control.update()

    def _apply_phone_mask(self, phone_str: str) -> str:
        """Aplica a máscara de telefone (XX) XXXXX-XXXX a uma string."""
        if not phone_str:
            return ""

        # Remove qualquer caractere que não seja dígito
        digits_only = re.sub(r'\D', '', phone_str)

        # Limita a 15 dígitos
        digits_only = digits_only[:15]

        formatted_value = ""
        if len(digits_only) <= 2:
            formatted_value = f"({digits_only}"
        elif len(digits_only) <= 6:
            formatted_value = f"({digits_only[:2]}) {digits_only[2:]}"
        elif len(digits_only) <= 10:  # Para números de 8 dígitos (fixos)
            formatted_value = f"({digits_only[:2]}) {digits_only[2:6]}-{digits_only[6:]}"
        elif len(digits_only) <= 11:  # Para números de 9 dígitos (celulares)
            formatted_value = f"({digits_only[:2]}) {digits_only[2:7]}-{digits_only[7:]}"
        else:  # Trunca se houver mais de 11 dígitos
            formatted_value = f"({digits_only[:2]}) {digits_only[2:7]}-{digits_only[7:11]}"

        return formatted_value

    def _handle_phone_change(self, e):
        """Formata a entrada do campo de telefone enquanto o usuário digita."""
        formatted_value = self._apply_phone_mask(e.control.value)

        if e.control.value != formatted_value:
            e.control.value = formatted_value
            e.control.update()

    def _handle_birthday_change(self, e):
        """
        Formata a entrada do campo de aniversário para DD/MM enquanto o usuário digita.
        """
        raw_value = e.control.value
        if not raw_value:
            return

        # Remove qualquer caractere que não seja dígito
        digits_only = re.sub(r'\D', '', raw_value)

        formatted_value = ""
        if len(digits_only) <= 2:
            # Se 0-2 dígitos, apenas mantém
            formatted_value = digits_only
        elif len(digits_only) <= 4:
            # Se 3-4 dígitos, insere '/' após os dois primeiros
            formatted_value = f"{digits_only[:2]}/{digits_only[2:]}"
        else:
            # Se mais de 4 dígitos, trunca para 4 e formata
            formatted_value = f"{digits_only[:2]}/{digits_only[2:4]}"

        # Atualiza o valor do TextField
        e.control.value = formatted_value
        e.control.update()

    def _validate_birthday_format(self, birthday_str: str) -> bool:
        """
        Valida se a string de aniversário está no formato DD/MM e representa um dia/mês válido.
        """
        if not birthday_str:
            return True  # Campo vazio é considerado válido (campo opcional)

        # Tenta converter para uma data para validar dia e mês (ano fictício)
        return bool(re.match(r'^\d{2}/\d{2}$', birthday_str) and self._is_valid_day_month(birthday_str))

    def build_form(self) -> ft.Container:
        """Constrói o formulário de Categoria de Clientes"""
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
                ft.Text("Identificação do Cliente", size=16),
                ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
                responsive_row(
                    controls=[self.first_name, self.last_name, self.email]),
                ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
                ft.ResponsiveRow(controls=[self.cpf, self.phone, self.is_whatsapp_check,
                                 self.birthday], columns=12, expand=True, spacing=20, run_spacing=20),
                ft.Divider(height=15, color=ft.Colors.TRANSPARENT),
                ft.Divider(height=5),
                ft.Text("Endereço de entrega", size=16),
                responsive_row(
                    controls=[self.street, self.number, self.complement]),
                ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
                responsive_row(
                    controls=[self.neighborhood, self.city, self.state, self.postal_code]),
                ft.Divider(height=15, color=ft.Colors.TRANSPARENT),
                ft.Divider(height=5),
                ft.Container(
                    self.status, alignment=ft.alignment.center_right, expand=True),
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

    def did_mount(self):
        if self.data and self.data.get('id'):
            # Preenche os campos com os dados fiscais da empresa
            self.populate_form_fields()
        self.page.update()

    def populate_form_fields(self):
        """Preenche os campos do formulário com os dados do cliente"""
        user_name = self.data["name"]
        self.first_name.value = user_name.first_name if user_name.first_name else ""
        self.last_name.value = user_name.last_name if user_name.last_name else ""
        self.email.value = self.data["email"]
        self.cpf.value = self._apply_cpf_mask(self.data.get("cpf", ""))
        self.phone.value = self.data.get("phone", "")
        self.is_whatsapp_check.value = self.data.get("is_whatsapp", False)

        # Converte o objeto 'date' do modelo para uma string 'DD/MM' para a UI
        birthday_date = self.data.get("birthday")
        if isinstance(birthday_date, datetime):
            # Formata a data para o formato DD/MM
            self.birthday.value = birthday_date.strftime('%d/%m')

        if address := self.data.get("delivery_address"):
            self.street.value = address.street
            self.number.value = address.number
            self.complement.value = address.complement
            self.neighborhood.value = address.neighborhood
            self.city.value = address.city
            self.state.value = address.state
            self.postal_code.value = address.postal_code

        status = self.data.get("status", RegistrationStatus.ACTIVE)

        if status == RegistrationStatus.ACTIVE:
            self.status.value = True
            self.status.label = "Cliente Ativo"
        else:
            self.status.value = False
            self.status.label = "Cliente Inativo"

    def _is_valid_day_month(self, dd_mm_str: str) -> bool:
        """
        Verifica se a string DD/MM corresponde a um dia e mês válidos.
        """
        try:
            day = int(dd_mm_str[:2])
            month = int(dd_mm_str[3:])
            # Usamos um ano bissexto para cobrir 29 de fevereiro
            datetime(year=2000, month=month, day=day)
            return True
        except ValueError:
            return False

    def get_form_object_updated(self) -> Cliente:
        """Atualiza self.data com os dados do formulário e o retorna atualizado."""
        client_name = NomePessoa(first_name=self.first_name.value, last_name=self.last_name.value)

        self.data['name'] = client_name
        self.data["email"] = self.email.value
        self.data["cpf"] = self.cpf.value
        self.data["phone"] = self.phone.value
        self.data["is_whatsapp"] = self.is_whatsapp_check.value

        birthday_str = self.birthday.value
        birthday_date = None

        # Converte a string 'DD/MM' da UI de volta para um objeto 'date' para o modelo
        if birthday_str and self._validate_birthday_format(birthday_str):
            try:
                # Usa um ano bissexto (2000) para validar e armazenar, garantindo que 29/02 seja aceito.
                birthday_date = datetime.strptime(
                    f"{birthday_str}/2000", '%d/%m/%Y'
                ).date() # Converte para objeto date para evitar problemas de fuso horário
            except ValueError:
                birthday_date = None  # Garante que datas inválidas não quebrem a aplicação

        self.data["birthday"] = birthday_date  # Armazena o objeto date ou None

        if self.street.value and self.number.value and self.neighborhood.value and self.city.value and self.state.value and self.postal_code.value:
            self.data["delivery_address"] = Address(
                street=self.street.value,
                number=self.number.value,
                complement=self.complement.value,
                neighborhood=self.neighborhood.value,
                city=self.city.value,
                state=self.state.value,
                postal_code=self.postal_code.value,
            )

        self.data['status'] = RegistrationStatus.ACTIVE if self.status.value else RegistrationStatus.INACTIVE

        if not self.data.get("empresa_id"):
            self.data["empresa_id"] = self.empresa_logada["id"]

        return Cliente.from_dict(self.data)

    def validate_form(self) -> str | None:
        """Valida os campos do formulário. Retorna uma mensagem de erro se algum campo obrigatório não estiver preenchido."""
        if not self.first_name.value:
            return "Por favor, preencha o nome do cliente."
        if not self.phone.value:
            return "Por favor, preencha o telefone do cliente."
        if self.birthday.value and not self._validate_birthday_format(self.birthday.value):
            return "Formato de aniversário inválido. Use DD/MM."

        # Lista de campos de endereço e suas respectivas mensagens de erro
        address_fields_with_messages = [
            (self.street.value, "Por favor, preencha o endereço do cliente."),
            (self.number.value, "Por favor, preencha o número do endereço do cliente."),
            (self.neighborhood.value, "Por favor, preencha o bairro do endereço do cliente."),
            (self.city.value, "Por favor, preencha a cidade do endereço do cliente."),
            (self.state.value, "Por favor, preencha o estado do endereço do cliente."),
            (self.postal_code.value, "Por favor, preencha o CEP do endereço do cliente.")
        ]

        # Verifica se *qualquer* campo de endereço foi preenchido
        if any(value for value, _ in address_fields_with_messages):
            # Se algum campo foi preenchido, todos os campos obrigatórios devem estar preenchidos
            for value, message in address_fields_with_messages:
                if not value:
                    return message

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
        self.phone.text_size = self.font_size
        self.cpf.text_size = self.font_size
        self.birthday.text_size = self.font_size

        # Atualiza o padding do container
        self.form.padding = self.padding
        self.form.update()

    def build(self) -> ft.Container:
        return self.form

    def clear_form(self):
        """Limpa os campos do formulário"""
        for field in self.__dict__.values():
            if isinstance(field, ft.TextField):
                field.value = ''
            if isinstance(field, ft.Switch):
                field.value = True  # Por default, o status é ativo
            if isinstance(field, ft.Checkbox):
                field.value = False  # Por default, o "tem whatsapp" é False

        # Limpa o buffer com os dados de clientes carregados
        self.data = {}


# Rota: /home/clientes/form
def show_client_form(page: ft.Page):
    """Página de cadastro de usuarios."""
    route_title = "home/clientes/form"
    cliente_data = page.app_state.form_data  # type: ignore

    if id := cliente_data.get("id"):
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
                on_click=lambda _: page.back(),  # type: ignore [attr-defined]
                tooltip="Voltar",
                # Ajuda a garantir que o hover respeite o border_radius
                clip_behavior=ft.ClipBehavior.ANTI_ALIAS
            ),
        ),
        title=ft.Text(route_title, size=18, selectable=True),
        bgcolor=ft.Colors.with_opacity(0.9, ft.Colors.PRIMARY_CONTAINER),
        adaptive=True,
    )

    clientes_view = ClienteForm(page=page)
    clientes_view.did_mount()
    form_container = clientes_view.build()

    def save_form_clientes(e):
        # Valida os dados do formulário
        if msg := clientes_view.validate_form():
            message_snackbar(
                page=page, message=msg, message_type=MessageType.WARNING)
            return

        # Desabilita o botão de salvar para evitar múltiplos cliques
        save_btn.disabled = True

        # Cria o gerenciador de mensagens progressivas
        progress_msg = ProgressiveMessage(page)

        try:
            # Primeira etapa: Salvando cliente
            progress_msg.show_progress("Salvando cliente...")

            # Instância do objeto Cliente com os dados do formulário para enviar para o backend
            cliente: Cliente = clientes_view.get_form_object_updated()

            # Envia os dados para o backend
            result = client_controllers.handle_save(
                cliente=cliente,
                usuario_logado=page.app_state.usuario # type: ignore  [attr-defined]
            )

            # Segunda etapa: Salvando no banco
            progress_msg.update_progress("Finalizando cadastro...")

            if result["status"] == "error":
                print(f"Debug  -> {result['message']}")
                progress_msg.show_error(result["message"])
                save_btn.disabled = False
                return

            clientes_view.clear_form()
            page.back()  # type: ignore [attr-defined]

        except Exception as ex:
            # Em caso de erro inesperado
            print(f"Debug  -> Erro inesperado: {str(ex)}")
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

    def exit_form_clientes(e):
        # Limpa o formulário sem salvar e volta para à página anterior que a invocou
        clientes_view.clear_form()
        page.back()  # type: ignore [attr-defined]

    # Adiciona os botões "Salvar" & "Cancelar"
    save_btn = ft.ElevatedButton(
        text="Salvar", col={'xs': 5, 'md': 5, 'lg': 5}, on_click=save_form_clientes)
    exit_btn = ft.ElevatedButton(
        text="Cancelar", col={'xs': 5, 'md': 5, 'lg': 5}, on_click=exit_form_clientes)
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
