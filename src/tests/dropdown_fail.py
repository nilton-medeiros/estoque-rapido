import flet as ft

def main(page: ft.Page):
    def on_dd_change(e: ft.ControlEvent):
        dd_value = e.control.value
        selected_opt_text = "N/A"
        if dd_value:
            selected_opt = next((opt for opt in dd.options if opt.key == dd_value), None)
            if selected_opt:
                selected_opt_text = selected_opt.text

        txt_value.value = f"Valor selecionado: {dd_value} (Texto: {selected_opt_text})"
        txt_value.update()

    dd = ft.Dropdown(
        label="Teste Dropdown",
        hint_text="Selecione uma opção",
        options=[
            ft.dropdown.Option(key="ID1", text="Opção 1"),
            ft.dropdown.Option(key="ID2", text="Opção 2"),
            ft.dropdown.Option(key="ID3", text="Opção 3"),
        ],
        on_change=on_dd_change,
        enable_filter=True # Para replicar sua configuração
    )
    txt_value = ft.Text("Nenhuma seleção ainda.")

    page.add(dd, txt_value)

ft.app(target=main)
