import flet as ft

from src.pages.partials.login_button import LoginButton


def landing_page(page: ft.Page):
    page.theme_mode = ft.ThemeMode.LIGHT

    title_bar = ft.Text(
        value="ESTOQUE RÁPIDO: Soluções Eficientes para Gestão de Estoque e Finanças",
        color=ft.Colors.WHITE,
    )

    def handle_page_resize(e):
        # Obtém a largura da página de forma segura
        width = page.width
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

        page.update()

    login_btn = LoginButton(page)

    page.appbar = ft.AppBar(
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

    def landing_card(icons: list, title: str, description: str, show_more: str) -> ft.Card:
        return ft.Card(
            col={'xs': 12, 'md': 6, 'lg': 4},
            width=250,
            height=270,
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
                            controls=icons,
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                        ft.Text(
                            title, size=16, weight=ft.FontWeight.BOLD),
                        ft.Text(description),
                        ft.ElevatedButton(
                            "Saiba Mais",
                            style=ft.ButtonStyle(
                                color=ft.Colors.WHITE,
                                bgcolor=ft.Colors.BLUE_700,
                                padding=ft.padding.all(20),
                            ),
                            on_click=lambda e: card_show_more(
                                e, title, show_more),
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
                    icons=[ft.Icon(ft.Icons.INVENTORY, size=40,
                                   color=ft.Colors.BLUE_400)],
                    title="Gestão de Estoque",
                    description="Controle total do seu inventário",
                    show_more="A Gestão de Estoque permite monitorar e controlar todos os produtos disponíveis, garantindo que você tenha sempre a quantidade certa em mãos. Com relatórios detalhados e alertas de reabastecimento, você pode otimizar seu inventário e evitar perdas."
                ),
                landing_card(
                    icons=[ft.Icon(ft.Icons.ADD_BUSINESS, size=40,
                                   color=ft.Colors.BLUE_400)],
                    title="Gestão Vendas",
                    description="Otimização de processos e estratégias para maximizar as vendas e fidelizar clientes.",
                    show_more="A Gestão de Vendas oferece uma visão clara das suas transações, permitindo acompanhar o desempenho das vendas em tempo real. Com análises detalhadas, você pode identificar tendências e ajustar suas estratégias para maximizar a receita."
                ),
                landing_card(
                    icons=[ft.Icon(ft.Icons.ATTACH_MONEY_OUTLINED,
                                   size=40, color=ft.Colors.BLUE_400)],
                    title="Gestão Financeira",
                    description="Controle eficiente de recursos financeiros para garantir estabilidade e crescimento sustentável.",
                    show_more="A Gestão Financeira proporciona um controle completo sobre suas finanças, incluindo receitas, despesas e lucros. Com relatórios financeiros precisos, você pode tomar decisões informadas e garantir a saúde financeira do seu negócio."
                ),
                landing_card(
                    icons=[ft.Icon(ft.Icons.BAR_CHART, size=40,
                                   color=ft.Colors.BLUE_400)],
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
        width=1400,
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

    footer = ft.Container(
        padding=10,
        bgcolor=ft.Colors.BLUE_700,
        alignment=ft.alignment.center,
        content=ft.Row(
            expand=True,
            alignment=ft.MainAxisAlignment.CENTER,
            controls=[
                ft.TextButton(
                    content=ft.Row(
                        controls=[
                            ft.Text(
                                value="© 2025 Sistrom Sistemas Web. Todos os direitos reservados.",
                                color=ft.Colors.GREY_400,
                                size=12,
                                text_align=ft.TextAlign.CENTER,
                            ),
                            ft.Icon(
                                name="images/logo_sistrom.png", size=14),
                        ],
                        tight=True,
                    ),
                    url="https://sistrom.com.br/site/#sistemas",
                    tooltip="Clique aqui para acessar o site",
                ),
            ],
        ),
    )

    page.on_resized = handle_page_resize

    parent_container = ft.Container(
        expand=True,
        height=page.height,
        alignment=ft.alignment.center,
        content=ft.Column(
            spacing=0,
            alignment=ft.alignment.center,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                main_content,
                footer,
            ]
        )
    )

    page.update()

    return parent_container
