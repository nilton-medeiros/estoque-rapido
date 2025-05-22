import logging
import traceback
import datetime
import math # Adicionado para a função ceil (arredondar para cima)

import flet as ft

import src.domains.produtos.controllers.categorias_controllers as cat_controllers
import src.pages.produtos.categorias_actions as cat_actions

from src.shared import format_datetime_to_utc_minus_3

logger = logging.getLogger(__name__)


# Rota: /home/produtos/categorias/grid/lixeira
def cat_grid_lixeira(page: ft.Page):
    """Página de exibição das categorias da empresa logada que estão inativas ('DELETED')em formato Cards"""
    page.theme_mode = ft.ThemeMode.DARK

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
            src=f"icons/recycle_empy_1772.png",
            error_content=ft.Text("Vazio"),
            width=300,
            height=300,
            fit=ft.ImageFit.COVER,
            border_radius=ft.border_radius.all(10),
        ),
        margin=ft.margin.only(top=100),
        alignment=ft.alignment.center,
    )

    async def handle_action_click(e):
        """Função para lidar com cliques nas ações do menu ou botões."""
        action = e.control.data.get('action')
        categoria = e.control.data.get('data')

        match action:
            case "RESTORE":
                is_restore = await cat_actions.restore_from_trash(page=page, categoria=categoria)
                if is_restore:
                    # Reexecuta o carregamento. Atualizar a lista de categorias na tela
                    page.run_task(load_data_and_update_ui)
                    # Não precisa de page.update() aqui, pois run_task já fará isso
            case "outro case":
                pass
            case _:
                pass

    def handle_icon_hover(e):
        """Muda o bgcolor do container no hover."""
        e.control.bgcolor = ft.Colors.with_opacity(0.1, ft.Colors.WHITE) if e.data == "true" else ft.Colors.TRANSPARENT
        e.control.update()

    ft_image = ft.Image(
        src=f"icons/recycle_empy_1771.png",
        fit=ft.ImageFit.CONTAIN,
        error_content=ft.Text("Erro"),
    )

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
                on_click=lambda _: page.go("/home/produtos/categorias/grid"), tooltip="Voltar",
                clip_behavior=ft.ClipBehavior.ANTI_ALIAS
            ),
        ),
        title=ft.Text(f"Categorias excluídas", size=18),
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
                content=ft_image,
                margin=ft.margin.only(right=10),
                clip_behavior=ft.ClipBehavior.ANTI_ALIAS # Boa prática adicionar aqui também
            ),
        ],
    )

    def handle_info_click(e):
        categoria = e.control.data.get('data')
        page_ctx = e.control.page # Obter a página do contexto do controle

        info_title = "Informação da Categoria"
        info_message = ""

        if categoria.status.name == 'DELETED':
            if categoria.deleted_at:  # Verifica se a data de exclusão está definida
                # Data em que o item foi movido para a lixeira (presumivelmente UTC)
                data_movido_lixeira = categoria.deleted_at

                # Data final para exclusão permanente (90 dias após mover para lixeira)
                data_exclusao_permanente = data_movido_lixeira + datetime.timedelta(days=90)

                # Data e hora atuais em UTC para comparação consistente
                agora_utc = datetime.datetime.now(datetime.UTC)

                # Calcula o tempo restante até a exclusão permanente
                tempo_restante = data_exclusao_permanente - agora_utc

                days_left = 0  # Valor padrão caso o tempo já tenha expirado
                if tempo_restante.total_seconds() > 0:
                    # Converte o tempo restante para dias (float)
                    dias_restantes_float = tempo_restante.total_seconds() / (24 * 60 * 60)
                    # Arredonda para cima para o próximo dia inteiro
                    days_left = math.ceil(dias_restantes_float)

                if days_left == 0:
                    info_message = "Esta categoria está na lixeira. A exclusão permanente está prevista para hoje ou já pode ter ocorrido."
                elif days_left == 1:
                    info_message = f"Esta categoria está na lixeira. A exclusão automática e permanente do banco de dados ocorrerá em {days_left} dia."
                else:
                    info_message = f"Esta categoria está na lixeira. A exclusão automática e permanente do banco de dados ocorrerá em {days_left} dias."
            else:
                # Caso deleted_at não esteja definido
                info_message = "Esta categoria está na lixeira, mas a data de início da contagem para exclusão não foi registrada."
        else:
            info_message = "Status desconhecido."

        def close_dialog(e_dialog):
            info_dialog.open = False
            page_ctx.update()

        info_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(info_title),
            content=ft.Text(info_message),
            actions=[
                ft.TextButton("Entendi", on_click=close_dialog)
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            on_dismiss=lambda _: logger.info(f"Dialog de informação para {categoria.id} dispensado.")
        )

        page_ctx.overlay.append(info_dialog)
        info_dialog.open = True
        page_ctx.update()

    # --- Função Assíncrona para Carregar Dados e Atualizar a UI ---
    async def load_data_and_update_ui():
        categorias_data = []
        categorias_inactivated = 0

        # ID da empresa logada
        empresa_id = page.app_state.empresa["id"] # type: ignore

        try:
            # *** IMPORTANTE: Garanta que handle_get_all seja async ***
            if not empresa_id:  # Só busca as categorias da empresa logada, se houver ID
                content_area.controls.append(empty_content_display)
                return

            result = await cat_controllers.handle_get_all(empresa_id=empresa_id, status_deleted=True)

            if result["status"] == "error":
                content_area.controls.append(empty_content_display)
                return

            categorias_data = result['data']["categorias"]
            categorias_inactivated: int = result['data']["deleted"]

            # --- Construir Conteúdo Baseado nos Dados ---
            content_area.controls.clear()  # Limpar conteúdo anterior

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
                                        ft.Container(
                                            image=ft.DecorationImage(src=categoria.image_url),
                                            width=100,
                                            height=100,
                                            border_radius=ft.border_radius.all(10),
                                            border=ft.border.all(width=1) if not categoria.image_url else None,
                                        ),
                                        # Container do PopMenuButton para não deixar colado com a margem direita de Column
                                        ft.Container(expand=True),
                                        ft.Icon(
                                            name=ft.Icons.DELETE_FOREVER_OUTLINED,
                                            color=ft.Colors.RED
                                        ),
                                        # Container do PopMenuButton para não deixar colado com a margem direita de Column
                                        ft.Container(
                                            # padding=ft.padding.only(right=5),
                                            content=ft.PopupMenuButton(
                                                icon=ft.Icons.MORE_VERT, tooltip="Mais Ações",
                                                items=[
                                                    ft.PopupMenuItem(
                                                        text="Restaurar",
                                                        tooltip="Restaurar categoria da lixeira",
                                                        icon=ft.Icons.RESTORE,
                                                        data={
                                                            'action': 'RESTORE', 'data': categoria},
                                                        on_click=handle_action_click
                                                    ),
                                                    ft.PopupMenuItem(
                                                        text="Informações",
                                                        tooltip="Informações sobre o status",
                                                        icon=ft.Icons.INFO_OUTLINED,
                                                        data={
                                                            'action': 'INFO', 'data': categoria},
                                                        on_click=handle_info_click
                                                    ),
                                                ],
                                            ),
                                        ),
                                    ],
                                    alignment=ft.MainAxisAlignment.START,
                                ),
                                ft.Text(
                                    f"{categoria.name}", color=ft.Colors.WHITE70, weight=ft.FontWeight.BOLD),
                                ft.Text(f"{categoria.description if categoria.description else '<Sem descrição>'}",
                                        theme_style=ft.TextThemeStyle.BODY_MEDIUM),
                                ft.Row(
                                    controls=[
                                        ft.Text(
                                            value=f"Excluído em: {format_datetime_to_utc_minus_3(categoria.deleted_at)}",
                                            color=ft.Colors.RED,
                                            theme_style=ft.TextThemeStyle.BODY_SMALL,
                                        ),
                                        ft.Row(
                                            controls=[
                                                ft.Container(
                                                    content=ft.Icon(
                                                        name=ft.Icons.RESTORE_OUTLINED,
                                                        color=ft.Colors.PRIMARY,
                                                    ),
                                                    margin=ft.margin.only(
                                                        right=5),
                                                    tooltip="Restaurar",
                                                    data={
                                                        'action': 'RESTORE', 'data': categoria},
                                                    on_hover=handle_icon_hover,
                                                    on_click=handle_action_click,
                                                    border_radius=ft.border_radius.all(
                                                        20),
                                                    ink=True,
                                                    bgcolor=ft.Colors.TRANSPARENT,
                                                    alignment=ft.alignment.center,
                                                    clip_behavior=ft.ClipBehavior.ANTI_ALIAS
                                                ),
                                                ft.Container(
                                                    content=ft.Icon(
                                                        name=ft.Icons.INFO_OUTLINED,
                                                        color=ft.Colors.PRIMARY,
                                                    ),
                                                    margin=ft.margin.only(
                                                        right=10),
                                                    tooltip="Informações sobre o status",
                                                    data={
                                                        'action': 'INFO', 'data': categoria},
                                                    on_hover=handle_icon_hover,
                                                    on_click=handle_info_click,
                                                    border_radius=ft.border_radius.all(
                                                        20),
                                                    ink=True,
                                                    bgcolor=ft.Colors.TRANSPARENT,
                                                    alignment=ft.alignment.center,
                                                    clip_behavior=ft.ClipBehavior.ANTI_ALIAS
                                                ),
                                            ],
                                        ),
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                ),
                            ])
                        ),
                        margin=ft.margin.all(5),
                        # Configuração responsiva para cada card
                        # Cada card com sua própria configuração de colunas
                        col={"xs": 12, "sm": 6, "md": 4, "lg": 3},
                        tooltip=f"{'Exclusão automática e permanente após 90 dias na lixeira' if categoria.status.name == 'DELETED' else 'categoria arquivada não será removida do banco de dados! Pode estar vinculada a pedidos ou produtos.'}",
                    ) for categoria in categorias_data  # Criar um card para cada empresa
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
            logger.error(f"Ocorreu um erro ao carregar as categorias deletadas. Tipo: {type(e).__name__}, Erro: {e}\nTraceback:\n{tb_str}")

            content_area.controls.clear()
            content_area.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.ERROR_OUTLINE,
                                color=ft.Colors.RED, size=50),
                        ft.Text(
                            f"Ocorreu um erro ao carregar as categorias deletadas.", color=ft.Colors.RED),
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
            current_trash_icon_filename = "recycle_full_1771.png" if categorias_inactivated else "recycle_empy_1771.png"
            # Garante que ft_image é uma Image
            if ft_image and isinstance(ft_image, ft.Image):
                ft_image.src = f"icons/{current_trash_icon_filename}"

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

    # --- Retornar Estrutura Inicial da Página como ft.View ---
    # A View inclui a AppBar e a área de conteúdo principal (que inicialmente mostra o spinner)
    return ft.View(
        route="/home/produtos/categorias/grid/lixeira",  # A rota que esta view corresponde
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
