import datetime
import logging
import math  # Adicionado para a função ceil (arredondar para cima)

import flet as ft

import src.domains.empresas.controllers.empresas_controllers as company_controllers
import src.pages.empresas.empresas_actions_page as empresas_actions_page
from src.pages.shared.components import create_recycle_bin_card
import src.pages.shared.recycle_bin_helpers as recycle_helpers
from src.shared.utils import format_datetime_to_utc_minus_3

logger = logging.getLogger(__name__)


# Rota: /home/empresas/grid/lixeira
def show_companies_grid_trash(page: ft.Page):
    """Página de exibição das empresas do usuário logado que estão inativas ('DELETED') e arquivadas ('ARCHIVED') em formato Cards"""
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

    def handle_action_click(e):
        """Função para lidar com cliques nas ações do menu ou botões."""
        action = e.control.data.get('action')
        empresa = e.control.data.get('data')

        match action:
            case "RESTORE":
                is_restore = empresas_actions_page.restore_from_trash(page=page, empresa=empresa)
                if is_restore:
                    # Reexecuta o carregamento. Atualizar a lista de empresas na tela
                    page.run_task(load_data_and_update_ui)
                    # Não precisa de page.update() aqui, pois run_task já fará isso
            case "outro case":
                pass
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
                on_click=lambda _: page.go("/home/empresas/grid"), tooltip="Voltar",
                clip_behavior=ft.ClipBehavior.ANTI_ALIAS
            ),
        ),
        title=ft.Text(f"Empresas excluídas ou arquivadas", size=18),
        bgcolor=ft.Colors.with_opacity(0.9, ft.Colors.PRIMARY_CONTAINER),
        adaptive=True,
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
        empresa = e.control.data.get('data')
        page_ctx = e.control.page  # Obter a página do contexto do controle

        info_title = "Informação da Empresa"
        info_message = ""

        if empresa.status.name == 'DELETED':
            info_message = recycle_helpers.get_deleted_info_message(empresa)
        elif empresa.status.name == 'ARCHIVED':
            info_message = "Esta empresa está arquivada!\nEmpresas arquivadas não são removidas automaticamente\ne podem estar vinculadas a outros registros como pedidos ou produtos."
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
            on_dismiss=lambda _: logger.info(
                f"Dialog de informação para {empresa.id} dispensado.")
        )

        page_ctx.overlay.append(info_dialog)
        info_dialog.open = True
        page_ctx.update()

    # --- Função Assíncrona para Carregar Dados e Atualizar a UI ---
    async def load_data_and_update_ui():

        # set_empresas: Conjunto de ID's de empresas que o usuário gerencia
        set_empresas = page.app_state.usuario.get( # type: ignore
            'empresas', []) # Usar get com default

        empresas_data = []
        empresas_inactivated = 0

        try:
            # *** IMPORTANTE: Garanta que handle_get_empresas seja async ***
            # Se handle_get_empresas for síncrona e demorar, a UI *vai* congelar.
            # Pode ser necessário refatorar handle_get_empresas para usar um driver de banco de dados async
            # ou executá-la em uma thread separada usando asyncio.to_thread (Python 3.9+)
            # Exemplo usando asyncio.to_thread se handle_get_empresas for sync:
            # empresas_data = asyncio.to_thread(handle_get_empresas, ids_empresas=set_empresas)

            if set_empresas:  # Só busca se houver IDs
                # Busca as empresas do usuário e por default somente as empresas inativas (deletedas ou arquivadas)
                result = company_controllers.handle_get_empresas(ids_empresas=set_empresas, empresas_inativas=True)
                if result["status"] == "success":
                    empresas_data = result['data']['empresas']
                    empresas_inactivated = result['data']['inactivated']

            # --- Construir Conteúdo Baseado nos Dados ---
            content_area.controls.clear()  # Limpar conteúdo anterior
            if not empresas_data:  # Checa se a lista é vazia ou None
                content_area.controls.append(empty_content_display)
            else:
                # Usar ResponsiveRow para um layout de grid responsivo
                # Ajuste colunas para diferentes tamanhos de tela
                # --- Construir o Grid de Cards ---

                grid = ft.ResponsiveRow(
                    controls=[create_recycle_bin_card(
                        entity=empresa,
                        # Empresa não tem imagem, então o conteúdo superior é o próprio nome
                        top_content=ft.Text(f"{empresa.corporate_name}", color=ft.Colors.WHITE70, weight=ft.FontWeight.BOLD),
                        title_text=f"{empresa.store_name if empresa.store_name else 'Loja N/A'}",
                        subtitle_controls=[
                            ft.Text(f"CNPJ: {empresa.cnpj if empresa.cnpj else 'N/A'}", color=ft.Colors.WHITE54, theme_style=ft.TextThemeStyle.BODY_MEDIUM),
                            ft.Text(f"{str(empresa.phone) if empresa.phone else ''}", color=ft.Colors.WHITE54, theme_style=ft.TextThemeStyle.BODY_MEDIUM),
                        ],
                        status_icon=ft.Icon(
                            name=ft.Icons.INVENTORY_2_OUTLINED if empresa.status.name == 'ARCHIVED' else ft.Icons.DELETE_FOREVER_OUTLINED,
                            color=ft.Colors.BLUE if empresa.status.name == 'ARCHIVED' else ft.Colors.RED
                        ),
                        date_text_control=ft.Text(
                            value=(
                                f"Arquivado em: {format_datetime_to_utc_minus_3(empresa.archived_at)}" if empresa.status.name == 'ARCHIVED'
                                else f"Excluído em: {format_datetime_to_utc_minus_3(empresa.deleted_at)}"
                            ),
                            color=ft.Colors.WHITE54 if empresa.status.name == 'ARCHIVED' else ft.Colors.RED,
                            theme_style=ft.TextThemeStyle.BODY_SMALL,
                        ),
                        tooltip_text=(
                            'Empresa arquivada não será removida do banco de dados!' if empresa.status.name == 'ARCHIVED'
                            else 'Exclusão automática e permanente após 90 dias na lixeira'
                        ),
                        on_action_click=handle_action_click,
                        on_info_click=handle_info_click,
                        on_icon_hover=handle_icon_hover,
                    ) for empresa in empresas_data],
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
                        ft.Icon(ft.Icons.ERROR_OUTLINE,
                                color=ft.Colors.RED, size=50),
                        ft.Text(
                            f"Ocorreu um erro ao carregar as empresas inativas.", color=ft.Colors.RED),
                        # Cuidado ao expor detalhes de erro
                        ft.Text(f"Detalhes: {e}",
                                color=ft.Colors.RED, size=10),
                    ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    alignment=ft.alignment.center,
                    margin=ft.margin.only(top=50),
                    expand=True
                )
            )
        finally:
            current_trash_icon_filename = "recycle_full_1771.png" if empresas_inactivated else "recycle_empy_1771.png"
            # Garante que ft_image é uma Image
            if ft_image and isinstance(ft_image, ft.Image):
                ft_image.src = f"icons/{current_trash_icon_filename}"

            # --- Atualizar Visibilidade da UI ---
            loading_container.visible = False
            content_area.visible = True
            # Importante: Atualizar a página para refletir as mudanças
            # Checar se o contexto da página ainda é válido antes de atualizar
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
        route="/home/empresas/grid/lixeira",  # A rota que esta view corresponde
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
