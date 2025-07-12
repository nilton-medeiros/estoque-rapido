import flet as ft
from src.pages.partials import build_input_field
from src.pages.shared.dialog_search import DialogSearch


class PedidoItemsSubform:
    """Subformulário para gerenciar os itens do pedido"""

    def __init__(self, page: ft.Page, app_colors: dict, products: list, on_items_change=None):
        self.page = page
        self.app_colors = app_colors
        self.products = products
        self.on_items_change = on_items_change  # Callback para notificar mudanças
        self.new_item_id = ''
        self.new_item_unit_of_measure = ""
        self.new_item_quantity_on_hand = 0
        self.items: list[dict] = []  # Lista de itens do pedido

        # Componentes do subformulário
        self.items_container = ft.Column(spacing=20, scroll=ft.ScrollMode.AUTO)
        self.total_display = ft.Text("Total: R$ 0,00", size=16, weight=ft.FontWeight.BOLD)

        # Campos do formulário de novo item
        self._create_new_item_fields()

        # Container principal
        self.container = self._build_container()

        # Atualiza a exibição inicial para mostrar a mensagem de lista vazia
        self._update_items_display()

    def _handle_product_selection(self, selected_item):
        """Callback para selecionar um produto"""
        self.new_item_id = selected_item["id"]
        self.new_item_description.value = selected_item["description"]
        # Converte o Decimal para string no formato esperado (com vírgula)
        self.new_item_unit_price.value = f"{selected_item['price']:.2f}".replace('.', ',')
        self.new_item_quantity_on_hand = selected_item["quantity_on_hand"]   # Quantidade disponível no estoque
        self.new_item_unit_of_measure = selected_item["unit_of_measure"]    # Unidade de Medida
        self.new_item_description.update()
        self.new_item_unit_price.update()
        self.new_item_quantity.value="1"
        self.new_item_quantity.counter_text=f"Estoque: {self.new_item_quantity_on_hand}"
        self.new_item_quantity.update()
        # Define o foco para o campo de quantidade
        self.new_item_quantity.focus()
        self._calculate_item_total()

    def _create_new_item_fields(self):
        """Cria os campos para adicionar um novo item"""

        # Função para manipular o evento de hover
        def handle_button_hover(e, button):
            """Altera a cor de fundo do botão no hover"""
            if e.data == "true":  # Mouse entra
                button.bgcolor = ft.Colors.with_opacity(0.8, self.app_colors.get("primary", ft.Colors.BLUE))
            else:  # Mouse sai
                button.bgcolor = self.app_colors.get("primary", ft.Colors.BLUE)
            button.update()

        # AlertDialog para selecionar produtos
        dialog_search = DialogSearch(
            page=self.page,
            items=self.products,
            hint_text="Selecione ou busque um produto...",
            on_select_callback=self._handle_product_selection,
        )

        # Botão de selecionar produtos
        self.select_products_btn = ft.ElevatedButton(
            text="Selecionar Produtos",
            icon=ft.Icons.SEARCH,
            col={'xs': 8, 'md': 8, 'lg': 8},
            on_click=lambda e: dialog_search.show(),
            bgcolor=self.app_colors.get("primary", ft.Colors.BLUE),
            color=ft.Colors.WHITE,
            on_hover=lambda e: handle_button_hover(e, self.select_products_btn),
        )

        # Produto/Descrição
        self.new_item_description = build_input_field(
            page_width=self.page.width if self.page.width else 600,
            app_colors=self.app_colors,
            col={'xs': 12, 'md': 6, 'lg': 4},
            label="Produto/Descrição",
            icon=ft.Icons.INVENTORY_2,
            hint_text="Nome do produto",
            read_only=True,
        )

        # Quantidade
        self.new_item_quantity = build_input_field(
            page_width=self.page.width if self.page.width else 600,
            app_colors=self.app_colors,
            col={'xs': 6, 'md': 3, 'lg': 2},
            label="Quantidade",
            icon=ft.Icons.NUMBERS,
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=self._calculate_item_total,
            counter_text=f"Estoque: {self.new_item_quantity_on_hand}",
        )

        # Valor Unitário
        self.new_item_unit_price = build_input_field(
            page_width=self.page.width if self.page.width else 600,
            app_colors=self.app_colors,
            col={'xs': 6, 'md': 3, 'lg': 2},
            label="Valor Unit. (R$)",
            icon=ft.Icons.ATTACH_MONEY,
            keyboard_type=ft.KeyboardType.NUMBER,
            hint_text="0,00",
            on_change=self._calculate_item_total,
        )

        # Total do Item (calculado automaticamente)
        self.new_item_total = build_input_field(
            page_width=self.page.width if self.page.width else 600,
            app_colors=self.app_colors,
            col={'xs': 6, 'md': 6, 'lg': 2},
            label="Total Item (R$)",
            icon=ft.Icons.CALCULATE,
            read_only=True,
            hint_text="0,00",
        )

        # Botão para adicionar item
        self.add_item_btn = ft.ElevatedButton(
            text="Adicionar Item",
            icon=ft.Icons.ADD,
            col={'xs': 5, 'md': 3, 'lg': 2},
            on_click=self._add_item,
            bgcolor=self.app_colors.get("primary", ft.Colors.BLUE),
            color=ft.Colors.WHITE,
            on_hover=lambda e: handle_button_hover(e, self.add_item_btn),
        )

    def _calculate_item_total(self, e=None):
        """Calcula o total do item baseado na quantidade e valor unitário"""
        _quantity = int(self.new_item_quantity.value or 0)
        self.add_item_btn.disabled = _quantity > self.new_item_quantity_on_hand
        self.add_item_btn.bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.RED_300) if self.add_item_btn.disabled else self.app_colors.get("primary", ft.Colors.BLUE)

        color = ft.Colors.RED if self.add_item_btn.disabled else ft.Colors.GREEN
        self.new_item_quantity.counter_style = ft.TextStyle(color=color, weight=ft.FontWeight.W_500)
        self.new_item_quantity.update()

        try:
            quantity = float(self.new_item_quantity.value or 0)
            _unit_price = self.new_item_unit_price.value or "0,00"
            unit_price = float(_unit_price.replace(',', '.') or 0)
            total = quantity * unit_price
            self.new_item_total.value = f"{total:.2f}".replace('.', ',')
        except ValueError:
            self.new_item_total.value = "0,00"

        self.new_item_total.update()
        self.add_item_btn.update()

    def _add_item(self, e):
        """Adiciona um novo item à lista"""
        # Validação básica
        if not self.new_item_description.value:
            self._show_error("Descrição do produto é obrigatória")
            return

        if not self.new_item_quantity.value or float(self.new_item_quantity.value) <= 0:
            self._show_error("Quantidade deve ser maior que zero")
            return

        if not self.new_item_unit_price.value or float(self.new_item_unit_price.value.replace(',', '.')) <= 0:
            self._show_error("Valor unitário deve ser maior que zero")
            return

        # Verifica se o produto já foi adicionado em self.items
        if any(item['id'] == self.new_item_id for item in self.items):
            self._show_error("Produto já adicionado")
            return

        # Cria o item
        item = {
            'id': self.new_item_id,
            'description': self.new_item_description.value,
            'quantity': float(self.new_item_quantity.value),  # Quantidade de compra
            'quantity_on_hand': self.new_item_quantity_on_hand,    # Quantidade disponível no estoque
            'unit_price': float(self.new_item_unit_price.value.replace(',', '.')),  # Preço de venda por unidade
            'unit_of_measure': self.new_item_unit_of_measure,   # Unidade de Medida
            'total': float(self.new_item_quantity.value) * float(self.new_item_unit_price.value.replace(',', '.'))
        }

        # Adiciona à lista
        self.items.append(item)

        # Limpa os campos
        self._clear_new_item_fields()

        # Atualiza a exibição
        self._update_items_display()
        self._update_total()

        # Notifica sobre a mudança
        if self.on_items_change:
            self.on_items_change(self.items)

    def _clear_new_item_fields(self):
        """Limpa os campos do novo item"""
        self.new_item_description.value = ""
        self.new_item_quantity.value = ""
        self.new_item_unit_price.value = ""
        self.new_item_total.value = "0,00"
        self.page.update()

    def _remove_item(self, item_id):
        """Remove um item da lista"""
        def remove_handler(e):
            self.items = [item for item in self.items if item['id'] != item_id]
            self._update_items_display()
            self._update_total()
            if self.on_items_change:
                self.on_items_change(self.items)
        return remove_handler

    def _edit_item(self, item_id):
        """Edita um item existente"""
        def edit_handler(e):
            # Encontra o item
            item = next((item for item in self.items if item['id'] == item_id), None)
            if not item:
                return

            # Preenche os campos com os dados do item
            self.new_item_description.value = item['description']
            self.new_item_quantity.value = str(item['quantity'])
            self.new_item_unit_price.value = f"{item['unit_price']:.2f}".replace('.', ',')
            self.new_item_total.value = f"{item['total']:.2f}".replace('.', ',')

            # Remove o item da lista (será re-adicionado quando salvar)
            self.items = [i for i in self.items if i['id'] != item_id]
            self._update_items_display()
            self._update_total()

            self.page.update()
        return edit_handler

    def _create_item_card(self, item):
        """Cria um card para exibir um item"""
        return ft.Card(
            content=ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Column(
                            controls=[
                                ft.Text(item['description'], weight=ft.FontWeight.BOLD, size=14),
                                ft.Text(f"Qtd: {item['quantity']:.0f} | Unit: R$ {item['unit_price']:.2f}", size=12),
                            ],
                        ),
                        ft.Column(
                            controls=[
                                ft.Text(f"R$ {item['total']:.2f}", weight=ft.FontWeight.BOLD, size=14),
                                ft.Row(
                                    controls=[
                                        ft.IconButton(
                                            icon=ft.Icons.EDIT,
                                            icon_size=16,
                                            on_click=self._edit_item(item['id']),
                                            tooltip="Editar",
                                        ),
                                        ft.IconButton(
                                            icon=ft.Icons.DELETE,
                                            icon_size=16,
                                            icon_color=ft.Colors.RED,
                                            on_click=self._remove_item(item['id']),
                                            tooltip="Remover",
                                        ),
                                    ],
                                    spacing=5,
                                ),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.END,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                padding=10,
            ),
            margin=ft.margin.all(0),# Removido margin=5 para evitar interferência
            elevation=2,  # Adiciona uma leve elevação para melhor distinção visual
        )

    def _update_items_display(self):
        """Atualiza a exibição dos itens"""
        self.items_container.controls.clear()

        if not self.items:
            self.items_container.controls.append(
                ft.Container(
                    content=ft.Text(
                        "Nenhum item adicionado",
                        color=ft.Colors.GREY_500,
                        italic=True,
                    ),
                    padding=20,
                    alignment=ft.alignment.center,
                )
            )
        else:
            for item in self.items:
                self.items_container.controls.append(self._create_item_card(item))

        # Atualiza a altura do container pai
        self.items_container_container.height = 100 if not self.items else 300
        if self.items_container_container.page:
            self.items_container_container.update()

        if self.items_container.page:
            self.items_container.update()

    def _update_total(self):
        """Atualiza o valor total dos itens"""
        total = sum(item['total'] for item in self.items)
        self.total_display.value = f"Total: R$ {total:.2f}"
        if self.total_display.page:
            self.total_display.update()

    def _show_error(self, message):
        """Exibe uma mensagem de erro"""
        # Integração com seu sistema de mensagens
        try:
            import src.shared.utils.messages as messages
            messages.message_snackbar(
                page=self.page,
                message=message,
                message_type=messages.MessageType.ERROR
            )
        except ImportError:
            # Fallback se o módulo não estiver disponível
            print(f"Erro: {message}")

    def _build_container(self):
        """Constrói o container principal do subformulário"""

        # Seção de adição de novos itens
        new_item_section = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("Adicionar Item", size=16, weight=ft.FontWeight.BOLD),
                        ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
                        self.select_products_btn,
                        ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
                        ft.ResponsiveRow(
                            columns=12,
                            spacing=10,
                            run_spacing=10,
                            controls=[
                                self.new_item_description,
                                self.new_item_quantity,
                                self.new_item_unit_price,
                                self.new_item_total,
                                self.add_item_btn,
                            ],
                        ),
                    ],
                    spacing=10,
                ),
                padding=15,
            ),
            margin=5,
        )

        # Seção de exibição dos itens
        self.items_container_container = ft.Container(
            content=self.items_container,
            height=100 if not self.items else 300,  # Altura dinâmica
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=8,
            padding=10,
        )

        items_section = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text("Itens do Pedido", size=16, weight=ft.FontWeight.BOLD),
                                ft.Container(expand=True),
                                self.total_display,
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
                        self.items_container_container,
                    ],
                    spacing=10,
                ),
                padding=15,
            ),
            margin=5,
        )

        return ft.Column(
            controls=[
                new_item_section,
                items_section,
            ],
            spacing=10,
        )

    def get_items(self) -> list[dict]:
        """Retorna a lista de itens"""
        return self.items.copy()

    def set_items(self, items: list[dict]):
        """Define os itens do pedido"""
        self.items = items.copy()
        self._update_items_display()
        self._update_total()

    def clear_items(self):
        """Limpa todos os itens"""
        self.items.clear()
        self._clear_new_item_fields()
        self._update_items_display()
        self._update_total()

    def get_total_amount(self) -> float:
        """Retorna o valor total dos itens"""
        return sum(item['total'] for item in self.items)

    def get_total_quantity(self) -> float:
        """Retorna a quantidade total de itens"""
        return len(self.items)

    def get_total_products(self) -> int:
        """Retorna o número total de produtos"""
        return sum(item['quantity'] for item in self.items)

    def build(self) -> ft.Column:
        """Retorna o container do subformulário"""
        return self.container