import flet as ft

from src.pages.home.home_page import home_page
from src.pages.signup import signup
from src.pages.landing_page import landing_page
from src.pages.login import login
from src.services import AppStateManager  # Alterado para AppStateManager


def main(page: ft.Page):
    # Força a limpeza do cache no início da aplicação
    page.clean()
    page.user_name_text = ft.Text("Nenhum Usuário logado")
    page.company_name_text = ft.Text("Nenhuma empresa selecionada")

    # ToDo: Usar sessions_data para armazenar array user_id e company_id para o próximo logon
    # if not hasattr(page, 'sessions_data'):
    #     page.sessions_data = {}

    # Usando uma abordagem mais profissional com States e Pubsub
    app_state = AppStateManager(page)
    page.app_state = app_state  # Torna o app_state acessível globalmente

    # Registrar o evento para mudanças
    def handle_pubsub(message):
        if message == "user_updated":
            user = app_state.user
            if user:
                # Atualiza elementos da UI que dependem do usuário
                update_user_dependent_ui()
            else:
                print(":")
                print("================================================================================")
                print(f"Debug | Usuário foi desconectado.")
                print("================================================================================")
                print(" ")

                # Limpa elementos da UI relacionados ao usuário
                clear_user_ui()

        elif message.startswith("company_updated:"):
            company = app_state.company
            if company:
                print(f"Empresa atualizada: {company['name']}")
                # Atualiza elementos da UI que dependem da empresa
                update_company_dependent_ui()
            else:
                print(":")
                print("================================================================================")
                print(f"Debug | Empresa foi desconectada.")
                print("================================================================================")
                print(" ")

                # Limpa elementos da UI relacionados à empresa
                clear_company_ui()

    def update_user_dependent_ui():
        # Exemplo: Atualiza o nome do usuário no header
        if hasattr(page, 'user_name_text'):
            page.user_name_text.value = page.app_state.user['name'].nome_completo
            page.user_name_text.update()

    def update_company_dependent_ui():
        # Exemplo: Atualiza o nome da empresa no header
        if hasattr(page, 'company_name_text'):
            page.company_name_text.value = app_state.company['name']
            page.company_name_text.update()

    def clear_user_ui():
        if hasattr(page, 'user_name_text'):
            page.user_name_text.value = ""
            page.user_name_text.update()

    def clear_company_ui():
        if hasattr(page, 'company_name_text'):
            page.company_name_text.value = ""
            page.company_name_text.update()

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
            case '/signup':  # Registro
                pg_view = ft.View(
                    route='/signup',
                    controls=[signup(page)],
                    bgcolor=ft.Colors.BLACK,
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
                # page.sessions_data.clear()
                page.route = '/'
            case '/home':
                if not app_state.user:
                    page.go('/login')  # Redireciona se não estiver autenticado
                else:
                    pg_view = ft.View(
                        route='/home',
                        controls=[home_page(page)],
                        bgcolor=ft.Colors.BLACK,
                        vertical_alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    )
            case _:
                print('rota selecionada:', e.route)
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
    ft.app(target=main, assets_dir="assets", view=ft.WEB_BROWSER)
