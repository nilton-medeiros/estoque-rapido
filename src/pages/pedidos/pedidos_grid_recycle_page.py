import logging
import traceback

import flet as ft

import src.domains.pedidos.controllers.pedidos_controllers as order_controllers
from src.domains.shared import RegistrationStatus
import src.pages.pedidos.pedidos_actions_page as order_actions
import src.pages.shared.recycle_bin_helpers as recycle_helpers
from src.pages.shared.components import create_recycle_bin_card

from src.shared.utils import format_datetime_to_utc_minus_3

logger = logging.getLogger(__name__)


# Rota: /home/pedidos/grid/lixeira
def show_orders_grid_trash(page: ft.Page):
    """Página de exibição em formato Cards dos pedidos da empresa logada que estão 'DELETED'"""
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
        pedido = e.control.data.get('data')

        match action:
            case "RESTORE":
                is_restore = order_actions.restore_from_trash(page=page, pedido=pedido)
                if is_restore:
                    # Reexecuta o carregamento. Atualizar a lista de pedidos na tela
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
                on_click=lambda _: page.go("/home/pedidos/grid"), tooltip="Voltar",
                clip_behavior=ft.ClipBehavior.ANTI_ALIAS
            ),
        ),
        title=ft.Text(f"Pedidos excluídos", size=18),
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
        pedido = e.control.data.get('data')
        page_ctx = e.control.page # Obter a página do contexto do controle

        info_title = "Informação do Pedido"
        info_message = ""

        if pedido.status == RegistrationStatus.DELETED:
            info_message = recycle_helpers.get_deleted_info_message(pedido)
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
            on_dismiss=lambda _: logger.info(f"Dialog de informação para {pedido.id} dispensado.")
        )

        page_ctx.overlay.append(info_dialog)
        info_dialog.open = True
        page_ctx.update()

    # --- Função Assíncrona para Carregar Dados e Atualizar a UI --- #
    async def load_data_and_update_ui():
        pedidos_data = []
        pedidos_deleted_count = 0

        # ID da empresa logada
        empresa_id = page.app_state.empresa["id"] # type: ignore

        try:
            if not empresa_id:  # Só busca as pedidos da empresa logada, se houver ID
                content_area.controls.append(empty_content_display)
                return

            result = order_controllers.handle_get_pedidos_by_empresa_id(empresa_id=empresa_id, status=RegistrationStatus.DELETED)

            if result["status"] == "error":
                content_area.controls.append(empty_content_display)
                return

            pedidos_data = result['data']["pedidos"]
            pedidos_deleted_count: int = result['data']["quantidade_deletados"]

            # --- Construir Conteúdo Baseado nos Dados ---
            content_area.controls.clear()  # Limpar conteúdo anterior

            if not pedidos_data:
                content_area.controls.append(empty_content_display)

            grid = ft.ResponsiveRow(
                controls=[
                    create_recycle_bin_card(
                        entity=pedido,
                        top_content=ft.Text(f"ID: {pedido.id}", color=ft.Colors.WHITE70, weight=ft.FontWeight.BOLD),
                        title_text=f"Pedido: #{pedido.order_number}",
                        subtitle_controls=[
                            ft.Text(f"Cliente: {pedido.client_name if pedido.client_name else 'Consumidor Final'}", theme_style=ft.TextThemeStyle.BODY_MEDIUM, size=12),
                            ft.Text(f"Fone: {pedido.client_phone if pedido.client_phone else 'Não informado'}", theme_style=ft.TextThemeStyle.BODY_MEDIUM, size=12),
                        ],
                        status_icon=ft.Icon(name=ft.Icons.DELETE_SWEEP_OUTLINED, color=ft.Colors.RED),
                        date_text_control=ft.Text(
                            value=f"Excluído em: {format_datetime_to_utc_minus_3(pedido.deleted_at)}",
                            color=ft.Colors.RED,
                            theme_style=ft.TextThemeStyle.BODY_SMALL,
                        ),
                        tooltip_text='Exclusão automática e permanente após 90 dias na lixeira',
                        on_action_click=handle_action_click,
                        on_info_click=handle_info_click,
                        on_icon_hover=handle_icon_hover,
                        col_config={"xs": 12, "sm": 6, "md": 4, "lg": 4, "xl": 3}
                    ) for pedido in pedidos_data
                ],
                columns=12,  # Total de colunas no sistema de grid
                spacing=10,  # Espaço horizontal entre os cards
                run_spacing=10  # Espaço vertical entre as linhas
            )
            content_area.controls.append(grid)
            # Ou apenas adicione os cards diretamente à Coluna se preferir uma lista vertical
            # content_area.controls.extend(cards)

        except Exception as e:
            # Mostrar uma mensagem de erro para o pedido
            tb_str = traceback.format_exc()
            logger.error(f"Ocorreu um erro ao carregar os pedidos deletados. Tipo: {type(e).__name__}, Erro: {e}\nTraceback:\n{tb_str}")

            content_area.controls.clear()
            content_area.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.ERROR_OUTLINE,
                                color=ft.Colors.RED, size=50),
                        ft.Text(
                            f"Ocorreu um erro ao carregar os pedidos deletados.", color=ft.Colors.RED),
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
            current_trash_icon_filename = "recycle_full_1771.png" if pedidos_deleted_count else "recycle_empy_1771.png"
            # Garante que ft_image é uma Image
            if ft_image and isinstance(ft_image, ft.Image):
                ft_image.src = f"icons/{current_trash_icon_filename}"

            loading_container.visible = False
            content_area.visible = True
            if page.client_storage:  # Uma checagem se a página ainda está ativa
                page.update()
            else:
                logger.info("Contexto da página perdido, não foi possível atualizar.")

    # --- Disparar Carregamento dos Dados ---
    # Executa a função async em background. A UI mostrará o spinner primeiro.
    page.run_task(load_data_and_update_ui)

    # --- Retornar Estrutura Inicial da Página como ft.View ---
    # A View inclui a AppBar e a área de conteúdo principal (que inicialmente mostra o spinner)
    return ft.View(
        route="/home/pedidos/grid/lixeira",  # A rota que esta view corresponde
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
