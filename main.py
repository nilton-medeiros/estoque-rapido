import flet as ft
import logging
import os

from dotenv import load_dotenv

from src.pages.external_pages import show_signup_page, show_landing_page, show_login_page
from src.pages.clientes.clientes_form_page import show_client_form
from src.pages.clientes.clientes_grid_page import show_clients_grid
from src.pages.clientes.clientes_grid_recycle_page import show_clients_grid_trash
from src.pages.empresas import show_companies_grid, show_company_main_form, show_company_tax_form, show_companies_grid_trash
from src.pages.home import show_home_page
from src.pages.pedidos.pedidos_form_page import show_pedido_form
from src.pages.pedidos.pedidos_grid_page import show_orders_grid
from src.pages.pedidos.pedidos_grid_recycle_page import show_orders_grid_trash
from src.pages.produtos import show_products_grid, show_products_grid_trash, show_product_form
from src.pages.categorias import show_categories_grid, show_categories_grid_trash, show_category_form
from src.pages.usuarios.usuarios_form_page import show_user_form
from src.pages.usuarios.usuarios_grid_page import show_users_grid
from src.pages.usuarios.usuarios_grid_recycle_page import show_users_grid_trash
from src.services import AppStateManager
from src.services.states.refresh_session import refresh_dashboard_session
from src.shared.config import get_app_colors

logger = logging.getLogger(__name__)

# Carrega a chave do Flet para assinar URLs temporárias de upload
load_dotenv()
flet_key: str | None = os.getenv('FLET_SECRET_KEY')
# Definindo a chave secreta - em produção, use variáveis de ambiente
if flet_key:
    os.environ["FLET_SECRET_KEY"] = flet_key


def main(page: ft.Page):
    # Força a limpeza do cache no início da aplicação
    page.clean()
    page.user_name_text: ft.Text = ft.Text( # type: ignore  [attr-defined]
        "Nenhum Usuário logado")  # type: ignore  [attr-defined]
    page.company_name_text_btn: ft.TextButton = ft.TextButton(  # type: ignore  [attr-defined]
        text="NENHUMA EMPRESA SELECIONADA",
        style=ft.ButtonStyle(
            alignment=ft.alignment.center,  # type: ignore  [attr-defined]
            # mouse_cursor="pointer",
            text_style=ft.TextStyle(  # type: ignore  [attr-defined]
                color=ft.Colors.WHITE, size=14, weight=ft.FontWeight.NORMAL) # type: ignore  [attr-defined]
        ),
        tooltip="Clique aqui e preencha os dados da empresa"
    )

    # Configurar cores padrão imediatamente para evitar erros
    # Garante que há sempre uma cor padrão
    page.session.set("user_colors", get_app_colors('yellow'))

    dashboard_data = {
        "repor_produtos": 0,
        "encomendas": 0,
        "pagamentos": 0,
        "recebimentos": 0,
    }

    page.session.set("dashboard", dashboard_data)

    # Inicialize o estado da aplicação
    app_state = AppStateManager(page)
    # Torna o app_state acessível globalmente
    page.app_state = app_state # type: ignore  [attr-defined]

    # Registrar o evento para mudanças
    def handle_pubsub(message):
        match message:
            case "usuario_updated":
                if page.app_state.usuario.get('name'): # type: ignore  [attr-defined]
                    # Atualiza elementos da UI que dependem do usuário
                    update_usuario_dependent_ui()
                else:
                    # Limpa elementos da UI relacionados ao usuário
                    clear_usuario_ui()
            case "empresa_updated": # Adicionado o tratamento para empresa_updated
                # Executa a atualização do dashboard em uma task separada (async)
                page.run_task(refresh_dashboard_session, page) # type: ingnore [attr: defined]
                if page.app_state.empresa.get('corporate_name'): # type: ignore  [attr-defined]
                    # Atualiza elementos da UI que dependem da empresa
                    update_empresa_dependent_ui()
                else:
                    # Limpa elementos da UI relacionados à empresa
                    clear_empresa_ui()

            case "dashboard_refreshed":
                print("Debug -> Evento 'dashboard_refreshed' recebido em main.py")
                # A UI específica (MainContent) irá lidar com a atualização.
                # Podemos forçar um page.update() aqui se necessário para outras partes da UI global.
                # page.update()

    def update_usuario_dependent_ui():
        # Exemplo: Atualiza o nome do usuário no header
        if hasattr(page, 'user_name_text'):
            # type: ignore  [attr-defined]
            page.user_name_text.value = page.app_state.usuario['name'].nome_completo # type: ignore  [attr-defined]
            # O update deve ser no controlador que chama o evento após chamar este evento
            # page.user_name_text.update()

    def update_empresa_dependent_ui():
        # Exemplo: Atualiza o nome da empresa no header
        if hasattr(page, 'company_name_text_btn'):
            page.company_name_text_btn.text = page.app_state.empresa.get(  # type: ignore  [attr-defined]
                'trade_name', 'corporate_name')
            # O update deve ser no controlador que chama o evento após chamar este evento
            # page.company_name_text_btn.update()

    def clear_usuario_ui():
        if hasattr(page, 'user_name_text'):
            page.user_name_text.value = ""  # type: ignore  [attr-defined]
            # page.user_name_text.update()

    def clear_empresa_ui():
        if hasattr(page, 'company_name_text_btn'):
            # type: ignore  [attr-defined]
            page.company_name_text_btn.text = "NENHUMA EMPRESA SELECIONADA" # type: ignore  [attr-defined]
            # page.company_name_text_btn.update()

    def page_back(_=None):
        """Gerencia a navegação para a página anterior.

        Prioriza a rota armazenada em `page.data`. Se não houver rota
        definida, navega para '/home' como fallback.
        """
        # Antes de voltar a página anterior, limpa dados de formulário.
        page.app_state.clear_form_data()  # type: ignore [attr-defined]
        if page.data:
            page.go(page.data)
        else:
            page.go('/home')

    page.back = page_back  # type: ignore  [attr-defined]

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

    def handle_icon_hover(e):
        """Muda o bgcolor do container no hover"""
        e.control.bgcolor = ft.Colors.with_opacity(
            0.1, ft.Colors.WHITE) if e.data == "true" else ft.Colors.TRANSPARENT
        e.control.update()

    # Rotas
    def route_change(e: ft.RouteChangeEvent):
        # Centraliza a verificação de autenticação para rotas protegidas
        if e.route.startswith('/home'):
            page.on_resized = None
            if not page.app_state.usuario.get('id'):  # type: ignore [attr-defined]
                page.go('/login')
                return  # Interrompe o processamento para redirecionar

        page.views.clear()
        pg_view = None

        match e.route:
            case '/':  # Raiz: Landing Page
                pg_view = ft.View(
                    route='/',
                    controls=[show_landing_page(page)],
                    appbar=page.appbar,
                    vertical_alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                )
            case '/login':
                pg_view = ft.View(
                    route='/login',
                    controls=[show_login_page(page)],
                    bgcolor=ft.Colors.BLACK,
                    vertical_alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                )
            case '/logout':
                page.app_state.clear_states()  # type: ignore [attr-defined]
                page.go('/')  # Redireciona para a página inicial
            case '/home':
                # Acesso a página /home somente usuários logados
                home_container = show_home_page(page)
                pg_view = ft.View(
                    route='/home',
                    appbar=home_container.data,
                    controls=[home_container],
                    bgcolor=ft.Colors.BLACK,
                    vertical_alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                )
            case '/home/empresas/grid':
                pg_view = show_companies_grid(page)
            case '/home/empresas/grid/lixeira':
                pg_view = show_companies_grid_trash(page)
            case '/home/empresas/form/principal':
                form = show_company_main_form(page)
                pg_view = ft.View(
                    route='/home/empresas/form/principal',
                    appbar=form.data,
                    controls=[form],
                    scroll=ft.ScrollMode.AUTO,
                    bgcolor=ft.Colors.BLACK,
                    vertical_alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                )
            case '/home/empresas/form/dados-fiscais':
                form = show_company_tax_form(page)
                pg_view = ft.View(
                    route='/home/empresas/form/dados-fiscais',
                    appbar=form.data,
                    controls=[form],
                    scroll=ft.ScrollMode.AUTO,
                    bgcolor=ft.Colors.BLACK,
                    vertical_alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                )
            case '/home/usuarios/grid':
                pg_view = show_users_grid(page)
            case '/home/usuarios/grid/lixeira':
                pg_view = show_users_grid_trash(page)
            case '/home/usuarios/form':
                form = show_user_form(page)
                pg_view = ft.View(
                    route='home/usuarios/form',
                    appbar=form.data,
                    controls=[form],
                    scroll=ft.ScrollMode.AUTO,
                    bgcolor=ft.Colors.BLACK,
                    vertical_alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                )
            case '/home/clientes/grid':
                pg_view = show_clients_grid(page)
            case '/home/clientes/grid/lixeira':
                pg_view = show_clients_grid_trash(page)
            case '/home/clientes/form':
                form = show_client_form(page)
                pg_view = ft.View(
                    route='home/clientes/form',
                    appbar=form.data,
                    controls=[form],
                    scroll=ft.ScrollMode.AUTO,
                    bgcolor=ft.Colors.BLACK,
                    vertical_alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                )
            case '/home/produtos/grid':
                pg_view = show_products_grid(page)
            case '/home/produtos/grid/lixeira':
                pg_view = show_products_grid_trash(page)
            case '/home/produtos/form':
                form = show_product_form(page)
                pg_view = ft.View(
                    route='home/produtos/form',
                    appbar=form.data,
                    controls=[form],
                    scroll=ft.ScrollMode.AUTO,
                    bgcolor=ft.Colors.BLACK,
                    vertical_alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                )
            case '/home/produtos/categorias/grid':
                pg_view = show_categories_grid(page)
            case '/home/produtos/categorias/grid/lixeira':
                pg_view = show_categories_grid_trash(page)
            case '/home/produtos/categorias/form':
                form = show_category_form(page)
                pg_view = ft.View(
                    route='home/produtos/categorias/form',
                    appbar=form.data,
                    controls=[form],
                    scroll=ft.ScrollMode.AUTO,
                    bgcolor=ft.Colors.BLACK,
                    vertical_alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                )
            case '/home/pedidos/grid':
                pg_view = show_orders_grid(page)
            case '/home/pedidos/grid/lixeira':
                pg_view = show_orders_grid_trash(page)
            case '/home/pedidos/form':
                pg_view = show_pedido_form(page)
            case '/signup':  # Registro
                pg_view = ft.View(
                    route='/signup',
                    controls=[show_signup_page(page)],
                    bgcolor=ft.Colors.BLACK,
                    vertical_alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                )
            case _:  # Rota não encontrada (page 404)
                # Opcional: tratamento para rotas não encontradas
                pg_view = ft.View(
                    route="/404",
                    controls=[
                        ft.AppBar(
                            leading=ft.Container(
                                width=40,
                                height=40,
                                # Metade da largura/altura para ser círculo
                                border_radius=ft.border_radius.all(20),
                                # Aplica ink ao wrapper (ao clicar da um feedback visual para o usuário)
                                ink=True,
                                bgcolor=ft.Colors.TRANSPARENT,
                                alignment=ft.alignment.center,
                                on_hover=handle_icon_hover,
                                content=ft.Icon(
                                    name=ft.Icons.INVENTORY_OUTLINED, color=ft.Colors.WHITE),
                            ),
                            title=ft.Text(
                                "ESTOQUE RÁPIDO: Soluções Eficientes para Gestão de Estoque e Finanças", color=ft.Colors.WHITE),
                            bgcolor=ft.Colors.BLUE_700,
                        ),
                        ft.Text("404 - Página não encontrada", size=30),
                        ft.OutlinedButton(
                            text="Ir para a página inicial",
                            on_click=lambda _: page.go("/"),
                        )
                    ],
                    vertical_alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                )

        # Adiciona a view à página, no caso das rota /logout, pg_view é None e /home, pg_view pode ser None ou não
        if pg_view:
            page.views.append(pg_view)
            page.update()

    def view_pop(e: ft.ViewPopEvent):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)  # type: ignore

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go(page.route)


if __name__ == '__main__':
    # A configuração de logging agora é feita centralmente através da importação
    # de src.shared.config.logging_config (que é importado por src.shared.config)
    # Inicia o app Flet
    ft.app(
        target=main,
        assets_dir="assets",
        upload_dir="uploads",
        port=10000,
        view=ft.AppView.WEB_BROWSER
        # view=ft.WEB_BROWSER
    )
