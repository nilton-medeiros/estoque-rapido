import flet as ft
from datetime import datetime, UTC
import locale
import platform

from src.shared.utils.time_zone import format_datetime_to_utc_minus_3

# Problemas de acentuação ao mostrar texto no navegador web quando sob S.O. Windows. Corrigido desta forma:
# Configurar o locate dinamicamente
if platform.system() == "Windows":
    locale.setlocale(locale.LC_TIME, 'pt_BR')
else:
    try:
        locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
    except locale.Error:
        # Fallback para o locale padrão do sistema, se o desejado não estiver disponível
        locale.setlocale(locale.LC_TIME, '')

from typing import Any, Callable


class MainContent(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page

        # Referências para os TextSpans que exibem os dados do dashboard
        self.low_stok_prefix_span = ft.TextSpan(
            text="0 ", # Valor inicial
            style=ft.TextStyle(
                color=ft.Colors.PRIMARY,
                weight=ft.FontWeight.W_900,
                size=20,
            )
        )
        self.orders_prefix_span = ft.TextSpan(text="0 ", style=self.low_stok_prefix_span.style)
        self.payments_prefix_span = ft.TextSpan(text="0 ", style=self.low_stok_prefix_span.style)
        self.receipts_prefix_span = ft.TextSpan(text="0 ", style=self.low_stok_prefix_span.style)

        self.low_stok_text_control = self._create_news_text_control(self.low_stok_prefix_span, 'Produtos para repor')
        self.orders_text_control = self._create_news_text_control(self.orders_prefix_span, 'Encomendas')
        self.payments_text_control = self._create_news_text_control(self.payments_prefix_span, 'Pagamentos')
        self.receipts_text_control = self._create_news_text_control(self.receipts_prefix_span, 'Recebimentos')

        self._build_layout()
        self.page.pubsub.subscribe(self._on_dashboard_event)
        self._update_dashboard_display() # Carrega os dados iniciais

    def content_card(self, icons: list, title: str, click_action: Callable[[Any], None], tool_tip: str | None = None) -> ft.Card:
        return ft.Card(
            content=ft.Container(
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[
                        ft.Row(
                            controls=icons,
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                        ft.Text(
                            title,
                            color=ft.Colors.WHITE,
                            size=16,
                            weight=ft.FontWeight.NORMAL,
                        ),
                    ],
                ),
                tooltip= tool_tip,
                expand=True,
                padding=20,
                bgcolor=ft.Colors.ON_INVERSE_SURFACE,
                border_radius=10,
                on_click=click_action,
                on_hover=self._on_hover_card,
            ),
            col={'xs': 12, 'md': 6, 'lg': 4},
            width=200,
            height=150,
        )

    def _create_news_text_control(self, prefix_span: ft.TextSpan, description: str) -> ft.Text:
        return ft.Text(
            col={'xs': 6, 'md': 3},
            text_align=ft.TextAlign.CENTER,
            spans=[
                prefix_span,
                ft.TextSpan(
                    text=description,
                    style=ft.TextStyle(
                        color=ft.Colors.WHITE,
                        size=16,
                    )
                )
            ]
        )

    def _on_hover_card(self, e):
        e.control.bgcolor = ft.Colors.OUTLINE_VARIANT if e.data == "true" else ft.Colors.ON_INVERSE_SURFACE
        e.control.update()

    def _update_dashboard_display(self):
        # Adiciona uma verificação para self.page para satisfazer o Pylance e aumentar a robustez
        if not self.page:
            print("Debug  -> MainContent._update_dashboard_display -> self.page is None. Skipping update.")
            return
        dashboard_data = self.page.session.get("dashboard") or {}
        print(f"Debug  -> MainContent._update_dashboard_display -> dashboard_data: {dashboard_data}")

        self.low_stok_prefix_span.text = f"{dashboard_data.get('repor_produtos', 0)} "
        self.orders_prefix_span.text = f"{dashboard_data.get('encomendas', 0)} "
        self.payments_prefix_span.text = f"{dashboard_data.get('pagamentos', 0)} "
        self.receipts_prefix_span.text = f"{dashboard_data.get('recebimentos', 0)} "

        # Atualiza os controles de texto individualmente ou o container deles
        if self.page and self.news_container.page: # Garante que o controle está na página
            self.news_container.update()

    def _on_dashboard_event(self, message):
        if message == "dashboard_refreshed":
            print("Debug -> MainContent recebeu 'dashboard_refreshed'")
            self._update_dashboard_display()
        elif message == "empresa_updated": # Se a empresa mudar, também pode precisar limpar/redefinir
            print("Debug -> MainContent recebeu 'empresa_updated', atualizando dashboard display")
            self._update_dashboard_display()

    def _build_layout(self):
        # date_description = datetime.now(UTC).strftime("%A, %d de %B")
        date_description = format_datetime_to_utc_minus_3(datetime.now(UTC), "%A, %d de %B")

        side_left = ft.Container(
            col={'md': 12, 'lg': 8},
            padding=ft.padding.all(20),
            content=ft.Column(
                controls=[
                    ft.Text(value='Estoque Rápido',
                            theme_style=ft.TextThemeStyle.HEADLINE_LARGE),
                    ft.Text(
                        spans=[
                            ft.TextSpan(
                                text="Gestão de Estoque, Vendas, Financeiro, Fluxo de Caixa e NFC-e.",
                                style=ft.TextStyle(
                                    color=ft.Colors.WHITE),
                        ),
                    ],
                    theme_style=ft.TextThemeStyle.BODY_MEDIUM,
                ),
                ft.Row(
                    col={'xs': 6, 'md': 3},
                    alignment=ft.MainAxisAlignment.START,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Text("Hoje", style=ft.TextStyle(color=ft.Colors.WHITE, weight=ft.FontWeight.W_900, size=20)),
                        ft.Container(
                            content=ft.Text(".", style=ft.TextStyle(color=ft.Colors.WHITE, weight=ft.FontWeight.W_900, size=40)),
                            offset=ft.transform.Offset(0, -0.2),
                        ),
                        ft.Text(date_description, style=ft.TextStyle(color=ft.Colors.PRIMARY, size=18)),
                    ],
                ),
            ],
            spacing=20,
            alignment=ft.MainAxisAlignment.START,
        ))

        side_right = ft.Container(
            margin=ft.margin.only(top=20),
            col={'xl': 2, 'md': 2, 'lg': 4},
            content=ft.Image(src='images/face-2.png', width=20, scale=ft.Scale(scale=1, alignment=ft.alignment.top_center))
        )

        banner = ft.Container(
            bgcolor='#111418',
            margin=ft.margin.only(top=0),
            height=200,
            content=ft.ResponsiveRow(columns=12, vertical_alignment=ft.CrossAxisAlignment.START, controls=[side_left, side_right])
        )

        self.news_container = ft.Container(
            content=ft.ResponsiveRow(
                columns=12,
                controls=[
                    self.low_stok_text_control,
                    self.orders_text_control,
                    self.payments_text_control,
                    self.receipts_text_control,
                ]
            ),
            bgcolor="#111418",
            margin=ft.margin.only(top=40, bottom=40),
            padding=0,
        )

        # --- Cards de Ação ---
        # (O código para on_click_registrar, on_click_status, on_click_nfce e content_card permanece o mesmo)
        # ... (Adapte para usar self.content_card e self._on_hover_card se necessário, ou mantenha-os como funções locais/estáticas)

        # Exemplo de como os cards seriam criados (simplificado)
        # Mantenha as funções on_click como métodos da classe se elas precisarem acessar self ou page
        salles_cards = [
            self.content_card(icons=[ft.Icon(ft.Icons.ADD, size=40, color=ft.Colors.PRIMARY), ft.Icon(ft.Icons.POINT_OF_SALE, size=40, color=ft.Colors.PRIMARY)], title="Registrar", click_action=self._on_click_registrar, tool_tip="Registrar venda"),
            self.content_card(icons=[ft.Icon(ft.Icons.NOTE_ALT_OUTLINED, size=40, color=ft.Colors.PRIMARY)], title="Status", click_action=self._on_click_status, tool_tip="Verificar status da venda"),
            self.content_card(icons=[ft.Icon(ft.Icons.ATTACH_MONEY_OUTLINED, size=40, color=ft.Colors.PRIMARY)], title="NFC-e", click_action=self._on_click_nfce, tool_tip="Gerar Nota Fiscal de Consumidor Eletrônica"),
        ]

        salles = ft.Container(
            content=ft.ResponsiveRow(controls=salles_cards),
            col={"xs": 12, "md": 7, "lg": 8, "xxl": 9}, expand=True, bgcolor="#111418",
            border_radius=10, alignment=ft.alignment.top_center, margin=ft.margin.only(top=30, bottom=30)
        )

        stock = ft.Container(
            col={"xs": 12, "md": 7, "lg": 8, "xxl": 9}, expand=True, bgcolor="#111418",
            border_radius=10, alignment=ft.alignment.center, margin=ft.margin.symmetric(vertical=40)
        )

        financial = ft.Container(
            col={"xs": 12, "md": 7, "lg": 8, "xxl": 9}, expand=True, bgcolor="#111418",
            border_radius=10, alignment=ft.alignment.center, margin=ft.margin.symmetric(vertical=40)
        )

        # --- Layout Final do Container ---
        self.content = ft.Column(
            controls=[
                banner,
                self.news_container,
                self._sections_title(title='Vendas'),
                salles,
                self._sections_title(title="Estoque"),
                stock,
                self._sections_title(title="Financeiro"),
                financial,
            ],
            scroll=ft.ScrollMode.HIDDEN,
            alignment=ft.MainAxisAlignment.START,
            spacing=0,
        )
        self.bgcolor = "#111418"
        self.padding = ft.padding.only(left=20, right=20, bottom=20)

    # --- Métodos Helper para Ações e Títulos (movidos para dentro da classe) ---
    def _on_click_registrar(self, e):
        print(f"on_click_registrar {e.control}")

    def _on_click_status(self, e):
        print(f"on_click_status {e.control}")

    def _on_click_nfce(self, e):
        print(f"on_click_nfce {e.control}")

    def _sections_title(self, title: str):
        return ft.Container(content=ft.Text(value=title, theme_style=ft.TextThemeStyle.HEADLINE_MEDIUM))


# Função original que será chamada para criar a instância de MainContent
def main_content(page: ft.Page) -> MainContent:
    return MainContent(page)
