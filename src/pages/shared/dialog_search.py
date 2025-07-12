import flet as ft

class DialogSearch:
    def __init__(self, page: ft.Page, items: list[dict], hint_text: str = "Digite para buscar...", on_select_callback=None):
        self.page = page
        self.original_items = items
        self.on_select_callback = on_select_callback
        self.hint_text = hint_text

    def show(self):
        """Mostra um dialog com campo de busca"""
        # Campo de busca
        search_field = ft.TextField(
            hint_text=self.hint_text,
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
                ft.TextButton("Cancelar", on_click=self.close_dialog),
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
                is_unavailable = item["quantity_on_hand"] < 1
                results_column.controls.append(
                    ft.ListTile(
                        title=ft.Text(item["description"], size=14),
                        subtitle=ft.Text(f"Estoque: {item['quantity_on_hand']}", size=12),
                        on_click=(lambda e, item_id=item["id"], item_desc=item["description"],
                                 item_price=item["sale_price"], item_quantity_on_hand=item["quantity_on_hand"],
                                 item_unit_of_measure=item["unit_of_measure"]:
                                 self.select_item(item_id, item_desc, item_price, item_quantity_on_hand, item_unit_of_measure))
                                 if not is_unavailable else None,
                        disabled=is_unavailable,
                        bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.RED_300) if is_unavailable
                                else ft.Colors.with_opacity(0.1, ft.Colors.GREY),
                        shape=ft.RoundedRectangleBorder(radius=5)
                    )
                )

        if results_column.page:
            results_column.update()

    def select_item(self, item_id, item_desc, item_price, item_quantity_on_hand, item_unit_of_measure):
        """Seleciona um item da busca"""
        self.close_dialog(None)
        if self.on_select_callback:
            self.on_select_callback(
                {
                    "id": item_id,
                    "description": item_desc,
                    "price": item_price,
                    "quantity_on_hand": item_quantity_on_hand,
                    "unit_of_measure": item_unit_of_measure
                }
            )

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
                self.select_item(first_item["id"], first_item["description"], first_item["sale_price"], first_item["quantity_on_hand"], first_item["unit_of_measure"])

    def close_dialog(self, e):
        """Fecha o dialog de busca"""
        if hasattr(self, 'search_dialog') and self.page:
            self.page.close(self.search_dialog)

# Exemplo de uso
# def main(page: ft.Page):
#     page.title = "DialogSearch Demo"
#     page.vertical_alignment = ft.MainAxisAlignment.CENTER
#     page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

#     # Dados de exemplo
#     items = [
#         {"id": "1", "description": "Python Programming"},
#         {"id": "2", "description": "JavaScript Development"},
#         {"id": "3", "description": "Data Science with Python"},
#         {"id": "4", "description": "Web Development"},
#         {"id": "5", "description": "Machine Learning"},
#         {"id": "6", "description": "Mobile App Development"},
#         {"id": "7", "description": "Database Management"},
#         {"id": "8", "description": "Cloud Computing"},
#         {"id": "9", "description": "Artificial Intelligence"},
#         {"id": "10", "description": "Cybersecurity"},
#         {"id": "11", "description": "DevOps Engineering"},
#         {"id": "12", "description": "Full Stack Development"},
#     ]

#     # Texto para mostrar seleção
#     selected_text = ft.Text("Nenhum item selecionado", size=16)

#     def on_selection_change(selected_item):
#         if selected_item:
#             selected_text.value = f"Selecionado: {selected_item['description']}"
#         else:
#             selected_text.value = "Nenhum item selecionado"
#         page.update()

#     dialog_search = DialogSearch(
#         page=page,
#         items=items,
#         hint_text="Selecione ou busque uma tecnologia...",
#         on_select_callback=on_selection_change
#     )

#     page.add(
#         ft.Container(
#             content=ft.Column([
#                 ft.Text("DialogSearch Demo", size=24, weight=ft.FontWeight.BOLD),
#                 ft.ElevatedButton("Abrir Busca", on_click=lambda e: dialog_search.show()),
#                 selected_text
#             ], spacing=20),
#             margin=ft.margin.all(20),
#             alignment=ft.alignment.center
#         )
#     )

# if __name__ == "__main__":
#     ft.app(target=main)
