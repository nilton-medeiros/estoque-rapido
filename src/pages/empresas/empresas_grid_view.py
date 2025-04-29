import logging

import flet as ft
# import asyncio  # Importar asyncio se precisar simular delays ou usar recursos async

import src.domains.empresas.controllers.empresas_controllers as empresas_controllers
import src.pages.empresas.empresas_actions as empresas_actions
# Rota: /home/empresas/grid

logger = logging.getLogger(__name__)


def empresas_grid(page: ft.Page):
    """Página de exibição das empresas do usuário logado em formato Cards"""
    page.theme_mode = ft.ThemeMode.DARK
    page.data = "/home/empresas/grid"
    print(f"Debug  ->  Entrou em {page.data}")
    # Resetar alinhamentos da página que podem interferir com o layout da View
    # page.vertical_alignment = ft.MainAxisAlignment.START
    # page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH

    # --- Indicador de Carregamento (Spinner) ---
    progress_ring = ft.ProgressRing(width=32, height=32, stroke_width=3)
    loading_container = ft.Container(
        content=progress_ring,
        alignment=ft.alignment.center,
        expand=True,  # Ocupa o espaço disponível enquanto carrega
        visible=True  # Começa visível
    )

    # --- Área para o Conteúdo Real (Grid ou Imagem Vazia) ---
    # Usando uma Coluna para conter a imagem vazia ou o grid posteriormente
    content_area = ft.Column(
        controls=[],  # Começa vazia
        alignment=ft.MainAxisAlignment.START,  # Ou CENTER
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        expand=True,
        visible=False,  # Começa oculta
        scroll=ft.ScrollMode.ADAPTIVE  # Permite rolagem se o conteúdo exceder
    )

    # --- Conteúdo Padrão Vazio (definido uma vez) ---
    empty_content_display = ft.Container(
        content=ft.Image(
            src=f"images/empty_folder.png",
            error_content=ft.Text("Nenhuma empresa cadastrada"),
            width=300,
            height=300,
            fit=ft.ImageFit.COVER,
            border_radius=ft.border_radius.all(10),
        ),
        margin=ft.margin.only(top=100),
        alignment=ft.alignment.center,
    )

    # --- Definição da AppBar (permanece a mesma) ---
    def handle_icon_hover(e):
        """Muda o bgcolor do container no hover."""
        e.control.bgcolor = ft.Colors.with_opacity(
            0.1, ft.Colors.WHITE) if e.data == "true" else ft.Colors.TRANSPARENT
        e.control.update()

    def handle_action_click(e):
        """Função para lidar com cliques nas ações do menu ou botões."""
        action = e.control.data.get('action')
        empresa = e.control.data.get('data')

        print(f"action: {action}")

        match action:
            case "INCLUIR":
                print("Debug:  ->  Incluir: Redirecionando para '/home/empresas/form'")
                page.go('/home/empresas/form')
            case "EXCLUIR":
                print(f"Excluir {empresa.id}")
                is_deleted = empresas_actions.delete(empresa, e.control.page)
                if is_deleted:
                    # Reexecuta o carregamento. Atualizar a lista de empresas na tela
                    print("Atualizando a grade de empresas")
                    page.run_task(load_data_and_update_ui)
                    # Não precisa de page.update() aqui, pois run_task já fará isso
            case _:
                pass

    appbar = ft.AppBar(
        leading=ft.Container(
            alignment=ft.alignment.center_left,
            padding=ft.padding.only(left=10),
            content=ft.Container(
                width=40, height=40, border_radius=ft.border_radius.all(20),
                ink=True, bgcolor=ft.Colors.TRANSPARENT, alignment=ft.alignment.center,
                on_hover=handle_icon_hover, content=ft.Icon(
                    ft.Icons.ARROW_BACK),
                on_click=lambda _: page.go("/home"), tooltip="Voltar",
                clip_behavior=ft.ClipBehavior.ANTI_ALIAS
            ),
        ),
        title=ft.Text("Empresas"),
        bgcolor=ft.Colors.with_opacity(0.9, ft.Colors.PRIMARY_CONTAINER),
        adaptive=True,
        actions=[
            ft.Container(
                padding=ft.padding.only(right=10),
                content=ft.IconButton(
                    icon=ft.Icons.ADD_CIRCLE_OUTLINE, tooltip="Incluir Nova Empresa",
                    data={'action': 'INCLUIR', 'data': None},
                    on_click=handle_action_click,
                ),
            ),
        ],
    )

    # --- Função Assíncrona para Carregar Dados e Atualizar a UI ---
    async def load_data_and_update_ui():
        empresas_data = []

        # set_empresas: Conjunto de ID's de empresas que o usuário gerencia
        set_empresas = page.app_state.usuario.get(
            'empresas', [])  # Usar get com default

        try:
            # *** IMPORTANTE: Garanta que handle_get_empresas seja async ***
            # Se handle_get_empresas for síncrona e demorar, a UI *vai* congelar.
            # Pode ser necessário refatorar handle_get_empresas para usar um driver de banco de dados async
            # ou executá-la em uma thread separada usando asyncio.to_thread (Python 3.9+)
            # Exemplo usando asyncio.to_thread se handle_get_empresas for sync:
            # empresas_data = await asyncio.to_thread(handle_get_empresas, ids_empresas=set_empresas)

            if set_empresas:  # Só busca se houver IDs
                result = await empresas_controllers.handle_get_empresas(ids_empresas=set_empresas)
                empresas_data = result.get('data_list', [])
            else:
                empresas_data = []  # Se não há IDs, a lista está vazia

            # --- Construir Conteúdo Baseado nos Dados ---
            content_area.controls.clear()  # Limpar conteúdo anterior
            if not empresas_data:  # Checa se a lista é vazia ou None
                content_area.controls.append(empty_content_display)
            else:
                # Usar ResponsiveRow para um layout de grid responsivo
                # Ajuste colunas para diferentes tamanhos de tela
                # --- Construir o Grid de Cards ---

                grid = ft.ResponsiveRow(
                    controls=[
                        ft.Card(
                            content=ft.Container(
                                padding=15,
                                content=ft.Column([
                                    ft.Row(
                                        controls=[
                                            ft.Text(
                                                f"{empresa.corporate_name}", weight=ft.FontWeight.BOLD),
                                            # Container do PopMenuButton para não deixar colado com a margem direita de Column
                                            ft.Container(
                                                # padding=ft.padding.only(right=5),
                                                content=ft.PopupMenuButton(
                                                    icon=ft.Icons.MORE_VERT, tooltip="Mais Ações",
                                                    items=[
                                                        ft.PopupMenuItem(text="Dados Principais", icon=ft.Icons.EDIT_NOTE_OUTLINED, data={
                                                                         'action': 'PRINCIPAL', 'data': empresa}, on_click=handle_action_click),
                                                        ft.PopupMenuItem(
                                                            text="Nota Fiscal", icon=ft.Icons.RECEIPT_LONG_OUTLINED, data={'action': 'FISCAL', 'data': empresa}, on_click=handle_action_click),
                                                        ft.PopupMenuItem(text="Certificado Digital", icon=ft.Icons.SECURITY_OUTLINED, data={
                                                                         'action': 'CERTIFICADO', 'data': empresa}, on_click=handle_action_click),
                                                        ft.PopupMenuItem(
                                                            text="Excluir Empresa", icon=ft.Icons.DELETE_OUTLINE, data={'action': 'EXCLUIR', 'data': empresa}, on_click=handle_action_click),
                                                    ],
                                                ),
                                            ),
                                        ],
                                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                    ),
                                    ft.Text(f"{empresa.trade_name if empresa.trade_name else 'Nome fantasia N/A'}",
                                            theme_style=ft.TextThemeStyle.BODY_MEDIUM),
                                    ft.Text(f"{empresa.store_name if empresa.store_name else 'Loja N/A'}  {str(empresa.phone) if empresa.phone else ''}",
                                            theme_style=ft.TextThemeStyle.BODY_MEDIUM),
                                    ft.Text(
                                        f"CNPJ: {empresa.cnpj if empresa.cnpj else 'N/A'}", theme_style=ft.TextThemeStyle.BODY_MEDIUM),
                                    ft.Text(
                                        f"Email: {empresa.email}", theme_style=ft.TextThemeStyle.BODY_SMALL),
                                ])
                            ),
                            margin=ft.margin.all(5),
                            # Configuração responsiva para cada card
                            # Cada card com sua própria configuração de colunas
                            col={"xs": 12, "sm": 6, "md": 4, "lg": 3}
                        ) for empresa in empresas_data  # Criar um card para cada empresa
                    ],
                    columns=12,  # Total de colunas no sistema de grid
                    spacing=10,  # Espaço horizontal entre os cards
                    run_spacing=10  # Espaço vertical entre as linhas
                )
                content_area.controls.append(grid)
                # Ou apenas adicione os cards diretamente à Coluna se preferir uma lista vertical
                # content_area.controls.extend(cards)

        except Exception as e:
            # Mostrar uma mensagem de erro para o usuário
            content_area.controls.clear()
            content_area.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.icons.ERROR_OUTLINE,
                                color=ft.colors.RED, size=50),
                        ft.Text(
                            f"Ocorreu um erro ao carregar as empresas.", color=ft.colors.RED),
                        # Cuidado ao expor detalhes de erro
                        ft.Text(f"Detalhes: {e}",
                                color=ft.colors.RED, size=10),
                    ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    alignment=ft.alignment.center,
                    margin=ft.margin.only(top=50),
                    expand=True
                )
            )
        finally:
            # --- Atualizar Visibilidade da UI ---
            loading_container.visible = False
            content_area.visible = True
            # Importante: Atualizar a página para refletir as mudanças
            # Checar se o contexto da página ainda é válido antes de atualizar
            if page.client_storage:  # Uma checagem se a página ainda está ativa
                page.update()
            else:
                print("Contexto da página perdido, não foi possível atualizar.")

    # --- Disparar Carregamento dos Dados ---
    # Executa a função async em background. A UI mostrará o spinner primeiro.
    page.run_task(load_data_and_update_ui)

    # --- Retornar Estrutura Inicial da Página como ft.View ---
    # A View inclui a AppBar e a área de conteúdo principal (que inicialmente mostra o spinner)
    return ft.View(
        route="/home/empresas/grid",  # A rota que esta view corresponde
        controls=[
            loading_container,  # Mostra o spinner inicialmente
            content_area       # Oculto inicialmente, populado por load_data_and_update_ui
        ],
        appbar=appbar,
        vertical_alignment=ft.MainAxisAlignment.START,  # Alinha conteúdo ao topo
        # Deixa o conteúdo esticar horizontalmente
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        # Adiciona um padding ao redor da área de conteúdo
        padding=ft.padding.all(10)
    )

    # ft.View(
    #     scroll=ft.ScrollMode.AUTO,
    #     bgcolor=ft.Colors.BLACK,
    # )

# Nota: Garanta que a função `handle_get_empresas` localizada em
# `src.domains.empresas.controllers.empresas_controllers` esteja definida como uma função `async def`
# para que esta abordagem de indicador de carregamento funcione sem congelar a UI durante a chamada ao banco de dados.
# Se for uma função síncrona, você precisará adaptá-la usando técnicas como
# `asyncio.to_thread` conforme mostrado nos comentários dentro de `load_data_and_update_ui`.
