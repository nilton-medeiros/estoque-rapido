import flet as ft
import logging
import time
import threading
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path

from dotenv import load_dotenv
from src.pages.empresas.empresas_form import empresas_form
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

# Função para silenciar logs do uvicorn, mantendo-os apenas em arquivo


def reconfigure_logging():
    time.sleep(1)  # Espere o Flet inicializar

    # Configuração de arquivo
    log_dir = Path(__file__).parent.parent.parent.parent / 'logs'
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "app.log")

    # Crie o handler de arquivo
    file_handler = RotatingFileHandler(
        log_file, maxBytes=5242880, backupCount=5)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - [%(levelname)s] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    # Configure os loggers do uvicorn
    for logger_name in ["uvicorn", "uvicorn.access", "uvicorn.error"]:
        logger = logging.getLogger(logger_name)
        # Remova todos os handlers existentes (especialmente os do console)
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        # Adicione apenas o handler de arquivo
        logger.addHandler(file_handler)
        logger.propagate = False


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
        match message:
            case "usuario_updated":
                if page.app_state.usuario.get('name'):
                    # Atualiza elementos da UI que dependem do usuário
                    update_usuario_dependent_ui()
                else:
                    # Limpa elementos da UI relacionados ao usuário
                    clear_usuario_ui()
            case "empresa_updated":
                if page.app_state.empresa.get('corporate_name'):
                    # Atualiza elementos da UI que dependem da empresa
                    update_empresa_dependent_ui()
                else:
                    # Limpa elementos da UI relacionados à empresa
                    clear_empresa_ui()
            case "empresa_form_updated":
                # ToDo: Implementando módulo empresas_form() em empresas_form.py
                pass

    def update_usuario_dependent_ui():
        # Exemplo: Atualiza o nome do usuário no header
        if hasattr(page, 'user_name_text'):
            page.user_name_text.value = page.app_state.usuario['name'].nome_completo
            page.user_name_text.update()

    def update_empresa_dependent_ui():
        # Exemplo: Atualiza o nome da empresa no header
        if hasattr(page, 'company_name_text_btn'):
            page.company_name_text_btn.text = page.app_state.empresa.get(
                'name', page.app_state.empresa.get('corporate_name'))
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
                page.go('/')  # Redireciona para a página inicial
            case '/home':
                # Acesso a página /home somente usuários logados
                print(f'Acessando a página /home. Usuário id: {page.app_state.usuario.get('id')}')
                if page.app_state.usuario.get('id'):
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
                else:
                    print('Usuário não autenticado. Redirecionando para /login')
                    page.go('/login')  # Redireciona se não estiver autenticado
            case '/empresas/form':
                # Verifica se usuário está logado
                if page.app_state.usuario.get('id'):
                    route_title = "home/empresas/form"
                    empresa = page.app_state.empresa_form
                    id = empresa.get('id', None)
                    if id:
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
                        controls=[empresas_form(page)],
                        scroll=ft.ScrollMode.AUTO,
                        bgcolor=ft.Colors.BLACK,
                        vertical_alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    )
                else:
                    page.go('/login')  # Redireciona se não estiver autenticado
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

        # Adiciona a view à página, no caso das rota /logout, pg_view é None e /home, pg_view pode ser None ou não
        if pg_view:
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
    # Inicie a reconfiguração de log em uma thread separada
    threading.Thread(target=reconfigure_logging, daemon=True).start()

    # Inicia o app Flet
    ft.app(
        target=main,
        assets_dir="assets",
        upload_dir="uploads",
        view=ft.WEB_BROWSER
    )
