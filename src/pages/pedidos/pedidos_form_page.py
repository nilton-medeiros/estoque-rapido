import logging
import re  # Adicionado para expressões regulares

import flet as ft
from datetime import datetime  # Adicionado para validação de data

from src.domains.clientes.controllers.clientes_controllers import handle_get_by_name_cpf_or_phone
from src.domains.clientes.models.clientes_model import Cliente
from src.domains.pedidos.models.pedidos_model import Pedido
from src.domains.pedidos.models.pedidos_subclass import DeliveryStatus
from src.domains.shared import RegistrationStatus
from src.domains.shared.models.address import Address
from src.pages.partials import build_input_field
from src.pages.partials.responsive_sizes import get_responsive_sizes
from src.pages.pedidos.pedido_items_subform import PedidoItemsSubform
from src.shared.config import get_app_colors

import src.domains.pedidos.controllers.pedidos_controllers as order_controllers
import src.shared.utils.messages as messages

logger = logging.getLogger(__name__)


class PedidoForm:
    def __init__(self, page: ft.Page):
        self.page = page
        self.empresa_logada = page.app_state.empresa  # type: ignore [attr-defined]
        self.data = page.app_state.form_data  # type: ignore [attr-defined] dados do pedido, se houver.
        # Campos de redimencionamento do formulário
        self.font_size = 18
        self.icon_size = 24
        self.padding = 50
        self.app_colors: dict[str, str] = get_app_colors('blue')

        # * page.session é um objeto que contém o método .get(), não confundir com um dict *
        if page.session.get("user_colors"):
            self.app_colors: dict[str, str] = page.session.get(
                "user_colors")  # type: ignore [attr-defined]

        self.input_width = 400

        # Responsividade
        self._create_form_fields()

        # Inicializa o subformulário de itens
        self.items_subform = PedidoItemsSubform(
            page=self.page,
            app_colors=self.app_colors,
            on_items_change=self._on_items_change
        )

        self.form = self.build_form()
        self.page.on_resized = self._page_resize

    def on_change_status(self, e):
        status = e.control
        status.label = "Pedido Ativo" if e.data == "true" else "Pedido Inativo"
        status.update()

    def on_change_delivery_status(self, e):
        delivery_index = e.control.selected_index

        match delivery_index:
            case 0:
                e.control.thumb_color = ft.Colors.AMBER_900
            case 1:
                e.control.thumb_color = ft.Colors.GREEN_900
            case 2:
                e.control.thumb_color = ft.Colors.BLUE_900
            case 3:
                e.control.thumb_color = ft.Colors.RED_900
            case _:
                e.control.thumb_color = ft.Colors.AMBER_900

        e.control.update()

    def _on_items_change(self, items):
        """Callback chamado quando os itens são alterados"""
        # Atualiza os campos de totais automaticamente
        self.total_amount.value = f"{self.items_subform.get_total_amount():.2f}"
        self.quantity_items.value = str(int(self.items_subform.get_total_quantity()))
        self.quantity_products.value = str(self.items_subform.get_total_products())

        # Atualiza a interface
        self.total_amount.update()
        self.quantity_items.update()
        self.quantity_products.update()


    def _create_form_fields(self):
        """Cria os campos do formulário de Pedido"""

        # Identificação do Pedido ---------------------------------------------
        # Primeiro responsive row
        # Número do Pedido
        self.order_number = build_input_field(
            page_width=self.page.width,  # type: ignore [attr-defined]
            app_colors=self.app_colors,
            col={'xs': 12, 'md': 4, 'lg': 4},
            label="Pedido Nº",
            icon=ft.Icons.NUMBERS,
            read_only=True,
        )
        # Total do pedido
        self.total_amount = build_input_field(
            page_width=self.page.width, # type: ignore [attr-defined]
            app_colors=self.app_colors,
            col={'xs': 12, 'md': 4, 'lg': 4},
            label="Total Pedido",
            icon=ft.Icons.ATTACH_MONEY,
            read_only=True,
        )
        # Quantidade de Itens
        self.quantity_items = build_input_field(
            page_width=self.page.width, # type: ignore [attr-defined]
            app_colors=self.app_colors,
            col={'xs': 12, 'md': 4, 'lg': 4},
            label="Total Itens",
            icon=ft.Icons.NUMBERS,
            read_only=True,
        )

        # Segundo responsive row
        # Quantidade de Produtos
        self.quantity_products = build_input_field(
            page_width=self.page.width, # type: ignore [attr-defined]
            app_colors=self.app_colors,
            col={'xs': 12, 'md': 4, 'lg': 4},
            label="Qtde. Produtos",
            icon=ft.Icons.NUMBERS,
            read_only=True,
        )
        # Status do Pedido: Switch Ativo/Inativo
        self.status = ft.Switch(
            col={'xs': 12, 'md': 2, 'lg': 2},
            label="Pedido Ativo",
            value=True,
            on_change=self.on_change_status,
        )
        # Status de Entrega
        self.delivery_status = ft.CupertinoSlidingSegmentedButton(
            selected_index=0,
            thumb_color=ft.Colors.AMBER_900,
            padding=ft.padding.symmetric(0, 10),
            controls=[ft.Text(delivery.value) for delivery in DeliveryStatus],
            on_change=self.on_change_delivery_status,
        )
        self.entrega_column = ft.Column(
            col={'xs': 12, 'md': 6, 'lg': 6},
            alignment=ft.MainAxisAlignment.START,
            spacing=20,
            run_spacing=20,
            controls=[
                ft.Text("Status de Entrega", size=16),
                ft.Divider(height=5),
                self.delivery_status,
            ],
        )

        # Identificação do Cliente (Opcional) ---------------------------------
        # Filtro para Consultar Cliente
        self.consult_client = build_input_field(
            page_width=self.page.width,  # type: ignore [attr-defined]
            app_colors=self.app_colors,
            col={'xs': 8, 'md': 6, 'lg': 4},
            label="Consultar Cliente",
            icon=ft.Icons.SEARCH,
            counter_text="Nome, CPF ou Celular",
        )
        self.consult_client_btn = ft.IconButton(
            col={'xs': 4, 'md': 2, 'lg': 2},
            icon=ft.Icons.SEARCH,
            icon_size=self.icon_size,
            tooltip="Consultar CNPJ",
            disabled=True,
            on_click=self._consult_client
        )
        # CPF
        self.client_cpf = build_input_field(
            page_width=self.page.width,  # type: ignore [attr-defined]
            app_colors=self.app_colors,
            col={'xs': 12, 'md': 4, 'lg': 4},
            label="CPF",
            hint_text="123.456.789-00",
            keyboard_type=ft.KeyboardType.NUMBER,
            max_length=14,  # 11 dígitos + 2 pontos + 1 traço
            icon=ft.Icons.BADGE_OUTLINED,
            counter_text="Opcional",
            on_change=self._handle_cpf_change,
        )

        sizes = get_responsive_sizes(self.page.width)

        # Dia e mês de aniversário
        self.client_birthday = ft.TextField(
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

        # Cliente (Opcional)
        self.client_name = build_input_field(
            page_width=self.page.width,  # type: ignore [attr-defined]
            app_colors=self.app_colors,
            col={'xs': 12, 'md': 12, 'lg': 4},
            label="Nome do Cliente",
            icon=ft.Icons.PERSON_3,
        )
        # Email do Cliente
        self.client_email = build_input_field(
            page_width=self.page.width,  # type: ignore [attr-defined]
            app_colors=self.app_colors,
            col={'xs': 12, 'md': 12, 'lg': 4},
            label="Email",
            keyboard_type=ft.KeyboardType.EMAIL,
            icon=ft.Icons.EMAIL_OUTLINED,
        )
        # Celular
        self.client_phone = build_input_field(
            page_width=self.page.width,  # type: ignore [attr-defined]
            app_colors=self.app_colors,
            col={'xs': 12, 'md': 6, 'lg': 3},
            label="Celular",
            hint_text="(11) 98765-4321",  # Atualizado para refletir a máscara
            keyboard_type=ft.KeyboardType.NUMBER,  # Define o teclado numérico
            max_length=15,  # (XX) XXXXX-XXXX tem 15 caracteres
            icon=ft.Icons.CONTACT_PHONE_OUTLINED,
            on_change=self._handle_phone_change,  # Adiciona o handler de mudança
        )
        self.client_is_whatsapp_check = ft.Checkbox(
            col={'xs': 12, 'md': 6, 'lg': 1},
            label="WhatsApp",
        )

        # Endereço
        self.client_street = build_input_field(
            page_width=self.page.width,  # type: ignore
            app_colors=self.app_colors,
            col={'xs': 12, 'md': 12, 'lg': 6},
            label="Rua",
            icon=ft.Icons.LOCATION_ON,
        )
        self.client_number = build_input_field(
            page_width=self.page.width,  # type: ignore
            app_colors=self.app_colors,
            col={'xs': 12, 'md': 6, 'lg': 2},
            label="Número",
            icon=ft.Icons.NUMBERS,
        )
        self.client_complement = build_input_field(
            page_width=self.page.width,  # type: ignore
            app_colors=self.app_colors,
            col={'xs': 12, 'md': 6, 'lg': 4},
            label="Complemento",
            icon=ft.Icons.ADD_LOCATION,
            hint_text="Apto 101",
            hint_fade_duration=5,
        )
        self.client_neighborhood = build_input_field(
            page_width=self.page.width,  # type: ignore
            app_colors=self.app_colors,
            col={'xs': 12, 'md': 6, 'lg': 4},
            label="Bairro",
            icon=ft.Icons.LOCATION_CITY,
        )
        self.client_city = build_input_field(
            page_width=self.page.width,  # type: ignore
            app_colors=self.app_colors,
            col={'xs': 12, 'md': 6, 'lg': 3},
            label="Cidade",
            icon=ft.Icons.LOCATION_CITY,
            hint_text="São Paulo",
            hint_fade_duration=5,
        )
        self.client_state = build_input_field(
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
        self.client_postal_code = build_input_field(
            page_width=self.page.width,  # type: ignore
            app_colors=self.app_colors,
            col={'xs': 12, 'md': 6, 'lg': 3},
            label="CEP",
            icon=ft.Icons.LOCATION_CITY,
            hint_text="00000-000",
            hint_fade_duration=5,
        )

        # self.order_items será gerenciado pelo subformulário

    def _handle_consult_client_change(self, e) -> None:
        """Atualiza o estado do botão de consulta de clientes baseado no valor do campo de consulta"""
        self.consult_client_btn.disabled = not self.consult_client.value
        self.consult_client_btn.update()

    def _consult_client(self, e) -> None:
        research_data = self.consult_client.value
        if not research_data or len(research_data.strip()) < 3:
            return
        research_data = research_data.strip()
        result = handle_get_by_name_cpf_or_phone(self.empresa_logada["id"], research_data)

        if result["status"] == "error":
            messages.message_snackbar(
                page=self.page, message=result["message"], message_type=messages.MessageType.ERROR)
            return

        clientes_list = result["data"]

        if len(clientes_list) == 0:
            messages.show_banner(self.page, "Nenhum cliente encontrado", "Fechar")
            return
        elif len(clientes_list) == 1:
            cliente = clientes_list[0]
        else:
            # Mais de um cliente encontrado, pedir para o usuário escolher um deles
            cliente = self.select_a_client(clientes_list)

        if not cliente:
            messages.show_banner(self.page, "Nenhum cliente selecionado", "Fechar")
            return

        self.populate_client_fields(cliente)

    def populate_client_fields(self, cliente) -> None:
        self.client_name.value = f"{cliente.nome.first_name} {cliente.nome.last_name}"
        self.client_cpf.value = cliente.cpf
        self.client_phone.value = cliente.phone
        self.client_email.value = cliente.email
        self.client_is_whatsapp_check.value = cliente.is_whatsapp
        self.client_birthday.value = cliente.birthday
        self.client_street.value = cliente.endereco.street
        self.client_number.value = cliente.endereco.number
        self.client_complement.value = cliente.endereco.complement
        self.client_neighborhood.value = cliente.endereco.neighborhood
        self.client_city.value = cliente.endereco.city
        self.client_state.value = cliente.endereco.state
        self.client_postal_code.value = cliente.endereco.postal_code
        self.page.update()
        return

    def select_a_client(self, clientes) -> Cliente | None:
        """
        Abre uma interface ui para o usuário escolher um cliente da lista de clientes.

        Args:
            clientes (list): Lista de objetos Cliente.

        Returns:
            Cliente: Cliente selecionado pelo usuário ou None se usuário desistir (Cancelar).
        """
        # ToDo: Implementar este método para obter do usuário uma das empresas da lista de objetos do tipo Clientes do argumento clientes
        pass

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
        """Constrói o formulário de Pedidos"""
        def responsive_row(controls):
            return ft.ResponsiveRow(
                columns=12,
                expand=True,
                # alignment=ft.MainAxisAlignment.START,
                spacing=20,
                run_spacing=20,
                controls=controls,
            )

        client_identifications = ft.ExpansionTile(
            title=ft.Text("Dados do Cliente"),
            subtitle=ft.Text("Identificação do cliente ou NFCe (Opcional)"),
            affinity=ft.TileAffinity.LEADING,
            collapsed_text_color=self.app_colors["primary"],
            text_color=self.app_colors["container"],
            controls=[
                ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                responsive_row(controls=[self.consult_client, self.consult_client_btn, self.client_cpf, self.client_birthday]),
                ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                responsive_row(controls=[self.client_name, self.client_email, self.client_phone, self.client_is_whatsapp_check]),
                ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                ft.Divider(height=5),
                ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                ft.Text("Endereço de entrega", size=16),
                ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                responsive_row(controls=[self.client_street, self.client_number, self.client_complement]),
                ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                responsive_row(controls=[self.client_neighborhood, self.client_city, self.client_state, self.client_postal_code]),
                ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            ],
            expanded_cross_axis_alignment=ft.CrossAxisAlignment.START,
        )

        # ExpansionTile para os itens do pedido
        items_section = ft.ExpansionTile(
            title=ft.Text("Itens do Pedido"),
            subtitle=ft.Text("Adicione produtos ao pedido"),
            affinity=ft.TileAffinity.LEADING,
            collapsed_text_color=self.app_colors["primary"],
            text_color=self.app_colors["container"],
            initially_expanded=True,  # Começa expandido
            controls=[
                ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                self.items_subform.build(),
                ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            ],
            expanded_cross_axis_alignment=ft.CrossAxisAlignment.START,
        )

        build_content = ft.Column(
            controls=[
                ft.Text("Identificação do Pedido", size=16),
                ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
                responsive_row(controls=[self.order_number, self.total_amount, self.quantity_items]),
                ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
                responsive_row(controls=[self.quantity_products, self.status, self.entrega_column]),
                ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
                client_identifications,
                ft.Divider(height=15, color=ft.Colors.TRANSPARENT),
                items_section,  # Substitui a linha antiga "Itens do Pedido"
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
        """Preenche os campos do formulário com os dados do pedido"""

        self.order_number.value = self.data["order_number"]
        self.total_amount.value = str(self.data["total_amount"])
        # self.quantity_items.value = str(len(self.data["items"]))
        # self.quantity_products.value = str(sum(item['quantity'] for item in self.data["items"]))
        self.quantity_items.value = str(self.data["total_items"])
        self.quantity_products.value = str(self.data["total_products"])

        index_status = {
            "PENDING": 0,
            "IN_TRANSIT": 1,
            "DELIVERED": 2,
            "CANCELED": 3,
        }

        status_data = self.data["delivery_status"]
        self.delivery_status.selected_index = index_status[status_data.name]

        self.status.value = self.data["status"] == RegistrationStatus.ACTIVE
        self.status.label = f"Pedido {str(self.data["status"])}"
        self.consult_client.value = ""
        self.consult_client_btn.disabled = True
        self.client_cpf.value = self.data.get("client_cpf", "")
        self.client_name.value = self.data.get("client_name", "")
        self.client_email.value = self.data.get("client_email", "")
        self.client_phone.value = self.data.get("client_phone", "")
        self.client_is_whatsapp_check.value = self.data.get("client_is_whatsapp", False)

        # Converte o objeto 'date' do modelo para uma string 'DD/MM' para a UI
        birthday_date = self.data.get("client_birthday")
        if isinstance(birthday_date, datetime):
            # Formata a data para o formato DD/MM
            self.client_birthday.value = birthday_date.strftime('%d/%m')

        if address := self.data.get("client_address"):
            self.client_street.value = address.street
            self.client_number.value = address.number
            self.client_complement.value = address.complement
            self.client_neighborhood.value = address.neighborhood
            self.client_city.value = address.city
            self.client_state.value = address.state
            self.client_postal_code.value = address.postal_code

        items_data = []
        for i, item in enumerate(self.data.get("items", [])):
            items_data.append({
                'id': i + 1,
                'description': item.get('description', ''),
                'quantity': item.get('quantity', 0),
                'unit_price': item.get('unit_price', 0),
                'total': item.get('total', 0)
            })

        self.items_subform.set_items(items_data)

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

    def get_form_object_updated(self) -> Pedido:
        """Atualiza self.data com os dados do formulário e o retorna atualizado."""
        index_status = {
            0: DeliveryStatus.PENDING,
            1: DeliveryStatus.IN_TRANSIT,
            2: DeliveryStatus.DELIVERED,
            3: DeliveryStatus.CANCELED,
        }
        self.data["delivery_status"] = index_status[self.delivery_status.selected_index]
        self.data["status"] = RegistrationStatus.ACTIVE if self.status.value else RegistrationStatus.INACTIVE
        self.data["client_cpf"] = self.client_cpf.value if self.client_cpf.value else None
        self.data['client_name'] = self.client_name.value if self.client_name.value else None
        self.data["client_email"] = self.client_email.value if self.client_email.value else None
        self.data["client_phone"] = self.client_phone.value if self.client_phone.value else None
        self.data["client_is_whatsapp"] = self.client_is_whatsapp_check.value

        birthday_str = self.client_birthday.value
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

        self.data["client_birthday"] = birthday_date  # Armazena o objeto date ou None

        if self.client_street.value and self.client_number.value and self.client_neighborhood.value and\
           self.client_city.value and self.client_state.value and self.client_postal_code.value:
            self.data["client_address"] = Address(
                street=self.client_street.value,
                number=self.client_number.value,
                complement=self.client_complement.value,
                neighborhood=self.client_neighborhood.value,
                city=self.client_city.value,
                state=self.client_state.value,
                postal_code=self.client_postal_code.value,
            )

        if not self.data.get("empresa_id"):
            self.data["empresa_id"] = self.empresa_logada["id"]

        items_data = []
        for item in self.items_subform.get_items():
            items_data.append({
                'description': item['description'],
                'quantity': item['quantity'],
                'unit_price': item['unit_price'],
                'total': item['total']
            })

        self.data["items"] = items_data

        # Atualiza o valor total baseado nos itens
        total_amount = self.items_subform.get_total_amount()
        self.data["total_amount"] = {"amount_cents": int(total_amount * 100)}

        # Atualiza as quantidades
        self.data["total_items"] = int(self.items_subform.get_total_quantity())
        self.data["total_products"] = self.items_subform.get_total_products()

        return Pedido.from_dict(self.data)

    def validate_form(self) -> str | None:
        """Valida os campos do formulário. Retorna uma mensagem de erro se algum campo obrigatório não estiver preenchido."""

        # Validação dos itens
        if not self.items_subform.get_items():
            return "Adicione pelo menos um item ao pedido."

        selected_index = self.delivery_status.selected_index
        if selected_index in [1, 2]:
            # Pedido entregue, verifica se há itens e valor para faturamento
            qtty_items = self.items_subform.get_total_products()
            qtty_products = int(self.items_subform.get_total_quantity())
            if qtty_items == 0 or qtty_products == 0:
                return "O Pedido não pode estar em trânsito ou entregue sem itens."

        if self.client_birthday.value and not self._validate_birthday_format(self.client_birthday.value):
            return "Formato de aniversário inválido. Use DD/MM."

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
        self.order_number.text_size = self.font_size
        self.total_amount.text_size = self.font_size
        self.quantity_items.text_size = self.font_size
        self.quantity_products.text_size = self.font_size
        self.consult_client.text_size = self.font_size
        self.client_cpf.text_size = self.font_size
        self.client_name.text_size = self.font_size
        self.client_email.text_size = self.font_size
        self.client_phone.text_size = self.font_size
        self.client_birthday.text_size = self.font_size
        self.client_street.text_size = self.font_size
        self.client_number.text_size = self.font_size
        self.client_complement.text_size = self.font_size
        self.client_neighborhood.text_size = self.font_size
        self.client_city.text_size = self.font_size
        self.client_state.text_size = self.font_size
        self.client_postal_code.text_size = self.font_size

        # Atualiza o padding do container
        self.form.padding = self.padding
        self.form.update()

    def build(self) -> ft.Container:
        return self.form

    def clear_form(self):
        """Limpa os campos do formulário"""
        for field in self.__dict__.values():
            if isinstance(field, ft.TextField):
                field.value = ""
            if isinstance(field, ft.Switch):
                field.value = True  # Por default, o status é ativo
            if isinstance(field, ft.Checkbox):
                field.value = False  # Por default, o "tem whatsapp" é False
            if isinstance(field, ft.CupertinoSlidingSegmentedButton):
                field.selected_index = 0  # Por default, o status é pendente

        # Limpa os itens do subformulário
        self.items_subform.clear_items()

        # Limpa o buffer com os dados de pedidos carregados
        self.data = {}

# Rota: /home/pedidos/form
def show_pedido_form(page: ft.Page):
    """Página de cadastro de usuarios."""
    route_title = "home/pedidos/form"
    pedido_data = page.app_state.form_data  # type: ignore

    if id := pedido_data.get("id"):
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

    pedidos_view = PedidoForm(page=page)
    pedidos_view.did_mount()
    form_container = pedidos_view.build()

    def save_form_pedidos(e):
        # Valida os dados do formulário
        if msg := pedidos_view.validate_form():
            messages.message_snackbar(
                page=page, message=msg, message_type=messages.MessageType.WARNING)
            return

        # Desabilita o botão de salvar para evitar múltiplos cliques
        save_btn.disabled = True

        # Cria o gerenciador de mensagens progressivas
        progress_msg = messages.ProgressiveMessage(page)

        try:
            # Primeira etapa: Salvando pedido
            progress_msg.show_progress("Salvando pedido...")

            # Instância do objeto Pedido com os dados do formulário para enviar para o backend
            pedido: Pedido = pedidos_view.get_form_object_updated()

            # Envia os dados para o backend
            result = order_controllers.handle_save_pedido(
                pedido=pedido,
                usuario_logado=page.app_state.usuario # type: ignore  [attr-defined]
            )

            # Segunda etapa: Salvando no banco
            progress_msg.update_progress("Finalizando cadastro...")

            if result["status"] == "error":
                print(f"Debug  -> {result['message']}")
                progress_msg.show_error(result["message"])
                save_btn.disabled = False
                return

            progress_msg.show_success("Pedido salvo com sucesso!")
            # Limpa o formulário e volta para a página anterior
            pedidos_view.clear_form()
            page.back()  # type: ignore [attr-defined]

        except Exception as ex:
            # Em caso de erro inesperado
            logger.error(f"Erro em get_form_object_updated ou handle_save_pedido: {str(ex)}")
            print(f"Debug  -> Erro: {str(ex)}")
            progress_msg.show_error(f"Erro: {str(ex)}")
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

    def exit_form_pedidos(e):
        # Limpa o formulário sem salvar e volta para à página anterior que a invocou
        pedidos_view.clear_form()
        page.back()  # type: ignore [attr-defined]

    # Adiciona os botões "Salvar" & "Cancelar"
    save_btn = ft.ElevatedButton(
        text="Salvar", col={'xs': 5, 'md': 5, 'lg': 5}, on_click=save_form_pedidos)
    exit_btn = ft.ElevatedButton(
        text="Cancelar", col={'xs': 5, 'md': 5, 'lg': 5}, on_click=exit_form_pedidos)
    space_between = ft.Container(col={'xs': 2, 'md': 2, 'lg': 2})

    form_page = ft.Column(
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
        route=page.route,
        controls=[form_page],
        appbar=appbar,
        bgcolor=ft.Colors.BLACK,
        scroll=ft.ScrollMode.AUTO,
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )
