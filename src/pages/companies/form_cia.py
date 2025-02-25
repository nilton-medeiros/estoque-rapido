import flet as ft
from src.presentation.components.company_form import CompanyForm
from src.utils.message_snackbar import MessageType, message_snackbar


def company_form(page: ft.Page):
    current_company = page.app_state.company
    print(f"current_company: {current_company}")

    print("Debug | current_company: {current_company}")
    # Cria o formulário
    form = CompanyForm(
        page=page,
        company_data=current_company if current_company.get('id') else None
    )

    print(f"form: {form}")

    # Define a função salvar
    async def save_company(e):
        try:
            form_data = form.get_form_data()  # Obtém os dados do formulário

            if current_company.get('id'):
                form_data['id'] = current_company['id']

            print(f"Dados do formulário: {form_data}")  # Debug
            # Todo: Implementar a lógica de salvar os dados da empresa

        except ValueError as err:
            message_snackbar(page=page, message=str(err), message_type=MessageType.ERROR)

    # Adiciona o botão "Salvar"
    save_btn = ft.ElevatedButton("Salvar", on_click=save_company)

    print("Debug | Botão Salvar foi adicionado à página")

    return ft.Column(
        controls=[form, save_btn]
    )
