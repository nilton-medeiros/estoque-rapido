import logging
import traceback

import flet as ft

import src.pages.produtos.categorias_actions as cat_actions
import src.domains.produtos.controllers.categorias_controllers as cat_controllers


logger = logging.getLogger(__name__)


def cat_grid_view(page: ft.Page):
    """Página de exibição das categorias de produtos da empresa logada"""
    page.theme_mode = ft.ThemeMode.DARK
    page.data = "/home/produtos/categorias/grid"

        # --- Indicador de Carregamento (Spinner) ---
    loading_container = ft.Container(
        content=ft.ProgressRing(width=32, height=32, stroke_width=3),
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

    async def handle_action_click(e):
        """Função para lidar com cliques nas ações do menu ou botões."""
        action = e.control.data.get('action')
        categoria = e.control.data.get('data')

        match action:
            case "INSERT":
                # Garante que ao entrar no formulário principal, os campos estejam vazio
                page.app_state.clear_form_data() # type: ignore
                page.go('/home/produtos/categorias/form')
            case "EDIT":
                page.app_state.set_form_data(categoria.to_dict()) # type: ignore
                page.go('/home/produtos/categorias/form')
            case "SOFT_DELETE":
                is_deleted = await cat_actions.send_to_trash(page=page, categoria=categoria)
                if is_deleted:
                    # Reexecuta o carregamento. Atualizar a lista de empresas na tela
                    page.run_task(load_data_and_update_ui)
                    # Não precisa de page.update() aqui, pois run_task já fará isso
            case _:
                pass

    def handle_icon_hover(e):
        """Muda o bgcolor do container no hover."""
        e.control.bgcolor = ft.Colors.with_opacity(0.1, ft.Colors.WHITE) if e.data == "true" else ft.Colors.TRANSPARENT
        e.control.update()

    appbar = ft.AppBar(
        leading=ft.Container(
            alignment=ft.alignment.center_left,
            padding=ft.padding.only(left=10),
            content=ft.Container(
                width=40,
                height=40,
                border_radius=ft.border_radius.all(20),
                ink=True,
                bgcolor=ft.Colors.TRANSPARENT,
                alignment=ft.alignment.center,
                on_hover=handle_icon_hover,
                content=ft.Icon(
                    ft.Icons.ARROW_BACK),
                on_click=lambda _: page.go("/home"), tooltip="Voltar",
                clip_behavior=ft.ClipBehavior.ANTI_ALIAS
            ),
        ),
        title=ft.Text(f"Categorias de Produtos", size=18),
        bgcolor=ft.Colors.with_opacity(0.9, ft.Colors.PRIMARY_CONTAINER),
        adaptive=True,
        actions=[
            ft.Container(
                width=43,
                height=43,
                border_radius=ft.border_radius.all(20), # Metade da largura/altura para ser círculo
                ink=True,
                bgcolor=ft.Colors.TRANSPARENT,
                alignment=ft.alignment.center,
                on_hover=handle_icon_hover,
                content=ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE, size=30),
                tooltip="Adicionar nova categoria",
                data={'action': 'INSERT', 'data': None},
                on_click=handle_action_click,
                margin=ft.margin.only(right=10),
                clip_behavior=ft.ClipBehavior.ANTI_ALIAS # Boa prática adicionar aqui também
            ),
        ],
    )

    # --- Conteúdo Padrão Vazio (definido uma vez) ---
    empty_content_display = ft.Container(
        content=ft.Image(
            # src=f"images/empty_folder.png",
            src=f"images/empty_folder.png",
            error_content=ft.Text("Nenhuma categoria cadastrada"),
            width=300,
            height=300,
            fit=ft.ImageFit.CONTAIN,
            border_radius=ft.border_radius.all(10),
        ),
        margin=ft.margin.only(top=100),
        alignment=ft.alignment.center,
    )

    # --- Função Assíncrona para Carregar Dados e Atualizar a UI ---
    async def load_data_and_update_ui():
        categorias_data = []
        categorias_inactivated = 0

        # empresa_id: ID da empresa logada para buscar as categorias desta empresa
        empresa_id = page.app_state.empresa['id'] # type: ignore

        try:
            # *** IMPORTANTE: Garanta que handle_get_empresas seja async ***
            # Se handle_get_empresas for síncrona e demorar, a UI *vai* congelar.
            # Pode ser necessário refatorar handle_get_all para usar um driver de banco de dados async
            # ou executá-la em uma thread separada usando asyncio.to_thread (Python 3.9+)
            # Exemplo usando asyncio.to_thread se handle_get_all for sync:
            # categorias_data = await asyncio.to_thread(handle_get_all, empresa_id=empresa_id)

            if empresa_id:  # Só busca as categorias de empresa logada, se houver ID
                # Busca as categorias menos as de status 'DELETED' da empresa logada
                result: dict = await cat_controllers.handle_get_all(empresa_id=empresa_id)
                categorias_data: list = result['data_list']
                categorias_inactivated: int = result['deleted']

            # --- Construir Conteúdo Baseado nos Dados ---
            content_area.controls.clear()  # Limpar conteúdo anterior
            if not categorias_data:  # Checa se a lista é vazia ou None
                # Mostra uma imagem de pasta vazia
                content_area.controls.append(empty_content_display)
                return

            # Usar ResponsiveRow para um layout de grid responsivo
            # Ajuste colunas para diferentes tamanhos de tela
            # --- Constroe o Grid de Cards ---
            grid = ft.ResponsiveRow(
                controls=[
                    # O componente Card() está sendo iterado em loop para uma ou mais categorias.
                    # Por isso, não é possível movê-lo para uma variável para reduzir o nível de aninhamento.
                    ft.Card(
                        content=ft.Container(
                            padding=15,
                            content=ft.Column([
                                ft.Row(
                                    controls=[
                                        ft.Text(
                                            f"{categoria.name}", weight=ft.FontWeight.BOLD),
                                        # Container do PopMenuButton para não deixar colado com a margem direita de Column
                                        ft.Container(
                                            # padding=ft.padding.only(right=5),
                                            content=ft.PopupMenuButton(
                                                icon=ft.Icons.MORE_VERT, tooltip="Mais Ações",
                                                items=[
                                                    ft.PopupMenuItem(
                                                        text="Editar categoria",
                                                        tooltip="Ver ou editar dados da categoria",
                                                        icon=ft.Icons.EDIT_NOTE_OUTLINED,
                                                        data={
                                                            'action': 'EDIT', 'data': categoria},
                                                        on_click=handle_action_click
                                                    ),
                                                    ft.PopupMenuItem(
                                                        text="Excluir categoria",
                                                        tooltip="Move categoria para a lixeira, após 90 dias remove do banco de dados",
                                                        icon=ft.Icons.DELETE_OUTLINE,
                                                        data={
                                                            'action': 'SOFT_DELETE', 'data': categoria},
                                                        on_click=handle_action_click
                                                    ),
                                                ],
                                            ),
                                        ),
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                ),
                                ft.Text(f"{categoria.description if categoria.description else '<Sem descrição>'}",
                                        theme_style=ft.TextThemeStyle.BODY_MEDIUM),
                                ft.Row(
                                    controls=[
                                        ft.Text(
                                            value=f"Status: {"ATIVO" if categoria.status.ACTIVE else 'OBSOLETO'}",
                                            theme_style=ft.TextThemeStyle.BODY_SMALL
                                        ),
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                ),
                            ])
                        ),
                        margin=ft.margin.all(5),
                        # Configuração responsiva para cada card
                        # Cada card com sua própria configuração de colunas
                        col={"xs": 12, "sm": 6, "md": 4, "lg": 3}
                    ) for categoria in categorias_data  # Criar um card para cada categoria
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
            tb_str = traceback.format_exc()
            logger.error(f"Ocorreu um erro ao carregar as categorias de produtos. Tipo: {type(e).__name__}, Erro: {e}\nTraceback:\n{tb_str}")

            content_area.controls.clear()
            content_area.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.ERROR_OUTLINE,
                                color=ft.Colors.RED, size=50),
                        ft.Text(
                            f"Ocorreu um erro ao carregar as categorias de produtos.", color=ft.Colors.RED),
                        # Mensagem de erro mais informativa na UI
                        ft.Text(f"Detalhes: Erro do tipo '{type(e).__name__}'. Mensagem: '{str(e)}'. Consulte os logs para mais informações.",
                                color=ft.Colors.RED, size=10, selectable=True),
                    ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    alignment=ft.alignment.center,
                    margin=ft.margin.only(top=50),
                    expand=True
                )
            )
        finally:
            # --- Atualizar Visibilidade da UI ---
            # Mostra uma lixeira vazia ou cheia
            current_trash_icon_filename = "recycle_full_1771.png" if categorias_inactivated else "recycle_empy_1771.png"

            if fab.content and isinstance(fab.content, ft.Image): # Garante que fab.content é uma Image
                fab.content.src = f"icons/{current_trash_icon_filename}"
                fab.tooltip = f"Categorias inativas: {categorias_inactivated}"

            loading_container.visible = False
            content_area.visible = True
            if page.client_storage:  # Uma checagem se a página ainda está ativa
                page.update()
            else:
                logger.info("Contexto da página perdido, não foi possível atualizar.")
                print("Contexto da página perdido, não foi possível atualizar.")

    # --- Disparar Carregamento dos Dados ---
    # Executa a função async em background. A UI mostrará o spinner primeiro.
    page.run_task(load_data_and_update_ui)

    fab = ft.FloatingActionButton(
        # icon=ft.Icons.FOLDER_DELETE_OUTLINED,
        content=ft.Image(
            # src="icons/recycle_empty_delete_trash_1771.png",
            src=f"icons/recycle_empy_1771.png",
            width=48,
            height=36,
            fit=ft.ImageFit.CONTAIN,
            error_content=ft.Text("Erro"),
        ),
        on_click=lambda _: page.go("/home/produtos/categorias/grid/lixeira"),
        tooltip="Categorias inativas: 0",
        bgcolor=ft.Colors.TRANSPARENT,
    )

    # Resetar alinhamentos da página que podem interferir com o layout da View
    # page.vertical_alignment = ft.MainAxisAlignment.START
    # page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH

    # --- Retornar Estrutura Inicial da Página como ft.View ---
    # A View inclui a AppBar e a área de conteúdo principal (que inicialmente mostra o spinner)
    return ft.View(
        route="/home/produtos/categorias/grid",  # A rota que esta view corresponde
        controls=[
            loading_container,  # Mostra o spinner inicialmente
            content_area       # Oculto inicialmente, populado por load_data_and_update_ui
        ],
        appbar=appbar,
        floating_action_button=fab,
        vertical_alignment=ft.MainAxisAlignment.START,  # Alinha conteúdo ao topo
        # Deixa o conteúdo esticar horizontalmente
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        # Adiciona um padding ao redor da área de conteúdo
        padding=ft.padding.all(10)
    )
