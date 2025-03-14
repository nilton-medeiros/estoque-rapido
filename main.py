import flet as ft
from dotenv import load_dotenv
import os

import logging

from src.pages.empresas.form_cia import company_form
from src.pages.home.home_page import home_page
from src.pages.signup import signup
from src.pages.landing_page import landing_page
from src.pages.login import login
from src.services import AppStateManager  # Alterado para AppStateManager

logger = logging.getLogger(__name__)

# Carrega a chave do Flet para assinar URLs temporárias de upload
load_dotenv()
flet_key = os.getenv('FLET_SECRET_KEY')
# Definindo a chave secreta - em produção, use variáveis de ambiente
os.environ["FLET_SECRET_KEY"] = flet_key


def main(page: ft.Page):
    # Força a limpeza do cache no início da aplicação
    page.clean()
    page.user_name_text = ft.Text("Nenhum Usuário logado")
    page.company_name_text_btn = ft.TextButton(
        text="NENHUMA EMPRESA SELECIONADA",
        style=ft.ButtonStyle(
            alignment=ft.alignment.center,
            mouse_cursor="pointer",
            text_style=ft.TextStyle(
                color=ft.Colors.GREY,
                size=14,
                weight=ft.FontWeight.NORMAL,
            )
        ),
        tooltip="Clique aqui e preencha os dados da empresa"
    )

    #  Uso de sessions
    if not hasattr(page, 'sessions_data'):
        page.sessions_data = {}

    # Usando uma abordagem mais profissional com States e Pubsub
    app_state = AppStateManager(page)
    page.app_state = app_state  # Torna o app_state acessível globalmente

    # Registrar o evento para mudanças
    def handle_pubsub(message):
        if message == "usuario_updated":
            if app_state.usuario:
                # Atualiza elementos da UI que dependem do usuário
                update_usuario_dependent_ui()
            else:
                # Limpa elementos da UI relacionados ao usuário
                clear_usuario_ui()

        elif message.startswith("empresa_updated:"):
            if app_state.empresa:
                # print(f"Empresa atualizada: {empresa['name']}")
                # Atualiza elementos da UI que dependem da empresa
                update_empresa_dependent_ui()
            else:
                # Limpa elementos da UI relacionados à empresa
                clear_empresa_ui()

    def update_usuario_dependent_ui():
        # Exemplo: Atualiza o nome do usuário no header
        if hasattr(page, 'user_name_text'):
            page.user_name_text.value = page.app_state.usuario['name'].nome_completo
            page.user_name_text.update()

    def update_empresa_dependent_ui():
        # Exemplo: Atualiza o nome da empresa no header
        if hasattr(page, 'company_name_text_btn'):
            page.company_name_text_btn.text = app_state.empresa['name']
            page.company_name_text_btn.update()

    def clear_usuario_ui():
        if hasattr(page, 'user_name_text'):
            page.user_name_text.value = ""
            page.user_name_text.update()

    def clear_empresa_ui():
        if hasattr(page, 'company_name_text_btn'):
            page.company_name_text_btn.text = "NENHUMA EMPRESA SELECIONADA"
            page.company_name_text_btn.update()

    # Registra o handler do PubSub
    page.pubsub.subscribe(handle_pubsub)

    page.title = "EstoqueRápido"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.window.width = 1680
    page.window.min_width = 300
    page.window.height = 992
    page.window.min_height = 900

    page.padding = 0
    page.spacing = 0

    # Rotas
    def route_change(e: ft.RouteChangeEvent):
        page.views.clear()
        pg_view = None

        match e.route:
            case '/':    # Raiz: Landing Page
                pg_view = ft.View(
                    route='/',
                    controls=[landing_page(page)],
                    appbar=page.appbar,
                    vertical_alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                )
            case '/login':
                pg_view = ft.View(
                    route='/login',
                    controls=[login(page)],
                    bgcolor=ft.Colors.BLACK,
                    vertical_alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                )
            case '/logout':
                page.app_state.clear_state()
                page.sessions_data.clear()
                page.update()
                page.go('/')
            case '/home':
                if not app_state.user:
                    page.go('/login')  # Redireciona se não estiver autenticado
                else:
                    page.on_resized = None
                    home = home_page(page)
                    pg_view = ft.View(
                        route='/home',
                        controls=[home],
                        appbar=home.data,
                        bgcolor=ft.Colors.BLACK,
                        vertical_alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    )
            case '/empresas/form':  # Registro
                route_title = "home/empresas/form"
                company = app_state.empresa
                id = company.get('id', None)
                if id is not None:
                    route_title += f"/{id}"
                else:
                    route_title += "/new"

                pg_view = ft.View(
                    route='/empresas/form',
                    appbar=ft.AppBar(
                        title=ft.Text(route_title, size=16),
                        leading=ft.IconButton(
                            icon=ft.Icons.ARROW_BACK,
                            on_click=lambda _: page.go("/home"),
                        ),
                    ),
                    controls=[company_form(page)],
                    scroll=ft.ScrollMode.AUTO,
                    bgcolor=ft.Colors.BLACK,
                    vertical_alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                )
            case '/signup':  # Registro
                pg_view = ft.View(
                    route='/signup',
                    controls=[signup(page)],
                    bgcolor=ft.Colors.BLACK,
                    vertical_alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                )
            case _:
                # Opcional: tratamento para rotas não encontradas
                pg_view = ft.View(
                    route="/404",
                    controls=[
                        ft.AppBar(
                            leading=ft.Icon(
                                name=ft.Icons.INVENTORY_OUTLINED, color=ft.Colors.WHITE),
                            leading_width=40,
                            title=ft.Text(
                                "ESTOQUE RÁPIDO: Soluções Eficientes para Gestão de Estoque e Finanças", color=ft.Colors.WHITE),
                            bgcolor=ft.Colors.BLUE_700,
                        ),
                        ft.Text("404 - Página não encontrada", size=30),
                        ft.ElevatedButton(
                            text="Voltar à pagina principal",
                            on_click=lambda _: page.go("/"),
                            adaptive=True,
                        )
                    ],
                    vertical_alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                )

        page.views.append(pg_view)
        page.update()

    def view_pop(e: ft.ViewPopEvent):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go(page.route)


if __name__ == '__main__':
    ft.app(
        target=main,
        assets_dir="assets",
        upload_dir="uploads",
        view=ft.WEB_BROWSER
    )
