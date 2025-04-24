import flet as ft

from src.domains.empresas.controllers.empresas_controllers import handle_get_empresas


# Rota: /home/empresas/grid
def empresas_grid(page: ft.Page):
    """Página de exibição das empresas do usuário logado em formato Cards"""
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.theme_mode = ft.ThemeMode.DARK

    # ToDo: UI: Mostrar um spin enquanto o frontend faz consulta ao banco de dados e traz as empresas do usuário logado
    print("Entrou em empresas_grid...")

    set_empresas = page.app_state.usuario.get('empresas')
    # colors = page.app_state.usuario.get('user_colors')

    content = ft.Container(
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
        expand=True,
    )

    def handle_icon_hover(e):
        """Muda o bgcolor do container no hover."""
        e.control.bgcolor = ft.Colors.with_opacity(
            0.1, ft.Colors.WHITE) if e.data == "true" else ft.Colors.TRANSPARENT
        e.control.update()

    def handle_action_click(action: str):
        """Função para lidar com cliques nas ações do menu ou botões."""
        print(f"Ação '{action}' selecionada.")
        # Aqui você implementaria a lógica para cada ação
        match action:
            case "Incluir":
                # ToDo: Enviar o callback/flag para esta página à página /empresas/form
                page.go('/empresas/form')  # Exemplo: ir para o formulário
            case "Excluir":
                # Lógica para excluir (provavelmente precisa de seleção prévia)
                pass
            case "Dados Principais":
                # Lógica para ver/editar dados (provavelmente precisa de seleção prévia)
                pass
            case "Certificado Digital":
                # Lógica para certificado (provavelmente precisa de seleção prévia)
                pass
            case "Nota Fiscal":
                # Lógica para nota fiscal (provavelmente precisa de seleção prévia)
                pass

    appbar = ft.AppBar(
        leading=ft.Container(
            alignment=ft.alignment.center_left,
            padding=ft.padding.only(left=10),
            content=ft.Container(
                width=40,
                height=40,
                border_radius=ft.border_radius.all(20),
                # Aplica ink ao wrapper (ao clicar da um feedback visual para o usuário)
                ink=True,
                bgcolor=ft.Colors.TRANSPARENT,
                alignment=ft.alignment.center,
                on_hover=handle_icon_hover,
                content=ft.Icon(ft.Icons.ARROW_BACK),
                on_click=lambda _: page.go("/home"),
                tooltip="Voltar",
                # Ajuda a garantir que o hover respeite o border_radius
                clip_behavior=ft.ClipBehavior.ANTI_ALIAS
            ),
        ),
        title=ft.Text("Empresas"),
        bgcolor=ft.Colors.with_opacity(
            0.9, ft.Colors.PRIMARY_CONTAINER),  # Exemplo com opacidade
        adaptive=True,
        actions=[
            # 1. Botão Principal (Incluir/Nova) - Visível
            ft.IconButton(
                icon=ft.Icons.ADD_CIRCLE_OUTLINE,  # Ou ft.Icons.ADD
                tooltip="Incluir Nova Empresa",
                on_click=lambda _: handle_action_click("Incluir"),
                # Você pode estilizar com ft.Container se precisar de fundo, etc.
                # Ou usar um ft.TextButton("Nova", on_click=...)
            ),
            # 2. Container para adicionar padding ao PopupMenuButton
            ft.Container(
                # Adiciona 10 pixels de espaço à direita do container,
                # empurrando o PopupMenuButton para a esquerda.
                padding=ft.padding.only(right=10),
                content=ft.PopupMenuButton( # O botão original agora é o conteúdo do contai
                    icon=ft.Icons.MORE_VERT,  # Ícone padrão de "mais opções"
                    tooltip="Mais Ações",
                    items=[
                        ft.PopupMenuItem(
                            text="Excluir Empresa",
                            icon=ft.Icons.DELETE_OUTLINE,
                            on_click=lambda _: handle_action_click("Excluir")
                        ),
                        ft.PopupMenuItem(
                            text="Dados Principais",
                            icon=ft.Icons.EDIT_NOTE_OUTLINED,
                            on_click=lambda _: handle_action_click("Dados Principais")
                        ),
                        ft.PopupMenuItem(
                            text="Certificado Digital",
                            icon=ft.Icons.SECURITY_OUTLINED,
                            on_click=lambda _: handle_action_click(
                                "Certificado Digital")
                        ),
                        ft.PopupMenuItem(
                            text="Nota Fiscal",
                            icon=ft.Icons.RECEIPT_LONG_OUTLINED,
                            on_click=lambda _: handle_action_click("Nota Fiscal")
                        ),
                    ],
                ),
            ) # Fim do Container que envolve o PopupMenuButton
        ],
    )

    if len(set_empresas) > 0:
        pass

    # result = await handle_get_empresas(ids_empresas=set_empresas)



    # ToDo: Parar o spin aqui após obter os dados do banco de dados

    return ft.Column(
        controls=[content],
        data=appbar,
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )
