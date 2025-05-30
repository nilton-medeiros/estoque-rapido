import logging
import traceback

import flet as ft

from src.domains.produtos.models import ProdutoStatus
import src.pages.produtos.produtos_actions_page as pro_actions
import src.domains.produtos.controllers.produtos_controllers as product_controllers

logger = logging.getLogger(__name__)


def show_products_grid(page: ft.Page):
    """Página de exibição dos produtos da empresa logada"""
    page.theme_mode = ft.ThemeMode.DARK
    page.data = "/home/produtos/grid"

    # --- Indicador de Carregamento (Spinner) ---
    loading_container = ft.Container(
        content=ft.ProgressRing(width=32, height=32, stroke_width=3),
        alignment=ft.alignment.center,
        expand=True,  # Ocupa o espaço disponível enquanto carrega
        visible=True  # Começa visível
    )

    _all_produtos_data = []
    _produtos_inactivated_count = 0

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
        produto = e.control.data.get('data')

        match action:
            case "INSERT":
                # Garante que ao entrar no formulário principal, os campos estejam vazio
                page.app_state.clear_form_data() # type: ignore  [attr: defined]
                page.go('/home/produtos/form')
            case "EDIT":
                page.app_state.set_form_data(produto.to_dict()) # type: ignore  [attr: defined]
                page.go('/home/produtos/form')
            case "SOFT_DELETE":
                is_deleted = await pro_actions.send_to_trash(page=page, produto=produto)
                if is_deleted:
                    # Reexecuta o carregamento. Atualizar a lista de empresas na tela
                    page.run_task(load_data_and_update_ui)
                    # Não precisa de page.update() aqui, pois run_task já fará isso
            case _:
                pass

    def handle_icon_hover(e):
        """Muda o bgcolor do container no hover."""
        e.control.bgcolor = ft.Colors.with_opacity(
            0.1, ft.Colors.WHITE) if e.data == "true" else ft.Colors.TRANSPARENT
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
        title=ft.Text(f"Produtos", size=18),
        bgcolor=ft.Colors.with_opacity(0.9, ft.Colors.PRIMARY_CONTAINER),
        adaptive=True,
        actions=[],
    )

    # --- Conteúdo Padrão Vazio (definido uma vez) ---
    empty_content_display = ft.Container(
        content=ft.Image(
            src=f"images/empty_folder.png",
            error_content=ft.Text("Nenhuma produto cadastrado"),
            width=300,
            height=300,
            fit=ft.ImageFit.CONTAIN,
            border_radius=ft.border_radius.all(10),
        ),
        margin=ft.margin.only(top=100),
        alignment=ft.alignment.center,
    )

    def _get_filtered_produtos() -> list:
        """Filtra _all_produtos_data com base no valor de rg_filter."""
        nonlocal _all_produtos_data  # Acessa a variável do escopo de show_products_grid
        current_filter = rg_filter.value

        if current_filter == "all":
            return _all_produtos_data
        elif current_filter == "active":
            # Assumindo que produto.status.name pode ser 'ACTIVE', 'INACTIVE', etc.
            return [pro for pro in _all_produtos_data if pro.status.name == 'ACTIVE']
        elif current_filter == "inactive":  # "Descontinuado"
            return [pro for pro in _all_produtos_data if pro.status.name == 'INACTIVE']
        return []

    def _render_grid(produtos_to_display: list):
        """Constrói e exibe o grid de produtos ou a mensagem de vazio."""
        nonlocal content_area, empty_content_display, handle_action_click  # Acessa controles e handlers

        content_area.controls.clear()
        if not produtos_to_display:
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
                                        ft.Container(  # Container para a imagem da produto
                                            width=100,
                                            height=100,
                                            border_radius=ft.border_radius.all(
                                                10),
                                            border=ft.border.all(
                                                1, ft.Colors.OUTLINE) if not produto.image_url else None,
                                            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                                            alignment=ft.alignment.center,
                                            content=ft.Image(
                                                src=f"{produto.image_url}",
                                                fit=ft.ImageFit.COVER,
                                                width=100,
                                                height=100,
                                                border_radius=ft.border_radius.all(
                                                    10),
                                                error_content=ft.Icon(
                                                    ft.Icons.IMAGE_NOT_SUPPORTED_OUTLINED, size=30, color=ft.Colors.ERROR)
                                            ) if produto.image_url else ft.Icon(ft.Icons.CATEGORY_OUTLINED, size=40, opacity=0.5)
                                        ),
                                        ft.Text(
                                            f"{produto.categoria_name}", weight=ft.FontWeight.BOLD, theme_style=ft.TextThemeStyle.BODY_LARGE),
                                        # Empurra o próximo controler até o limite
                                        ft.Container(expand=True),
                                        ft.Container(
                                            content=ft.PopupMenuButton(
                                                icon=ft.Icons.MORE_VERT, tooltip="Mais Ações",
                                                items=[
                                                    ft.PopupMenuItem(
                                                        text="Editar produto", tooltip="Ver ou editar dados da produto",
                                                        icon=ft.Icons.EDIT_NOTE_OUTLINED,
                                                        data={
                                                            'action': 'EDIT', 'data': produto},
                                                        on_click=handle_action_click
                                                    ),
                                                    ft.PopupMenuItem(
                                                        text="Excluir produto", tooltip="Move produto para a lixeira, após 90 dias remove do banco de dados",
                                                        icon=ft.Icons.DELETE_OUTLINE,
                                                        data={
                                                            'action': 'SOFT_DELETE', 'data': produto},
                                                        on_click=handle_action_click
                                                    ),
                                                ],
                                            ),
                                        ),
                                    ],
                                    alignment=ft.MainAxisAlignment.START,
                                ),
                                ft.Text(f"{produto.name}", weight=ft.FontWeight.BOLD,
                                        theme_style=ft.TextThemeStyle.BODY_MEDIUM, no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS),
                                ft.Text(f"{produto.description.replace('\n', ' ')}",
                                        theme_style=ft.TextThemeStyle.BODY_SMALL, no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS),
                                ft.Text(f"{produto.sale_price}",
                                        theme_style=ft.TextThemeStyle.BODY_SMALL),
                                ft.Row(
                                    controls=[
                                        ft.Text(
                                            # Ex: "Ativo", "Descontinuado"
                                            value=f"Status: {produto.status.value}",
                                            theme_style=ft.TextThemeStyle.BODY_SMALL,
                                            color=ft.Colors.GREEN if produto.status == ProdutoStatus.ACTIVE else ft.Colors.RED,
                                        ),
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                ),
                            ])
                        ),
                        margin=ft.margin.all(5),
                        col={"xs": 12, "sm": 6, "md": 4, "lg": 3}
                    ) for produto in produtos_to_display
                ],
                columns=12, spacing=10, run_spacing=10
            )
            content_area.controls.append(grid)

    async def radiogroup_changed(e):
        """Chamado quando o valor do RadioGroup muda. Filtra e renderiza o grid."""
        nonlocal page  # Acessa page para update
        filtered_produtos = _get_filtered_produtos()
        _render_grid(filtered_produtos)
        if page.client_storage:
            page.update()

    rg_filter = ft.RadioGroup(
        value="all",  # Valor inicial do filtro
        content=ft.Row(
            controls=[
                ft.Radio(value="all", label="Todos"),
                ft.Radio(value="active", label="Ativos"),
                ft.Radio(value="inactive", label="Descontinuados"),
            ]
        ),
        on_change=radiogroup_changed,  # Conecta a função handler
    )
    # Adiciona o rg_filter às ações do AppBar agora que radiogroup_changed está definida
    appbar.actions.insert(0, ft.Container(  # type: ignore [attr-defined]
        bgcolor=ft.Colors.TRANSPARENT,
        alignment=ft.alignment.center,
        content=rg_filter,
        margin=ft.margin.only(left=10, right=10),
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS
    )
    )

    async def load_data_and_update_ui():
        """Carrega todos os dados do banco, armazena, filtra e atualiza a UI."""
        nonlocal _all_produtos_data, _produtos_inactivated_count, loading_container, content_area, page, fab_trash

        loading_container.visible = True
        content_area.visible = False
        if page.client_storage:
            page.update()  # Mostra o spinner

        # Limpa os dados armazenados antes de buscar novos
        _all_produtos_data = []
        _produtos_inactivated_count = 0

        # empresa_id: ID da empresa logada para buscar as produtos desta empresa
        empresa_id = page.app_state.empresa['id'] # type: ignore [attr-defined]

        try:
            # *** IMPORTANTE: Garanta que handle_get_empresas seja async ***
            # Se handle_get_empresas for síncrona e demorar, a UI *vai* congelar.
            # Pode ser necessário refatorar handle_get_all para usar um driver de banco de dados async
            # ou executá-la em uma thread separada usando asyncio.to_thread (Python 3.9+)
            # Exemplo usando asyncio.to_thread se handle_get_all for sync:
            # produtos_data = await asyncio.to_thread(handle_get_all, empresa_id=empresa_id)

            if not empresa_id:  # Só busca as produtos de empresa logada, se houver ID

                # Ou apenas adicione os cards diretamente à Coluna se preferir uma lista vertical
                # content_area.controls.extend(cards)
                # _all_produtos_data já está vazio, _render_grid mostrará empty_content_display
                pass
            else:
                # Busca as produtos menos as de status 'DELETED' da empresa logada
                result: dict = product_controllers.handle_get_all(
                    empresa_id=empresa_id)

                if result["status"] == "error":
                    logger.error(
                        f"Error: produtos_grid_page()/load_data_and_update_ui(): {result['message']}")
                    # _all_produtos_data permanece vazio, _render_grid mostrará empty_content_display
                    # Ou podemos exibir uma mensagem de erro específica aqui:
                    content_area.controls.clear()
                    content_area.controls.append(
                        ft.Container(
                            content=ft.Text(
                                f"Erro ao carregar dados: {result.get('message', 'Tente novamente mais tarde.')}", color=ft.Colors.ERROR),
                            alignment=ft.alignment.center,
                            margin=ft.margin.only(top=50)
                        )
                    )
                else:
                    _all_produtos_data = result['data']["produtos"]
                    _produtos_inactivated_count = result['data']["deleted"]

            # Atualiza o ícone e tooltip do FAB
            current_trash_icon_filename = "recycle_full_1771.png" if _produtos_inactivated_count else "recycle_empy_1771.png"
            # Garante que fab_trash.content é uma Image
            if fab_trash.content and isinstance(fab_trash.content, ft.Image):
                fab_trash.content.src = f"icons/{current_trash_icon_filename}"
                fab_trash.tooltip = f"Produtos inativos: {_produtos_inactivated_count}"

            # Filtra os dados carregados (ou vazios) e renderiza o grid
            filtered_produtos = _get_filtered_produtos()
            _render_grid(filtered_produtos)

        except Exception as e:
            # Mostrar uma mensagem de erro para o usuário
            tb_str = traceback.format_exc()
            logger.error(
                f"Ocorreu um erro ao carregar as produtos de produtos. Tipo: {type(e).__name__}, Erro: {e}\nTraceback:\n{tb_str}")

            content_area.controls.clear()
            _all_produtos_data = []  # Limpa dados em caso de erro geral
            _produtos_inactivated_count = 0
            content_area.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.ERROR_OUTLINE,
                                color=ft.Colors.RED, size=50),
                        ft.Text(
                            f"Ocorreu um erro ao carregar as produtos de produtos.", color=ft.Colors.RED),
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
                logger.info(
                    "Contexto da página perdido, não foi possível atualizar.")
                print("Contexto da página perdido, não foi possível atualizar.")

    # --- Disparar Carregamento dos Dados ---
    # Executa a função async em background. A UI mostrará o spinner primeiro.
    page.run_task(load_data_and_update_ui)

    fab_add = ft.FloatingActionButton(
        tooltip="Adicionar produto",
        icon=ft.Icons.ADD,
        data={'action': 'INSERT', 'data': None},
        on_click=handle_action_click
    )

    fab_trash = ft.FloatingActionButton(
        content=ft.Image(
            src=f"icons/recycle_empy_1771.png",
            fit=ft.ImageFit.CONTAIN,
            error_content=ft.Text("Erro"),
        ),
        on_click=lambda _: page.go("/home/produtos/grid/lixeira"),
        tooltip="Produtos inativos: 0",
        bgcolor=ft.Colors.TRANSPARENT,
    )

    # Resetar alinhamentos da página que podem interferir com o layout da View
    # page.vertical_alignment = ft.MainAxisAlignment.START
    # page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH

    # --- Retornar Estrutura Inicial da Página como ft.View ---
    # A View inclui a AppBar e a área de conteúdo principal (que inicialmente mostra o spinner)

    return ft.View(
        route="/home/produtos/grid",  # A rota que esta view corresponde
        controls=[
            loading_container,  # Mostra o spinner inicialmente
            content_area       # Oculto inicialmente, populado por load_data_and_update_ui
        ],
        appbar=appbar,
        floating_action_button=ft.Column(  # type: ignore [attr-defined]
            controls=[fab_add, fab_trash],
            alignment=ft.MainAxisAlignment.END,
        ),
        vertical_alignment=ft.MainAxisAlignment.START,  # Alinha conteúdo ao topo
        # Deixa o conteúdo esticar horizontalmente
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        # Adiciona um padding ao redor da área de conteúdo
        padding=ft.padding.all(10)
    )
