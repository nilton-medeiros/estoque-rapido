import logging
import traceback

import flet as ft

import src.pages.produtos.categorias_actions_page as cat_actions
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

    _all_categorias_data = []
    _categorias_inactivated_count = 0

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
                is_deleted = cat_actions.send_to_trash(page=page, categoria=categoria)
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
                margin=ft.margin.only(left=10, right=10),
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

    def _get_filtered_categorias() -> list:
        """Filtra _all_categorias_data com base no valor de rg_filter."""
        nonlocal _all_categorias_data # Acessa a variável do escopo de cat_grid_view
        current_filter = rg_filter.value

        if current_filter == "all":
            return _all_categorias_data
        elif current_filter == "active":
            # Assumindo que categoria.status.name pode ser 'ACTIVE', 'INACTIVE', etc.
            return [cat for cat in _all_categorias_data if cat.status.name == 'ACTIVE']
        elif current_filter == "inactive": # "Descontinuado"
            return [cat for cat in _all_categorias_data if cat.status.name == 'INACTIVE']
        return []

    def _render_grid(categorias_to_display: list):
        """Constrói e exibe o grid de categorias ou a mensagem de vazio."""
        nonlocal content_area, empty_content_display, handle_action_click # Acessa controles e handlers

        content_area.controls.clear()
        if not categorias_to_display:
            content_area.controls.append(empty_content_display)
        else:
            grid = ft.ResponsiveRow(
                controls=[
                    ft.Card(
                        content=ft.Container(
                            padding=15,
                            content=ft.Column([
                                ft.Row(
                                    controls=[
                                        ft.Container( # Container para a imagem da categoria
                                            width=100,
                                            height=100,
                                            border_radius=ft.border_radius.all(10),
                                            border=ft.border.all(1, ft.colors.OUTLINE) if not categoria.image_url else None,
                                            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                                            alignment=ft.alignment.center,
                                            content=ft.Image(
                                                src=categoria.image_url,
                                                fit=ft.ImageFit.COVER,
                                                width=100,
                                                height=100,
                                                border_radius=ft.border_radius.all(10),
                                                error_content=ft.Icon(ft.icons.IMAGE_NOT_SUPPORTED_OUTLINED, size=30, color=ft.colors.ERROR)
                                            ) if categoria.image_url else ft.Icon(ft.icons.CATEGORY_OUTLINED, size=40, opacity=0.5)
                                        ),
                                        ft.Container(
                                            content=ft.PopupMenuButton(
                                                icon=ft.Icons.MORE_VERT, tooltip="Mais Ações",
                                                items=[
                                                    ft.PopupMenuItem(
                                                        text="Editar categoria", tooltip="Ver ou editar dados da categoria",
                                                        icon=ft.Icons.EDIT_NOTE_OUTLINED,
                                                        data={'action': 'EDIT', 'data': categoria},
                                                        on_click=handle_action_click
                                                    ),
                                                    ft.PopupMenuItem(
                                                        text="Excluir categoria", tooltip="Move categoria para a lixeira, após 90 dias remove do banco de dados",
                                                        icon=ft.Icons.DELETE_OUTLINE,
                                                        data={'action': 'SOFT_DELETE', 'data': categoria},
                                                        on_click=handle_action_click
                                                    ),
                                                ],
                                            ),
                                        ),
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                ),
                                ft.Text(f"{categoria.name}", weight=ft.FontWeight.BOLD),
                                ft.Text(f"{categoria.description if categoria.description else '<Sem descrição>'}",
                                        theme_style=ft.TextThemeStyle.BODY_MEDIUM),
                                ft.Row(
                                    controls=[
                                        ft.Text(
                                            value=f"Status: {categoria.status.value}", # Ex: "Ativo", "Descontinuado"
                                            theme_style=ft.TextThemeStyle.BODY_SMALL,
                                            color=ft.Colors.GREEN if categoria.status.name == 'ACTIVE' else ft.Colors.RED,
                                        ),
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                ),
                            ])
                        ),
                        margin=ft.margin.all(5),
                        col={"xs": 12, "sm": 6, "md": 4, "lg": 3}
                    ) for categoria in categorias_to_display
                ],
                columns=12, spacing=10, run_spacing=10
            )
            content_area.controls.append(grid)

    async def radiogroup_changed(e):
        """Chamado quando o valor do RadioGroup muda. Filtra e renderiza o grid."""
        nonlocal page # Acessa page para update
        filtered_categorias = _get_filtered_categorias()
        _render_grid(filtered_categorias)
        if page.client_storage:
            page.update()

    rg_filter = ft.RadioGroup(
        value="all",  # Valor inicial do filtro
        content=ft.Row(
            controls=[
                ft.Radio(value="all", label="Todos"),
                ft.Radio(value="active", label="Ativos"),
                ft.Radio(value="inactive", label="Descontinuado"),
            ]
        ),
        on_change=radiogroup_changed, # Conecta a função handler
    )
    # Adiciona o rg_filter às ações do AppBar agora que radiogroup_changed está definida
    appbar.actions.insert(0, rg_filter)  # type: ignore [attr-defined]

    async def load_data_and_update_ui():
        """Carrega todos os dados do banco, armazena, filtra e atualiza a UI."""
        nonlocal _all_categorias_data, _categorias_inactivated_count, loading_container, content_area, page, fab

        loading_container.visible = True
        content_area.visible = False
        if page.client_storage:
            page.update() # Mostra o spinner

        # Limpa os dados armazenados antes de buscar novos
        _all_categorias_data = []
        _categorias_inactivated_count = 0

        # empresa_id: ID da empresa logada para buscar as categorias desta empresa
        empresa_id = page.app_state.empresa['id'] # type: ignore

        try:
            # *** IMPORTANTE: Garanta que handle_get_empresas seja async ***
            # Se handle_get_empresas for síncrona e demorar, a UI *vai* congelar.
            # Pode ser necessário refatorar handle_get_all para usar um driver de banco de dados async
            # ou executá-la em uma thread separada usando asyncio.to_thread (Python 3.9+)
            # Exemplo usando asyncio.to_thread se handle_get_all for sync:
            # categorias_data = await asyncio.to_thread(handle_get_all, empresa_id=empresa_id)

            if not empresa_id:  # Só busca as categorias de empresa logada, se houver ID

            # Ou apenas adicione os cards diretamente à Coluna se preferir uma lista vertical
            # content_area.controls.extend(cards)
                # _all_categorias_data já está vazio, _render_grid mostrará empty_content_display
                pass
            else:
                # Busca as categorias menos as de status 'DELETED' da empresa logada
                result: dict = cat_controllers.handle_get_all(empresa_id=empresa_id)

                if result["status"] == "error":
                    logger.error(f"Erro ao buscar categorias: {result.get('message', 'Desconhecido')}")
                    # _all_categorias_data permanece vazio, _render_grid mostrará empty_content_display
                    # Ou podemos exibir uma mensagem de erro específica aqui:
                    content_area.controls.clear()
                    content_area.controls.append(
                        ft.Container(
                            content=ft.Text(f"Erro ao carregar dados: {result.get('message', 'Tente novamente mais tarde.')}", color=ft.colors.ERROR),
                            alignment=ft.alignment.center,
                            margin=ft.margin.only(top=50)
                        )
                    )
                else:
                    _all_categorias_data = result['data']["categorias"]
                    _categorias_inactivated_count = result['data']["deleted"]

            # Atualiza o ícone e tooltip do FAB
            current_trash_icon_filename = "recycle_full_1771.png" if _categorias_inactivated_count else "recycle_empy_1771.png"
            if fab.content and isinstance(fab.content, ft.Image): # Garante que fab.content é uma Image
                fab.content.src = f"icons/{current_trash_icon_filename}"
                fab.tooltip = f"Categorias inativas: {_categorias_inactivated_count}"

            # Filtra os dados carregados (ou vazios) e renderiza o grid
            filtered_categorias = _get_filtered_categorias()
            _render_grid(filtered_categorias)

        except Exception as e:
            # Mostrar uma mensagem de erro para o usuário
            tb_str = traceback.format_exc()
            logger.error(f"Ocorreu um erro ao carregar as categorias de produtos. Tipo: {type(e).__name__}, Erro: {e}\nTraceback:\n{tb_str}")

            content_area.controls.clear()
            _all_categorias_data = [] # Limpa dados em caso de erro geral
            _categorias_inactivated_count = 0
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
