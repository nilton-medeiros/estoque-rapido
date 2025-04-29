import flet as ft
import uuid

"""
Test: Armazenar informações no lado do cliente (navegador)
usando o client_storage. do Flet.
"""


def main(page: ft.Page):
    page.title = "Gerar e Armazenar ID Único"

    # Chave para armazenar o token no client_storage
    STORAGE_KEY = "estoque.rapido.user_session"

    # Função para gerar um novo ID e armazená-lo
    def generate_id(e):
        # Gera um UUID único
        unique_id = str(uuid.uuid4())
        # Armazena no client_storage (persiste no navegador)
        page.client_storage.set(STORAGE_KEY, unique_id)
        # Atualiza a interface com o ID gerado
        page.add(ft.Text(f"ID Gerado: {unique_id}"))
        page.update()

    # Função para recuperar o ID armazenado
    def retrieve_id(e):
        sessionid_text.value = f"ID da Sessão: {page.session_id}"
        # Recupera o ID do client_storage
        stored_id = page.client_storage.get(STORAGE_KEY)
        if stored_id:
            page.add(ft.Text(f"ID Armazenado: {stored_id}"))
        else:
            page.add(ft.Text("Nenhum ID encontrado. Gere um novo ID."))
        page.update()

    # Interface com botões para gerar e recuperar o ID

    sessionid_text = ft.Text(f"ID da Sessão: {page.session_id}")

    page.add(
        sessionid_text,
        ft.ElevatedButton("Gerar ID", on_click=generate_id),
        ft.ElevatedButton("Recuperar ID", on_click=retrieve_id),
    )


# Executa a aplicação como um aplicativo web
ft.app(target=main, view=ft.AppView.WEB_BROWSER)

# Executa o aplicativo
# ft.app(target=main, view=ft.WEB_BROWSER)
