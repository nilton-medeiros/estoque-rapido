import os
import flet as ft
import requests

"""
Teste: Obter informações do computador como S.O., etc.
Não resolve nada
"""

def main(page: ft.Page):
    # Configurações iniciais da página
    page.title = "Formulário campos de empresa"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    response = requests.get('http://httpbin.org/headers')
    user_agent = response.json()['headers']['User-Agent']
    print(f"User-Agent: {user_agent}")  # Retorna "User-agent: python-requests/2.32.3"

# Executa o aplicativo
ft.app(target=main, view=ft.WEB_BROWSER)