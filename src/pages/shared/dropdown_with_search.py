import flet as ft

class DropdownSearch(ft.Row):
    def __init__(self, page: ft.Page, items: list, hint_text: str = 'Selecione uma opção!', on_change_callback=None, **kwargs):
        super().__init__(
            spacing=5,
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )

        # Armazena os dados originais
        self.page = page
        self.original_items = items
        self.item_descriptions = [item["description"] for item in items]
        self.on_change_callback = on_change_callback

        # Estado da busca
        self.is_searching = False
        self._value = None # Valor interno para a key

        # Configurações padrão do dropdown
        self.dropdown_config = {
            'filled': True,
            'dense': True,
            'border_radius': 20,
            'border_width': 3,
            'border_color': 'green',
            'text_size': 20,
            'text_style': ft.TextStyle(weight=ft.FontWeight.BOLD),
            'alignment': ft.alignment.top_left,
            'elevation': 20,
            'hint_text': hint_text,
            **kwargs
        }

        # --- Construção dos Componentes ---
        self.dropdown = ft.Dropdown(
            options=[
                ft.dropdown.Option(key=item["id"], text=item["description"])
                for item in self.original_items
            ],
            on_change=self.handle_dropdown_change,
            **self.dropdown_config
        )
        self.search_button = ft.IconButton(
            icon=ft.Icons.SEARCH,
            icon_size=20,
            icon_color=ft.Colors.GREEN,
            on_click=self.toggle_search,
            tooltip="Buscar item"
        )

        # Adiciona os controles à Row
        self.controls.append(ft.Container(content=self.dropdown, expand=True))
        self.controls.append(self.search_button)

    # --- Lógica de Busca ---
    def toggle_search(self, e):
        """Alterna para o modo de busca"""
        if not self.is_searching:
            self.show_search_dialog()

    def show_search_dialog(self):
        """Mostra um dialog com campo de busca"""
        self.is_searching = True

        # Campo de busca
        search_field = ft.TextField(
            hint_text="Digite para buscar...",
            autofocus=True,
            text_style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16),
            border_radius=10,
            on_change=self.on_search_change,
            on_submit=self.on_search_submit
        )

        # Lista de resultados
        results_column = ft.Column(
            controls=[],
            spacing=5,
            scroll=ft.ScrollMode.AUTO,
            height=200
        )

        # Mostra todos os itens inicialmente
        self.update_results_list(results_column, self.original_items)

        # Dialog de busca
        search_dialog = ft.AlertDialog(
            title=ft.Text("Buscar Item"),
            content=ft.Container(
                content=ft.Column([
                    search_field,
                    ft.Divider(),
                    ft.Text("Resultados:", weight=ft.FontWeight.BOLD, size=14),
                    results_column
                ], spacing=10),
                width=400,
                height=300
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=self.close_search_dialog),
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )

        # Armazena referências para uso posterior
        self.search_dialog = search_dialog
        self.search_field = search_field
        self.results_column = results_column

        # Mostra o dialog
        if self.page:
            self.page.open(search_dialog)

    def on_search_change(self, e):
        """Busca em tempo real conforme o usuário digita"""
        search_text = e.control.value.lower().strip()

        if not search_text:
            filtered_items = self.original_items
        else:
            # Busca por correspondência parcial
            filtered_items = [
                item for item in self.original_items
                if search_text in item["description"].lower()
            ]

        self.update_results_list(self.results_column, filtered_items)

    def update_results_list(self, results_column, items):
        """Atualiza a lista de resultados"""
        results_column.controls.clear()

        if not items:
            results_column.controls.append(
                ft.Text("Nenhum resultado encontrado",
                       color=ft.Colors.GREY_600,
                       italic=True)
            )
        else:
            for item in items:
                results_column.controls.append(
                    ft.ListTile(
                        title=ft.Text(item["description"], size=14),
                        on_click=lambda e, item_id=item["id"], item_desc=item["description"]:
                            self.select_item(item_id, item_desc),
                        bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.GREY),
                        shape=ft.RoundedRectangleBorder(radius=5)
                    )
                )

        if results_column.page:
            results_column.update()

    def select_item(self, item_id, item_desc):
        """Seleciona um item da busca"""
        self._value = item_id
        self.dropdown.value = item_id  # CORREÇÃO: Usar o ID (key) para definir o valor
        self.close_search_dialog(None)
        self.dropdown.update()

        # Chama o callback se definido
        if self.on_change_callback:
            self.on_change_callback(self.create_change_event())

    def on_search_submit(self, e):
        """Quando o usuário pressiona Enter na busca"""
        search_text = e.control.value.lower().strip()

        if search_text:
            # Busca o primeiro item correspondente
            filtered_items = [
                item for item in self.original_items
                if search_text in item["description"].lower()
            ]

            if filtered_items:
                first_item = filtered_items[0]
                self.select_item(first_item["id"], first_item["description"])

    def close_search_dialog(self, e):
        """Fecha o dialog de busca"""
        if hasattr(self, 'search_dialog') and self.page:
            self.page.close(self.search_dialog)

        self.is_searching = False

    # --- Handlers e Propriedades ---
    def handle_dropdown_change(self, e):
        """Handler para mudanças no dropdown"""
        self._value = e.control.value
        if self.on_change_callback:
            self.on_change_callback(e)

    def create_change_event(self):
        """Cria um evento simulado para compatibilidade"""
        class ChangeEvent:
            def __init__(self, control):
                self.control = control

        return ChangeEvent(self)

    @property
    def value(self):
        """Getter para o valor selecionado"""
        return self._value

    @value.setter
    def value(self, val):
        """Setter para o valor selecionado"""
        self._value = val
        if self.dropdown:
            self.dropdown.value = val
            self.dropdown.update()


    def set_on_change(self, callback):
        """Define o callback para mudanças"""
        self.on_change_callback = callback

# Exemplo de uso
def main(page: ft.Page):
    page.title = "DropdownSearch Demo"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    # Dados de exemplo
    items = [
        {"id": "1", "description": "Python Programming"},
        {"id": "2", "description": "JavaScript Development"},
        {"id": "3", "description": "Data Science with Python"},
        {"id": "4", "description": "Web Development"},
        {"id": "5", "description": "Machine Learning"},
        {"id": "6", "description": "Mobile App Development"},
        {"id": "7", "description": "Database Management"},
        {"id": "8", "description": "Cloud Computing"},
        {"id": "9", "description": "Artificial Intelligence"},
        {"id": "10", "description": "Cybersecurity"},
        {"id": "11", "description": "DevOps Engineering"},
        {"id": "12", "description": "Full Stack Development"},
    ]

    # Texto para mostrar seleção
    selected_text = ft.Text("Nenhum item selecionado", size=16)

    def on_selection_change(e):
        if e.control.value:
            selected_item = next(
                (item for item in items if item["id"] == e.control.value),
                None
            )
            if selected_item:
                selected_text.value = f"Selecionado: {selected_item['description']}"
            else:
                selected_text.value = "Nenhum item selecionado"
        else:
            selected_text.value = "Nenhum item selecionado"
        page.update()

    dropdown_search = DropdownSearch(
        page=page, # Passa a página para o componente
        items=items,
        hint_text="Selecione ou busque uma tecnologia...",
        width=400,
        on_change_callback=on_selection_change
    )

    page.add(
        ft.Container(
            content=ft.Column([
                ft.Text("DropdownSearch com Busca", size=24, weight=ft.FontWeight.BOLD),
                ft.Text("Clique no ícone de busca (🔍) para pesquisar!", size=14, color=ft.Colors.GREY_600),
                dropdown_search, # Adiciona a instância diretamente
                selected_text
            ], spacing=20),
            margin=ft.margin.all(20),
            alignment=ft.alignment.center
        )
    )

if __name__ == "__main__":
    ft.app(target=main)