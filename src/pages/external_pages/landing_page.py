import flet as ft
from src.shared.config.version import APP_VERSION

from src.pages.partials import LoginButton

def show_landing_page(page: ft.Page) -> ft.View:
    page.theme_mode = ft.ThemeMode.LIGHT

    title_bar = ft.Text(
        value="ESTOQUE RÁPIDO: Soluções Eficientes para Gestão de Estoque e Finanças",
        color=ft.Colors.WHITE,
    )
    from src.shared.config import version
    print(f"🧾 App rodando com versão {version.APP_VERSION}")
    # Containers do footer para controle dinâmico de alinhamento
    footer_version_container = ft.Container(
        content=ft.Text(
            f"Estoque Rápido v{APP_VERSION}",
            size=12,
            color=ft.Colors.WHITE,
            weight=ft.FontWeight.W_500,
        ),
        col={"xs": 12, "md": 6},
        alignment=ft.alignment.center_left,  # Inicial: esquerda
    )

    footer_copyright_row = ft.Row(
        controls=[
            ft.Text(
                "© 2025 Desenvolvido por",
                size=12,
                color=ft.Colors.GREY_400,
            ),
            ft.TextButton(
                text="Sistrom Sistemas Web.",
                url="https://sistrom.com.br/site/#sistemas",
                tooltip="Clique para acessar o site",
                style=ft.ButtonStyle(
                    padding=ft.padding.only(left=4, right=4),
                    overlay_color=ft.Colors.TRANSPARENT,
                    color={
                        ft.ControlState.DEFAULT: ft.Colors.WHITE,
                        ft.ControlState.HOVERED: ft.Colors.BLUE_200
                    },
                ),
            ),
        ],
        spacing=0,
        alignment=ft.MainAxisAlignment.END,  # Inicial: direita
        tight=True,
    )

    footer_copyright_container = ft.Container(
        content=footer_copyright_row,
        col={"xs": 12, "md": 6},
        alignment=ft.alignment.center_right,  # Inicial: direita
    )

    # Modifique a função handle_page_resize para incluir o controle do footer:
    def handle_page_resize(e):
        # Obtém a largura da página de forma segura
        width: int | float = page.width if page.width is not None else 600
        size = 18

        title_bar.value = "ESTOQUE RÁPIDO: Soluções Eficientes para Gestão de Estoque e Finanças"
        title_bar.size = size

        if width < 600:         # xs
            size = 10
            title_bar.max_lines = 2

            if width < 576:
                size = 8
                if width < 545:
                    title_bar.value = "ESTOQUE RÁPIDO" if width >= 435 else "ER"
        elif width < 900:       # sm
            size = 12
        elif width < 1200:      # md
            size = 14
        elif width < 1500:      # lg
            size = 16
        else:                   # xl
            size = 18

        title_bar.size = size

        # Atualiza o botão de login
        login_btn.update_sizes(width)

        # NOVO: Controle dinâmico de alinhamento do footer
        if width < 768:  # Breakpoint md (telas pequenas)
            # Centraliza ambos os elementos
            footer_version_container.alignment = ft.alignment.center
            footer_copyright_container.alignment = ft.alignment.center
            footer_copyright_row.alignment = ft.MainAxisAlignment.CENTER
        else:  # Telas grandes
            # Mantém alinhamento original (esquerda e direita)
            footer_version_container.alignment = ft.alignment.center_left
            footer_copyright_container.alignment = ft.alignment.center_right
            footer_copyright_row.alignment = ft.MainAxisAlignment.END

        page.update()

    # Atualize a definição do footer para usar os containers criados:
    footer = ft.Container(
        expand=True,
        padding=ft.padding.symmetric(horizontal=20, vertical=10),
        bgcolor=ft.Colors.BLUE_700,
        content=ft.ResponsiveRow(
            columns=12,
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True,
            spacing=0,
            run_spacing=10,
            controls=[
                footer_version_container,
                footer_copyright_container,
            ],
        ),
    )

    login_btn = LoginButton(page)

    lp_title = ft.Text(
        "Bem-vindo ao Estoque Rápido!",
        size=30,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.BLUE_700,
        text_align=ft.TextAlign.CENTER,
    )

    lp_subtitle = ft.Text(
        "Controle de estoque simplificado para sua empresa.",
        size=18,
        color=ft.Colors.GREY_800,
        text_align=ft.TextAlign.CENTER,
    )

    def card_show_more(e, title, show_more: str):
        def handle_close(e):
            page.close(dlg_modal)

        dlg_modal = ft.AlertDialog(
            modal=True,
            title=ft.Text(title),
            content=ft.Text(show_more),
            actions=[
                ft.TextButton("Fechar", on_click=handle_close),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        page.open(dlg_modal)

    def landing_card(icons: list[ft.Icon], title: str, description: str, show_more: str) -> ft.Card:
        return ft.Card(
            col={'xs': 12, 'md': 6, 'lg': 4},
            width=350,
            height=250,
            content=ft.Container(
                expand=True,
                padding=20,
                bgcolor=ft.Colors.BLUE_GREY_100,
                border_radius=10,
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[
                        ft.Row(
                            controls=[
                                *icons,   # Descompacta a lista de icons
                                ft.Text(
                                    title,
                                    color=ft.Colors.BLACK54,
                                    size=16,
                                    weight=ft.FontWeight.BOLD,
                                    text_align=ft.TextAlign.CENTER,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                        ft.Text(
                            description,
                            color=ft.Colors.BLACK87,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Container(
                            content=ft.ElevatedButton(
                                "Saiba Mais",
                                style=ft.ButtonStyle(
                                    color=ft.Colors.WHITE,
                                    bgcolor=ft.Colors.BLUE_700,
                                    padding=ft.padding.all(20),
                                ),
                                on_click=lambda e: card_show_more(
                                    e, title, show_more),
                            ),
                            margin=ft.margin.only(bottom=20),
                        ),
                    ],
                ),
            ),
        )

    cards = ft.Container(
        content=ft.ResponsiveRow(
            columns=12,
            expand=True,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=30,
            run_spacing=30,
            controls=[
                landing_card(
                    icons=[ft.Icon(ft.Icons.INVENTORY, size=40, color=ft.Colors.BLUE_400, tooltip="Ícone de gestão de estoque")],
                    title="Gestão de Estoque",
                    description="Controle total do seu inventário",
                    show_more="A Gestão de Estoque permite monitorar e controlar todos os produtos disponíveis, garantindo que você tenha sempre a quantidade certa em mãos. Com relatórios detalhados e alertas de reabastecimento, você pode otimizar seu inventário e evitar perdas."
                ),
                landing_card(
                    icons=[ft.Icon(ft.Icons.ADD_BUSINESS, size=40, color=ft.Colors.BLUE_400, tooltip="Ícone de gestão de vendas")],
                    title="Gestão Vendas",
                    description="Otimização de processos e estratégias para maximizar as vendas e fidelizar clientes.",
                    show_more="A Gestão de Vendas oferece uma visão clara das suas transações, permitindo acompanhar o desempenho das vendas em tempo real. Com análises detalhadas, você pode identificar tendências e ajustar suas estratégias para maximizar a receita."
                ),
                landing_card(
                    icons=[ft.Icon(ft.Icons.ATTACH_MONEY_OUTLINED, size=40, color=ft.Colors.BLUE_400, tooltip="Ícone de gestão de financeira")],
                    title="Gestão Financeira",
                    description="Controle eficiente de recursos financeiros para garantir estabilidade e crescimento sustentável.",
                    show_more="A Gestão Financeira proporciona um controle completo sobre suas finanças, incluindo receitas, despesas e lucros. Com relatórios financeiros precisos, você pode tomar decisões informadas e garantir a saúde financeira do seu negócio."
                ),
                landing_card(
                    icons=[ft.Icon(ft.Icons.BAR_CHART, size=40, color=ft.Colors.BLUE_400, tooltip="Ícone do fluxo de caixa")],
                    title="Fluxo de Caixa",
                    description="Monitoramento de entradas e saídas de dinheiro para manter a saúde financeira da empresa.",
                    show_more="O Fluxo de Caixa é essencial para entender a movimentação de dinheiro no seu negócio. Com uma visão clara das entradas e saídas, você pode planejar melhor seus investimentos e garantir que sempre haja liquidez."
                ),
                landing_card(
                    icons=[
                        ft.Icon(ft.Icons.DESKTOP_WINDOWS_OUTLINED,
                                size=40, color=ft.Colors.BLUE_400),
                        ft.Icon(ft.Icons.TABLET_ANDROID_OUTLINED,
                                size=40, color=ft.Colors.BLUE_400),
                        ft.Icon(ft.Icons.PHONE_ANDROID, size=40,
                                color=ft.Colors.BLUE_400),
                    ],
                    title="Multi-plataforma",
                    description="Acesse de qualquer dispositivo",
                    show_more="A funcionalidade Multi-plataforma permite acessar o sistema de qualquer dispositivo, seja desktop, tablet ou smartphone. Isso garante que você possa gerenciar seu estoque, vendas e finanças a qualquer hora e em qualquer lugar."
                ),
            ],
        ),
        alignment=ft.alignment.center,
        expand=True,
        margin=ft.margin.symmetric(vertical=40),
    )

    def on_hover_button(e):
        # Verifica se o cursor entrou ou saiu
        e.control.bgcolor = ft.Colors.BLUE_800 if e.data == "true" else ft.Colors.BLUE_700
        e.control.update()

    startfree_button = ft.ElevatedButton(
        "Comece seu teste grátis",
        style=ft.ButtonStyle(
            color=ft.Colors.WHITE,
            bgcolor=ft.Colors.BLUE_700,  # Cor inicial
            padding=ft.padding.all(20),
        ),
        on_click=lambda _: page.go('/signup'),
        on_hover=on_hover_button  # Ativa o efeito de hover
    )

    main_content = ft.Container(
        expand=True,
        # width=1920,
        alignment=ft.alignment.center,
        padding=20,
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                lp_title,
                lp_subtitle,
                cards,
                startfree_button,
            ],
        ),
    )

    page.on_resized = handle_page_resize

    parent_container = ft.Container(
        expand=True,
        alignment=ft.alignment.center,
        content=ft.Column(
            spacing=0,
            expand=True,
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                main_content,
                footer,
            ]
        )
    )

    appbar = ft.AppBar(
        leading=ft.Icon(name=ft.Icons.INVENTORY_OUTLINED,
                        color=ft.Colors.WHITE),
        leading_width=40,
        title=title_bar,
        bgcolor=ft.Colors.BLUE_700,
        actions=[
            ft.Container(
                content=login_btn.build(),
                margin=ft.margin.only(right=10),
            )
        ],
    )

    return ft.View(
        route="/",
        controls=[parent_container],
        appbar=appbar,
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )
