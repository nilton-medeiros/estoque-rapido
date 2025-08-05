import flet as ft
import logging
import os

from dotenv import load_dotenv

from src.domains.shared.context.session import get_current_user
from src.pages.partials.app_bars.sidebar import create_navigation_drawer
from src.pages.partials.app_bars.sidebar_header import create_sidebar_header
from src.routes import ROUTE_HANDLERS
from src.services import AppStateManager
from src.services.states.refresh_session import refresh_dashboard_session
from src.shared.config import get_theme_colors

logger = logging.getLogger(__name__)

# Carrega a chave do Flet para assinar URLs temporárias de upload
load_dotenv()
flet_key: str | None = os.getenv('FLET_SECRET_KEY')
# Definindo a chave secreta - em produção, use variáveis de ambiente
if flet_key:
    os.environ["FLET_SECRET_KEY"] = flet_key


def main(page: ft.Page):
    """
    Single Page Application (SPA)
    utiliza o sistema de rotas do Flet (page.route e page.on_route_change) para gerenciar a navegação dinamicamente,
    renderizando diferentes views (ft.View) dentro de uma única página, sem recarregar a aplicação no navegador.
    Isso proporciona uma experiência de usuário mais fluida, com transições rápidas entre diferentes seções da aplicação como
    (/home, /login, /home/empresas/grid, etc.), mantendo o estado e os dados no lado do cliente.
    """
    # Força a limpeza do cache no início da aplicação
    page.clean()
    page.user_name_text: ft.Text = ft.Text( # type: ignore  [attr-defined]
        "Nenhum Usuário logado")  # type: ignore  [attr-defined]
    page.company_name_text_btn: ft.TextButton = ft.TextButton(  # type: ignore  [attr-defined]
        text="NENHUMA EMPRESA SELECIONADA",
        style=ft.ButtonStyle(
            alignment=ft.alignment.center,
            # mouse_cursor="pointer",
            text_style=ft.TextStyle(
                color=ft.Colors.WHITE, size=14, weight=ft.FontWeight.NORMAL) # type: ignore  [attr-defined]
        ),
        tooltip="Clique aqui e preencha os dados da empresa"
    )

    # Configuração do page.session (Sessão do usuário)

    page.session.set("user_authenticaded", False)  # Indica se o usuário está logado ou não
    # Configurar cores padrão imediatamente para evitar erros
    page.session.set("theme_colors", get_theme_colors())  # Garante que há sempre uma cor padrão

    dashboard_data = {
        "repor_produtos": 0,
        "encomendas": 0,
        "pagamentos": 0,
        "recebimentos": 0,
    }

    page.session.set("dashboard", dashboard_data)

    # Inicialize o estado da aplicação
    # Torna o app_state acessível globalmente
    page.app_state = AppStateManager(page) # type: ignore  [attr-defined]

    # Registrar o evento para mudanças
    def handle_pubsub(message):
        match message:
            case "usuario_updated":
                if current_user := get_current_user(page):
                    # Atualiza elementos da UI que dependem do usuário
                    update_usuario_dependent_ui(current_user)
                else:
                    # Limpa elementos da UI relacionados ao usuário
                    clear_usuario_ui()
            case "empresa_updated": # Adicionado o tratamento para empresa_updated
                # Executa a atualização do dashboard em uma task separada (async)
                page.run_task(refresh_dashboard_session, page) # type: ingnore [attr-defined]
                if page.app_state.empresa.get('corporate_name'): # type: ignore  [attr-defined]
                    # Atualiza elementos da UI que dependem da empresa
                    update_empresa_dependent_ui()
                else:
                    # Limpa elementos da UI relacionados à empresa
                    clear_empresa_ui()

            case "dashboard_refreshed":
                pass
                # print("Debug -> Evento 'dashboard_refreshed' recebido em main.py")
                # A UI específica (MainContent) irá lidar com a atualização.
                # Podemos forçar um page.update() aqui se necessário para outras partes da UI global.
                # page.update()

    def update_usuario_dependent_ui(current_user):
        # Exemplo: Atualiza o nome do usuário no header
        if hasattr(page, 'user_name_text'):
            page.user_name_text.value = current_user.name.nome_completo  # type: ignore [attr-defined]
        if page.session.get("user_authenticaded"):
            if page.drawer:
                if page.drawer.controls:  # Garante que a lista de controles exista
                    page.drawer.controls[0] = create_sidebar_header(page)  # Recria apenas o cabeçalho

        page.update()

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

    page.drawer = create_navigation_drawer(page)  # Cria o drawer inicial (com placeholder se não logado)

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
            if not page.session.get("user_authenticaded"):
                page.go('/login')
                return  # Interrompe o processamento para redirecionar

        page.views.clear()
        pg_view = None

        # --- Lógica de Roteamento Refatorada ---

        # Tratar casos especiais primeiro
        if e.route == '/logout':
            page.app_state.clear_states()  # type: ignore [attr-defined]
            page.go('/')  # Redireciona para a página inicial
            return  # Interrompe o processamento

        # Busca o handler da rota no dicionário
        handler = ROUTE_HANDLERS.get(e.route)

        if handler:
            pg_view = handler(page) # chama a função vinda o dict
        else:
            # Rota não encontrada (page 404)
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

        # Adiciona a view à página
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
