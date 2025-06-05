import logging
import traceback

import flet as ft

from src.domains.produtos.models import ProdutoStatus
from src.domains.produtos.models.produtos_model import Produto
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

    def handle_icon__voltar_hover(e):
        """Muda o bgcolor do container no hover."""
        e.control.bgcolor = ft.Colors.with_opacity(
            0.1, ft.Colors.WHITE) if e.data == "true" else ft.Colors.TRANSPARENT
        e.control.update()

    def handle_icon_on_click(e) -> None:
        # 'e.page' refere-se à página do contexto do evento, o que é mais robusto.
        page_do_evento = e.page
        print(f"handle_icon_on_click: Evento recebido. Tentando abrir o drawer (UID: {drawer_filters.uid if drawer_filters else 'drawer_filters é None'}).")
        if drawer_filters:
            drawer_filters.open = True
            # Atualizar o próprio drawer é a forma recomendada.
            drawer_filters.update()
            print(f"handle_icon_on_click: drawer_filters.open definido como {drawer_filters.open}. drawer_filters.update() chamado.")
        else:
            print("handle_icon_on_click: ERRO crítico - drawer_filters não está definido.")

    icon_menu = ft.IconButton(icon=ft.Icons.MENU, visible=False, on_click=handle_icon_on_click)

    def filtrar_produtos(radiogroup_filter, textfield_filter, dropdwn_filter):
        filtered_produtos = _get_filtered_produtos(
            radiogroup_filter=radiogroup_filter,
            textfield_filter=textfield_filter,
            dropdwn_filter=dropdwn_filter
        )
        _render_grid(filtered_produtos)
        if page.client_storage:
            page.update()

    def radiogroup_changed(e):
        filtro = e.control
        if filtro == filter_radio_appbar:
            filtrar_produtos(filter_radio_appbar, filter_textfield_appbar, filter_dropdown_appbar)
        else:
            filtrar_produtos(filter_radio_drawer, filter_textfield_drawer, filter_dropdown_drawer)

    filter_radio_appbar = ft.RadioGroup(
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

    def textfield_filter_clicked(e):
        nonlocal page  # Acessa page para update
        icon_control = e.control

        text_field = filter_textfield_appbar if e.data == "appbar" else filter_textfield_drawer

        if text_field.value:
            # Se foi digitado algo no campo e a busca já foi feita, limpa o filtro
            if icon_control.icon == ft.Icons.FILTER_ALT_OFF or icon_control.icon == ft.Icons.FILTER_ALT_OFF_OUTLINED:
                text_field.value = ""

        if e.data == "appbar":
            filtrar_produtos(filter_radio_appbar, filter_textfield_appbar, filter_dropdown_appbar)
        else:
            filtrar_produtos(filter_radio_drawer, filter_textfield_drawer, filter_dropdown_drawer)

    filter_textfield_appbar = ft.TextField(
        label="Busca pelo nome do produto",
        width=300,
        height=40,
        text_size=13,
        label_style=ft.TextStyle(size=10),
        hint_style=ft.TextStyle(size=10),
        suffix=ft.IconButton(
            icon=ft.Icons.FILTER_ALT_OUTLINED,
            icon_color=ft.Colors.PRIMARY,
            on_click=textfield_filter_clicked,
            data="appbar",
        ),
        bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.BLACK),
    )

    def dropdown_filter_changed(e):
        filtro = e.control
        if filtro == filter_dropdown_appbar:
            filtrar_produtos(filter_radio_appbar, filter_textfield_appbar, filter_dropdown_appbar)
        else:
            filtrar_produtos(filter_radio_drawer, filter_textfield_drawer, filter_dropdown_drawer)

    filter_dropdown_appbar = ft.Dropdown(
        label="Estoque",
        text_size=13,
        options=[
            ft.DropdownOption(key="all", text= "Todos", content=ft.Text("Todos", size=13, color=ft.Colors.WHITE)),
            ft.DropdownOption(key="normal", text= "Normal", content=ft.Text("Normal", size=13, color=ft.Colors.GREEN)),
            ft.DropdownOption(key="excellent", text= "Excelente", content=ft.Text("Excelente", size=13, color=ft.Colors.BLUE)),
            ft.DropdownOption(key="replace", text="Repor", content=ft.Text("Repor", size=13, color=ft.Colors.RED)),
        ],
        on_change=dropdown_filter_changed,
    )

    filter_radio_drawer = ft.RadioGroup(
        value="all",  # Valor inicial do filtro
        content=ft.Column(
            controls=[
                ft.Radio(value="all", label="Todos"),
                ft.Radio(value="active", label="Ativos"),
                ft.Radio(value="inactive", label="Descontinuados"),
            ]
        ),
        on_change=radiogroup_changed,  # Conecta a função handler
    )

    filter_textfield_drawer = ft.TextField(
        label="Busca pelo nome do produto",
        width=300,
        height=40,
        text_size=13,
        label_style=ft.TextStyle(size=10),
        hint_style=ft.TextStyle(size=10),
        suffix=ft.IconButton(
            icon=ft.Icons.FILTER_ALT_OUTLINED,
            icon_color=ft.Colors.PRIMARY,
            on_click=textfield_filter_clicked,
            data="drawer",
        ),
        bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.BLACK),
    )

    filter_dropdown_drawer = ft.Dropdown(
        label="Estoque",
        text_size=13,
        options=[
            ft.DropdownOption(key="all", content=ft.Text("Todos", size=13, color=ft.Colors.WHITE)),
            ft.DropdownOption(key="normal", content=ft.Text("Normal", size=13, color=ft.Colors.GREEN)),
            ft.DropdownOption(key="excellent", content=ft.Text("Excelente", size=13, color=ft.Colors.BLUE)),
            ft.DropdownOption(key="replace", content=ft.Text("Repor", size=13, color=ft.Colors.RED)),
        ],
        on_change=dropdown_filter_changed,
    )

    def build_app_bar(width):
        controls = []

        # Atualiza visibilidade do menu ícone conforme a largura
        icon_menu.visible = width <= 1024
        filter_radio_appbar.visible = width > 1024
        filter_textfield_appbar.visible = width > 1024
        filter_dropdown_appbar.visible = width > 1024

        if width > 1024:
            controls.extend([
                ft.Container(
                    bgcolor=ft.Colors.TRANSPARENT,
                    alignment=ft.alignment.center,
                    content=filter_radio_appbar,
                    margin=ft.margin.only(left=10, right=10),
                    clip_behavior=ft.ClipBehavior.ANTI_ALIAS
                ),
                ft.Container(
                    bgcolor=ft.Colors.TRANSPARENT,
                    alignment=ft.alignment.center,
                    content=filter_textfield_appbar,
                    margin=ft.margin.only(left=10, right=10),
                    clip_behavior=ft.ClipBehavior.ANTI_ALIAS
                ),
                ft.Container(
                    bgcolor=ft.Colors.TRANSPARENT,
                    alignment=ft.alignment.center,
                    content=filter_dropdown_appbar,
                    margin=ft.margin.only(left=10, right=10),
                    clip_behavior=ft.ClipBehavior.ANTI_ALIAS
                )
            ])

        return ft.AppBar(
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
                # on_hover=handle_icon_hover,
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

    appbar = build_app_bar(page.width if page.width else 0)

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

    def stock_filter(prod: Produto, stk_dropdown_filter: ft.Dropdown) -> bool:
        if not stk_dropdown_filter.value or stk_dropdown_filter.value == "all":    # Todos os estoques
            return True
        elif stk_dropdown_filter.value == "normal":   # Estoque entre o mínimo e o máximo
            return prod.minimum_stock_level <= prod.quantity_on_hand < prod.maximum_stock_level
        elif stk_dropdown_filter.value == "excellent":    # Estoque acima do esperado ou igual ao máximo
            return prod.maximum_stock_level <= prod.quantity_on_hand
        else:   # Estoque abaixo do esperado ou igual ao mínimo
            return prod.quantity_on_hand < prod.minimum_stock_level

    def _get_filtered_produtos(radiogroup_filter: ft.RadioGroup, textfield_filter: ft.TextField, dropdwn_filter: ft.Dropdown) -> list:
        """Filtra _all_produtos_data com base no valor de radiogroup_filter."""
        nonlocal _all_produtos_data  # Acessa a variável do escopo de show_products_grid

        current_filter = radiogroup_filter.value
        # Valor original do campo de busca
        original_search_value = textfield_filter.value if textfield_filter.value else ""
        # Texto de busca processado para o filtro
        search_text_for_filtering = original_search_value.strip()
        product_filter = []

        if current_filter == "all":
            if search_text_for_filtering:
                product_filter = [pro for pro in _all_produtos_data if search_text_for_filtering.lower() in pro.name.lower() and stock_filter(pro, dropdwn_filter)]
            else:
                product_filter = [pro for pro in _all_produtos_data if stock_filter(pro, dropdwn_filter)]
        elif current_filter == "active":
            # Assumindo que produto.status.name pode ser 'ACTIVE', 'INACTIVE', etc.
            if search_text_for_filtering:
                product_filter = [pro for pro in _all_produtos_data if pro.status.name == 'ACTIVE' and search_text_for_filtering.lower() in pro.name.lower() and stock_filter(pro, dropdwn_filter)]
            else:
                product_filter = [pro for pro in _all_produtos_data if pro.status.name == 'ACTIVE' and stock_filter(pro, dropdwn_filter)]
        elif current_filter == "inactive":  # "Descontinuado"
            if search_text_for_filtering:
                product_filter = [pro for pro in _all_produtos_data if pro.status.name == 'INACTIVE' and search_text_for_filtering.lower() in pro.name.lower() and stock_filter(pro, dropdwn_filter)]
            else:
                product_filter = [pro for pro in _all_produtos_data if pro.status.name == 'INACTIVE' and stock_filter(pro, dropdwn_filter)]

        # Atualiza os elementos da UI (cor do TextField e ícone do Suffix)
        suffix_control = textfield_filter.suffix
        if isinstance(suffix_control, ft.IconButton): # Verifica se o sufixo é um IconButton
            if original_search_value.strip():  # Verifica se havia algum texto de busca (após remover espaços)
                if product_filter:  # E se foram encontrados resultados
                    textfield_filter.color = ft.Colors.GREEN
                    suffix_control.icon = ft.Icons.FILTER_ALT_OFF
                    suffix_control.icon_color = ft.Colors.GREEN
                else:  # Texto de busca presente, mas sem resultados
                    textfield_filter.color = ft.Colors.RED
                    suffix_control.icon = ft.Icons.FILTER_ALT_OFF_OUTLINED
                    suffix_control.icon_color = ft.Colors.RED
            else:  # Nenhum texto de busca (ou apenas espaços em branco)
                textfield_filter.color = ft.Colors.WHITE # Cor padrão/neutra
                suffix_control.icon = ft.Icons.FILTER_ALT_OUTLINED
                suffix_control.icon_color = ft.Colors.PRIMARY

            suffix_control.update() # Atualiza o IconButton para refletir a mudança de ícone

        # Mantém o valor original (com espaços, se houver) no TextField para a UI, mas filtra com o valor sem espaços
        textfield_filter.value = original_search_value
        textfield_filter.update() # Atualiza o TextField para refletir a mudança de cor e valor

        return product_filter

    def get_color_quantify_status(prod):
        try:
            quantity_on_hand = int(prod.quantity_on_hand)
            minimum_stock_level = int(prod.minimum_stock_level)
            maximum_stock_level = int(prod.maximum_stock_level)
        except ValueError:
            logger.error(
                f"Valores de estoque inválidos (não numéricos) para produto ID {getattr(prod, 'id', 'N/A')}: "
                f"QOH='{prod.quantity_on_hand}', Min='{prod.minimum_stock_level}', Max='{prod.maximum_stock_level}'"
            )
            # Retorna uma cor neutra ou de erro se os valores não puderem ser convertidos
            return ft.Colors.GREY

        # Abaixo do estoque mínimo
        if quantity_on_hand < minimum_stock_level:
            return ft.Colors.RED
        # Igual ao estoque mínimo
        elif quantity_on_hand == minimum_stock_level:
            return ft.Colors.ORANGE
        # Acima ou igual ao estoque máximo
        # Se maximum_stock_level for 0, esta condição (ex: 1 >= 0) será verdadeira, resultando em BLUE.
        elif quantity_on_hand >= maximum_stock_level:
            return ft.Colors.BLUE
        # Entre mínimo (exclusivo) e máximo (exclusivo)
        else:  # Cobre minimum_stock_level < quantity_on_hand < maximum_stock_level
            return ft.Colors.GREEN

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
                                ft.Text(
                                    f"{produto.description.replace(chr(10), ' ')}",  # chr(10) is newline
                                    theme_style=ft.TextThemeStyle.BODY_SMALL, no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS),
                                ft.Text(f"{produto.sale_price}",
                                        theme_style=ft.TextThemeStyle.BODY_SMALL),
                                ft.Row(
                                    controls=[
                                        ft.Text(
                                            # Ex: "Ativo", "Descontinuado"
                                            value=f"{produto.status.value}",
                                            theme_style=ft.TextThemeStyle.BODY_SMALL,
                                            color=ft.Colors.GREEN if produto.status == ProdutoStatus.ACTIVE else ft.Colors.RED,
                                        ),
                                        ft.Text(
                                            value=f"Estoque mínimo: {produto.minimum_stock_level}, máximo: {produto.maximum_stock_level}, atual: {produto.quantity_on_hand}",
                                            theme_style=ft.TextThemeStyle.BODY_SMALL,
                                            color=get_color_quantify_status(produto),
                                        )
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

    drawer_filters = ft.NavigationDrawer(
        controls=[
            filter_radio_drawer,
            filter_textfield_drawer,
            filter_dropdown_drawer,
        ],
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
            width = page.width if page.width else 0
            if width < 1024:
                filtered_produtos = _get_filtered_produtos(
                    radiogroup_filter=filter_radio_appbar,
                    textfield_filter=filter_textfield_appbar,
                    dropdwn_filter=filter_dropdown_appbar
                )
            else:
                filtered_produtos = _get_filtered_produtos(
                    radiogroup_filter=filter_radio_drawer,
                    textfield_filter=filter_textfield_drawer,
                    dropdwn_filter=filter_dropdown_drawer
                )

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
                logger.info("Contexto da página perdido, não foi possível atualizar.")

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

    def handle_page_resize(e):
        width = e.page.width if e.page.width else 0
        e.page.appbar = build_app_bar(width)
        e.page.update()

    page.on_resized = handle_page_resize

    return ft.View(
        route="/home/produtos/grid",  # A rota que esta view corresponde
        controls=[
            loading_container,  # Mostra o spinner inicialmente
            content_area       # Oculto inicialmente, populado por load_data_and_update_ui
        ],
        appbar=appbar,
        drawer=drawer_filters,
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
