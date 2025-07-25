import logging

import flet as ft
# import asyncio  # Importar asyncio se precisar simular delays ou usar recursos async

import src.domains.empresas.controllers.empresas_controllers as company_controllers
from src.domains.shared import RegistrationStatus
import src.pages.empresas.empresas_actions_page as empresas_actions_page
from src.pages.partials.app_bars.appbar import create_appbar_menu
from src.shared.utils import MessageType, message_snackbar, show_banner
# Rota: /home/empresas/grid

logger = logging.getLogger(__name__)


def show_companies_grid(page: ft.Page):
    """Página de exibição das empresas do usuário logado em formato Cards"""
    page.theme_mode = ft.ThemeMode.DARK
    page.data = page.route  # Armazena a rota atual em `page.data` para uso pela função `page.back()` de navegação.

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

    # --- Conteúdo Padrão Vazio (definido uma vez) ---
    empty_content_display = ft.Container(
        content=ft.Image(
            # src=f"images/empty_folder.png",
            src=f"images/steel_cabinets_documents_empty.png",
            error_content=ft.Text("Nenhuma empresa cadastrada"),
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
        empresa = e.control.data.get('data')

        match action:
            case "INSERT":
                # Garante que ao entrar no formulário principal, os campos estejam vazio
                page.app_state.clear_form_data() # type: ignore
                page.go('/home/empresas/form/principal')
            case "SELECT":
                # Seleciona a empresa para trabalhar
                page.app_state.set_empresa(empresa.to_dict()) # type: ignore
                usuario_id = page.app_state.usuario.get('id') # type: ignore
                empresas = page.app_state.usuario.get('empresas') # type: ignore
                result = empresas_actions_page.user_update(usuario_id, empresa.id, empresas)

                if result['status'] == 'error':
                    logger.warning(result['message'])
                    message_snackbar(
                        message=result['message'], message_type=MessageType.WARNING, page=page)
                    return

                page.go('/home')  # Redireciona para página home do usuário
            case "MAIN_DATA":
                page.app_state.set_form_data(empresa.to_dict()) # type: ignore
                page.go('/home/empresas/form/principal')
            case "TAX_DATA":
                if empresa.cnpj:
                    page.app_state.set_form_data(empresa.to_dict()) # type: ignore
                    page.go('/home/empresas/form/dados-fiscais')
                else:
                    show_banner(page=page, message="É preciso definir o CNPJ da empresa em Dados Principais antes de definir os dados fiscais")
            case "DIGITAL_CERTIFICATE":
                logger.info(f"Aguardando implementação: Certificado digital {empresa.id}")
            case "SOFT_DELETE":
                is_deleted = await empresas_actions_page.send_to_trash(page=page, empresa=empresa, status=RegistrationStatus.DELETED)
                if is_deleted:
                    # Reexecuta o carregamento. Atualizar a lista de empresas na tela
                    page.run_task(load_data_and_update_ui)
                    # Não precisa de page.update() aqui, pois run_task já fará isso
            case "ARCHIVE":
                is_archived = await empresas_actions_page.send_to_trash(page=page, empresa=empresa, status=RegistrationStatus.INACTIVE)
                if is_archived:
                    # Reexecuta o carregamento. Atualizar a lista de empresas na tela
                    page.run_task(load_data_and_update_ui)
                    # Não precisa de page.update() aqui, pois run_task já fará isso
            case _:
                pass

    def handle_icon_hover(e):
        """Muda o bgcolor do container no hover."""
        e.control.bgcolor = ft.Colors.with_opacity(0.1, ft.Colors.WHITE) if e.data == "true" else ft.Colors.TRANSPARENT
        e.control.update()

    appbar = create_appbar_menu(
        page=page,
        title=ft.Text(f"Empresas", size=18),
    )

    def handle_info_click(e):
        empresa = e.control.data.get('data')
        page_ctx = e.control.page # Obter a página do contexto do controle

        info_messages_list = []

        if not empresa.cnpj:
            info_messages_list.append("CNPJ: Não informado para emissão de NFCe.")
        if not empresa.certificate_a1:
            info_messages_list.append("A1: Certificado A1 não informado para emissão de NFCe.")
        if empresa.get_complete_address() == "Endereço não informado":
            info_messages_list.append("Endereço: Não informado.")

        nfce_is_enabled = empresa.is_nfce_enabled() # Chamada correta do método
        if not nfce_is_enabled:
            info_messages_list.append("NFCe: Não configurado.")

        final_info_message = "\n".join(info_messages_list)
        if not final_info_message: # Se a lista estiver vazia, significa que tudo está ok
            final_info_message = "Esta empresa está configurada para emitir NFCe."

        def close_dialog(e_dialog):
            info_dialog.open = False
            page_ctx.update()

        info_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Status da Empresa"),
            content=ft.Text(final_info_message),
            actions=[
                ft.TextButton("Entendi", on_click=close_dialog)
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            on_dismiss=lambda _: logger.info(f"Dialog de informação para {empresa.id} dispensado.")
        )

        page_ctx.overlay.append(info_dialog)
        info_dialog.open = True
        page_ctx.update()

    empresas_inactivated = 0

    # --- Função Assíncrona para Carregar Dados e Atualizar a UI ---
    async def load_data_and_update_ui():
        empresas_data = []
        nonlocal empresas_inactivated
        # set_empresas: Conjunto de ID's de empresas que o usuário gerencia
        set_empresas = page.app_state.usuario.get( # type: ignore
            'empresas', [])  # Usar get com default

        try:
            # *** IMPORTANTE: Garanta que handle_get_empresas seja async ***
            # Se handle_get_empresas for síncrona e demorar, a UI *vai* congelar.
            # Pode ser necessário refatorar handle_get_empresas para usar um driver de banco de dados async
            # ou executá-la em uma thread separada usando asyncio.to_thread (Python 3.9+)
            # Exemplo usando asyncio.to_thread se handle_get_empresas for sync:
            # empresas_data = await asyncio.to_thread(handle_get_empresas, ids_empresas=set_empresas)

            if set_empresas:  # Só busca se houver IDs
                # Busca as empresas do usuário e por default somente as empresas ativas
                result = company_controllers.handle_get_empresas(ids_empresas=set_empresas)

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
                # --- Constroe o Grid de Cards ---

                grid = ft.ResponsiveRow(
                    controls=[
                        # O componente Card() está sendo iterado em loop para uma ou mais empresas.
                        # Por isso, não é possível movê-lo para uma variável para reduzir o nível de aninhamento.
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
                                                        ft.PopupMenuItem(
                                                            text="Selecionar empresa",
                                                            tooltip="Escolha esta empresa para trabalhar com ela",
                                                            icon=ft.Icons.SELECT_ALL,
                                                            data={
                                                                'action': 'SELECT', 'data': empresa},
                                                            on_click=handle_action_click
                                                        ),
                                                        ft.PopupMenuItem(
                                                            text="Dados principais",
                                                            tooltip="Ver ou editar dados principais da empresa",
                                                            icon=ft.Icons.EDIT_NOTE_OUTLINED,
                                                            data={
                                                                'action': 'MAIN_DATA', 'data': empresa},
                                                            on_click=handle_action_click
                                                        ),
                                                        ft.PopupMenuItem(
                                                            text="Dados fiscais",
                                                            tooltip="Ver ou editar dados fiscais da empresa",
                                                            icon=ft.Icons.RECEIPT_LONG_OUTLINED,
                                                            data={
                                                                'action': 'TAX_DATA', 'data': empresa},
                                                            on_click=handle_action_click
                                                        ),
                                                        ft.PopupMenuItem(
                                                            text="Certificado digital",
                                                            tooltip="Informações e upload do certificado digital",
                                                            icon=ft.Icons.SECURITY_OUTLINED,
                                                            data={
                                                                'action': 'DIGITAL_CERTIFICATE', 'data': empresa},
                                                            on_click=handle_action_click),
                                                        ft.PopupMenuItem(
                                                            text="Excluir empresa",
                                                            tooltip="Move empresa para a lixeira, após 90 dias remove do banco de dados",
                                                            icon=ft.Icons.DELETE_OUTLINE,
                                                            data={
                                                                'action': 'SOFT_DELETE', 'data': empresa},
                                                            on_click=handle_action_click
                                                        ),
                                                        ft.PopupMenuItem(
                                                            text="Arquivar empresa",
                                                            tooltip="A empresa será movida para a lixeira e permanecerá lá indefinidamente até que você a restaure.",
                                                            icon=ft.Icons.INVENTORY_2_OUTLINED,
                                                            data={
                                                                'action': 'ARCHIVE', 'data': empresa},
                                                            on_click=handle_action_click
                                                        ),
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
                                    ft.Row(
                                        controls=[
                                            ft.Text(f"Email: {empresa.email}", theme_style=ft.TextThemeStyle.BODY_SMALL),
                                            ft.Container(
                                                content=ft.Icon(
                                                    name=ft.Icons.INFO_OUTLINED,
                                                    color=ft.Colors.PRIMARY,
                                                ),
                                                margin=ft.margin.only(right=10),
                                                tooltip="Informações sobre o status",
                                                data={'action': 'INFO', 'data': empresa},
                                                on_hover=handle_icon_hover,
                                                on_click=handle_info_click,
                                                border_radius=ft.border_radius.all(20),
                                                ink=True,
                                                bgcolor=ft.Colors.TRANSPARENT,
                                                alignment=ft.alignment.center,
                                                clip_behavior=ft.ClipBehavior.ANTI_ALIAS
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
                        ft.Icon(ft.Icons.ERROR_OUTLINE,
                                color=ft.Colors.RED, size=50),
                        ft.Text(
                            f"Ocorreu um erro ao carregar as empresas.", color=ft.Colors.RED),
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
            # --- Atualizar Visibilidade da UI ---
            current_trash_icon_filename = "recycle_full_1771.png" if empresas_inactivated else "recycle_empy_1771.png"
            if fab_trash.content and isinstance(fab_trash.content, ft.Image): # Garante que fab_trash.content é uma Image
                fab_trash.content.src = f"icons/{current_trash_icon_filename}"
                fab_trash.tooltip = f"Empresas inativas: {empresas_inactivated}"

            loading_container.visible = False
            content_area.visible = True
            # Importante: Atualizar a página para refletir as mudanças
            # Checar se o contexto da página ainda é válido antes de atualizar
            if page.client_storage:  # Uma checagem se a página ainda está ativa
                page.update()
            else:
                logger.info("Contexto da página perdido, não foi possível atualizar.")

    # --- Disparar Carregamento dos Dados ---
    # Executa a função async em background. A UI mostrará o spinner primeiro.
    page.run_task(load_data_and_update_ui)

    fab_add = ft.FloatingActionButton(
        tooltip="Adicionar empresa",
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
        on_click=lambda _: page.go("/home/empresas/grid/lixeira"),
        tooltip="Empresas inativas: 0",
        bgcolor=ft.Colors.TRANSPARENT,
    )

    # Resetar alinhamentos da página que podem interferir com o layout da View
    # page.vertical_alignment = ft.MainAxisAlignment.START
    # page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH

    # --- Retornar Estrutura Inicial da Página como ft.View ---
    # A View inclui a AppBar e a área de conteúdo principal (que inicialmente mostra o spinner)
    return ft.View(
        route="/home/empresas/grid",  # A rota que esta view corresponde
        controls=[
            loading_container,  # Mostra o spinner inicialmente
            content_area       # Oculto inicialmente, populado por load_data_and_update_ui
        ],
        appbar=appbar,
        drawer=page.drawer,
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

    # ft.View(
    #     scroll=ft.ScrollMode.AUTO,
    #     bgcolor=ft.Colors.BLACK,
    # )

# Nota: Garanta que a função `handle_get_empresas` localizada em
# `src.domains.empresas.controllers.company_controllers` esteja definida como uma função `async def`
# para que esta abordagem de indicador de carregamento funcione sem congelar a UI durante a chamada ao banco de dados.
# Se for uma função síncrona, você precisará adaptá-la usando técnicas como
# `asyncio.to_thread` conforme mostrado nos comentários dentro de `load_data_and_update_ui`.
