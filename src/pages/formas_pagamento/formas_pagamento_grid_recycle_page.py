import logging
import traceback

import flet as ft

from src.domains.formas_pagamento.controllers.formas_pagamento_controller import FormasPagamentoController
from src.domains.formas_pagamento.repositories.implementations.firebase_formas_pagamento_repository import FirebaseFormasPagamentoRepository
from src.domains.formas_pagamento.services.formas_pagamento_service import FormasPagamentoService
from src.domains.shared.context.session import get_current_company
from src.pages.formas_pagamento.formas_pagamento_actions_page import restore_from_trash
from src.pages.partials.app_bars.appbar import create_appbar_back
from src.pages.shared.components import create_recycle_bin_card
from src.pages.shared.recycle_bin_helpers import get_deleted_info_message
from src.shared.utils.time_zone import format_datetime_to_utc_minus_3

logger = logging.getLogger(__name__)


def show_formas_pagamento_grid_trash(page: ft.Page):
    """
    Página de exibição das forams de pagamento do pedido da empresa logada que estão excluídas
    ('DELETED'), em formato Cards.
    """
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
        forma_pagamento = e.control.data.get('data')

        match action:
            case "RESTORE":
                is_restore = restore_from_trash(
                    page=page, forma_pagamento=forma_pagamento)
                if is_restore:
                    # Reexecuta o carregamento. Atualizar a lista de formas de pagamento na tela
                    page.run_task(load_data_and_update_ui)
                    # Não precisa de page.update() aqui, pois run_task já fará isso
            case _:
                pass

    def handle_icon_hover(e):
        """Muda o bgcolor do container no hover."""
        e.control.bgcolor = ft.Colors.with_opacity(
            0.1, ft.Colors.WHITE) if e.data == "true" else ft.Colors.TRANSPARENT
        e.control.update()

    ft_image = ft.Image(
        src=f"icons/recycle_empy_1771.png",
        fit=ft.ImageFit.CONTAIN,
        error_content=ft.Text("Erro"),
    )

    appbar = create_appbar_back(
        page=page,
        title=ft.Text(f"Formas de Pagamento excluídos", size=18),
        actions=[
            ft.Container(
                width=43,
                height=43,
                # Metade da largura/altura para ser círculo
                border_radius=ft.border_radius.all(20),
                ink=True,
                bgcolor=ft.Colors.TRANSPARENT,
                alignment=ft.alignment.center,
                content=ft_image,
                margin=ft.margin.only(right=10),
                clip_behavior=ft.ClipBehavior.ANTI_ALIAS  # Boa prática adicionar aqui também
            ),
        ],
    )

    def handle_info_click(e):
        forma_pagamento = e.control.data.get('data')
        page_ctx = e.control.page  # Obter a página do contexto do controle

        info_message = ""

        if forma_pagamento.status.name == 'DELETED':
            info_message = get_deleted_info_message(forma_pagamento)
        else:
            info_message = "Status desconhecido."

        def close_dialog(e_close):
            page_ctx.close(info_dialog)

        info_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Informação da Forma de Pagamento"),
            content=ft.Text(info_message),
            actions=[
                ft.TextButton("Entendi", on_click=close_dialog)
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            on_dismiss=lambda _: logger.info(
                f"Dialog de informação para {forma_pagamento.id} dispensado.")
        )

        page_ctx.open(info_dialog)

    # --- Função Assíncrona para Carregar Dados e Atualizar a UI ---
    async def load_data_and_update_ui():
        # ID da empresa logada
        empresa_id = get_current_company(page)["id"]

        try:
            # *** IMPORTANTE: Garanta que get_formas_pagamento seja async ***
            if not empresa_id:  # Só busca as formas de pagamento da empresa logada, se houver ID
                content_area.controls.append(empty_content_display)
                return
            repository = FirebaseFormasPagamentoRepository()
            service = FormasPagamentoService(repository)
            controllers = FormasPagamentoController(service)

            formas_pagamentos_data, formas_pagamentos_inactivated = controllers.get_formas_pagamento(
                empresa_id=empresa_id, status_deleted=True)

            if formas_pagamentos_inactivated == 0:
                # Se formas_pagamentos_inactivated == 0, formas_pagamentos_data é vazio []
                content_area.controls.append(empty_content_display)
                return

            # --- Construir Conteúdo Baseado nos Dados ---
            content_area.controls.clear()  # Limpar conteúdo anterior

            if not formas_pagamentos_data:
                content_area.controls.append(empty_content_display)

            grid = ft.ResponsiveRow(
                controls=[
                    create_recycle_bin_card(
                        entity=forma_pagamento,
                        top_content=ft.Text(f"ID: {forma_pagamento.id}", color=ft.Colors.WHITE70, weight=ft.FontWeight.BOLD),
                        title_text=forma_pagamento.name,
                        subtitle_controls=[
                            ft.Text(f"Tipo de Pagamento: {forma_pagamento.payment_type.value}",
                                    theme_style=ft.TextThemeStyle.BODY_MEDIUM),
                        ],
                        status_icon=ft.Icon(
                            name=ft.Icons.DELETE_FOREVER_OUTLINED, color=ft.Colors.RED),
                        date_text_control=ft.Text(
                            value=f"Excluído em: {format_datetime_to_utc_minus_3(forma_pagamento.deleted_at)}",
                            color=ft.Colors.RED,
                            theme_style=ft.TextThemeStyle.BODY_SMALL,
                        ),
                        tooltip_text='Exclusão automática e permanente após 90 dias na lixeira',
                        on_action_click=handle_action_click,
                        on_info_click=handle_info_click,
                        on_icon_hover=handle_icon_hover,
                    ) for forma_pagamento in formas_pagamentos_data
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
            logger.error(
                f"Ocorreu um erro ao carregar os produtos deletados. Tipo: {type(e).__name__}, Erro: {e}\nTraceback:\n{tb_str}")

            content_area.controls.clear()
            content_area.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.ERROR_OUTLINE,
                                color=ft.Colors.RED, size=50),
                        ft.Text(
                            f"Ocorreu um erro ao carregar os produtos deletados.", color=ft.Colors.RED),
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
            current_trash_icon_filename = "recycle_full_1771.png" if formas_pagamentos_inactivated else "recycle_empy_1771.png"
            # Garante que ft_image é uma Image
            if ft_image and isinstance(ft_image, ft.Image):
                ft_image.src = f"icons/{current_trash_icon_filename}"

            loading_container.visible = False
            content_area.visible = True
            if page.client_storage:  # Uma checagem se a página ainda está ativa
                page.update()
            else:
                logger.info(
                    "Contexto da página perdido, não foi possível atualizar.")

    # --- Disparar Carregamento dos Dados ---
    # Executa a função async em background. A UI mostrará o spinner primeiro.
    page.run_task(load_data_and_update_ui)

    # --- Retornar Estrutura Inicial da Página como ft.View ---
    # A View inclui a AppBar e a área de conteúdo principal (que inicialmente mostra o spinner)
    return ft.View(
        route="/home/produtos/grid/lixeira",  # A rota que esta view corresponde
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
