import flet as ft
import datetime
import locale
import platform

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

from typing import Callable


def main_content():
    def on_hover_card(e):
        # Verifica se o cursor entrou ou saiu
        e.control.bgcolor = "#3a3a46" if e.data == "true" else ft.Colors.ON_INVERSE_SURFACE
        e.control.update()

    def content_card(icons: list, title: str, click_action: Callable[[any], None]) -> ft.Card:
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
                expand=True,
                padding=20,
                bgcolor=ft.Colors.ON_INVERSE_SURFACE,
                border_radius=10,
                on_click=click_action,
                on_hover=on_hover_card,
            ),
            col={'xs': 12, 'md': 6, 'lg': 4},
            width=200,
            height=150,
        )

    # Obter a data corrente, ex: '04 de março'
    date_description = datetime.datetime.now().strftime("%d de %B")
    # Garantir que o texto esteja em UTF-8
    # date_description = date_description.encode().decode('utf-8')

    def news_text(prefix: str, description: str):
        return ft.Text(
            col={'xs': 6, 'md': 3},
            text_align=ft.TextAlign.CENTER,
            spans=[
                ft.TextSpan(
                    text=prefix,
                    style=ft.TextStyle(
                        color=ft.Colors.PRIMARY,
                        weight=ft.FontWeight.W_900,
                        size=20,
                    )
                ),
                ft.TextSpan(
                    text=description,
                    style=ft.TextStyle(
                        color=ft.Colors.WHITE,
                        size=16,
                    )
                )
            ]
        )

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
                        ft.Text(
                            "Hoje",
                            style=ft.TextStyle(
                                color=ft.Colors.WHITE,
                                weight=ft.FontWeight.W_900,
                                size=20,
                            )
                        ),
                        ft.Container(
                            content=ft.Text(
                                ".",
                                style=ft.TextStyle(
                                    color=ft.Colors.WHITE,
                                    weight=ft.FontWeight.W_900,
                                    size=40,  # O tamanho maior do ponto
                                )
                            ),
                            offset=ft.transform.Offset(0, -0.2),
                        ),
                        ft.Text(
                            date_description,
                            style=ft.TextStyle(
                                color=ft.Colors.PRIMARY,
                                size=18,
                            )
                        ),
                    ],
                ),
            ],
            spacing=20,
            alignment=ft.MainAxisAlignment.START,
        )
    )

    side_right = ft.Container(
        margin=ft.margin.only(top=20),
        col={'xl': 2, 'md': 2, 'lg': 4},
        content=ft.Image(
            src='images/face-2.png',
            width=20,
            scale=ft.Scale(scale=1, alignment=ft.alignment.top_center),
        )
    )

    banner = ft.Container(
        # shadow=ft.BoxShadow(
        #     color='#2d2d3a',
        #     offset=ft.Offset(x=0, y=-60),
        #     spread_radius=-30,
        # ),
        # image=ft.Image(
        #     src='images/bg.jpg',
        #     # fit=ft.ImageFit.NONE,
        #     repeat=ft.ImageRepeat.NO_REPEAT,
        #     opacity=0.5,
        #     # width=100,
        #     # height=200,
        # ),
        bgcolor='#111418',
        margin=ft.margin.only(top=0),
        height=200,
        content=ft.ResponsiveRow(
            columns=12,
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=[side_left, side_right],
        )
    )

    news = ft.Container(
        content=ft.ResponsiveRow(
            columns=12,
            controls=[
                news_text('4 ', 'Produtos para reabastecer'),
                news_text('7 ', 'Encomendas pendentes'),
                news_text('3 ', 'Pagamentos'),
                news_text('5 ', 'Recebimentos'),
            ]
        ),
        bgcolor="#111418",
        margin=ft.margin.only(top=40, bottom=40),
        padding=0,
    )

    def on_click_registrar(e):
        print(f"on_click_registrar {e.control}")

    def on_click_status(e):
        print(f"on_click_status {e.control}")

    def on_click_nfce(e):
        print(f"on_click_nfce {e.control}")

    salles = ft.Container(
        content=ft.ResponsiveRow(
            controls=[
                content_card(
                    icons=[
                        ft.Icon(ft.Icons.ADD,
                                size=40, color=ft.Colors.PRIMARY),
                        ft.Icon(ft.Icons.POINT_OF_SALE,
                                size=40, color=ft.Colors.PRIMARY),
                    ],
                    title="Registrar",
                    click_action=on_click_registrar,
                ),
                content_card(
                    icons=[ft.Icon(ft.Icons.NOTE_ALT_OUTLINED, size=40,
                                   color=ft.Colors.PRIMARY)],
                    title="Status",
                    click_action=on_click_status,
                ),
                content_card(
                    icons=[ft.Icon(ft.Icons.ATTACH_MONEY_OUTLINED,
                                   size=40, color=ft.Colors.PRIMARY)],
                    title="NFC-e",
                    click_action=on_click_nfce,
                ),
            ],
            # spacing=30,
            # run_spacing=30,
        ),
        col={"xs": 12, "md": 7, "lg": 8, "xxl": 9},
        expand=True,
        bgcolor="#111418",
        border_radius=10,
        alignment=ft.alignment.top_center,
        margin=ft.margin.only(top=30, bottom=30),
        # padding=ft.padding.all(20),
    )

    stock = ft.Container(
        col={"xs": 12, "md": 7, "lg": 8, "xxl": 9},
        expand=True,
        bgcolor="#111418",
        border_radius=10,
        alignment=ft.alignment.center,
        margin=ft.margin.symmetric(vertical=40),
        # padding=ft.padding.all(20),
    )

    financial = ft.Container(
        col={"xs": 12, "md": 7, "lg": 8, "xxl": 9},
        expand=True,
        bgcolor="#111418",
        border_radius=10,
        alignment=ft.alignment.center,
        margin=ft.margin.symmetric(vertical=40),
        # padding=ft.padding.all(20),
    )

    def sections_title(title: str):
        return ft.Container(
            # padding=ft.padding.symmetric(vertical=20),
            content=ft.Text(
                value=title, theme_style=ft.TextThemeStyle.HEADLINE_MEDIUM),
        )

    return ft.Container(
        content=ft.Column(
            controls=[
                banner,
                news,
                sections_title(title='Vendas'),
                salles,
                sections_title(title="Estoque"),
                stock,
                sections_title(title="Financeiro"),
                financial,
            ],
            scroll=ft.ScrollMode.HIDDEN,
            alignment=ft.MainAxisAlignment.START,
            spacing=0,
        ),
        bgcolor="#111418",
        # padding=ft.padding.all(20),
        padding=ft.padding.only(left=20, right=20, bottom=20),
    )
