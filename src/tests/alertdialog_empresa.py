def edit_company_data(e):
    dialog = ft.AlertDialog(
        title=ft.Text("Editar dados da empresa"),
        content=ft.Container(
            content=ft.Column([
                ft.TextField(label="Razão Social"),
                ft.TextField(label="Nome Fantasia"),
                ft.TextField(label="CNPJ"),
                ft.TextField(label="Endereço"),
                ft.TextField(label="Cidade"),
                ft.TextField(label="Estado"),
            ]),
            padding=10
        ),
        actions=[
            ft.TextButton("Cancelar", on_click=close_dialog),
            ft.TextButton("Salvar", on_click=save_data),
        ],
    )
    page.dialog = dialog
    dialog.open = True
    page.update()