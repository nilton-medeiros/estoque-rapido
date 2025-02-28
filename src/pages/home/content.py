import flet as ft

import datetime
import locale

locale.setlocale(locale.LC_TIME, 'pt_BR.utf8')

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
                            weight=ft.FontWeight.BOLD,
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
            height=250,
        )

    date_description = datetime.datetime.now().strftime("%d de %B")

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

    banner = ft.Container(
        shadow=ft.BoxShadow(
            color='#2d2d3a',
            offset=ft.Offset(x=0, y=-60),
            spread_radius=-30,
        ),
        image=ft.Image(src='images/bg.jpg', fit=ft.ImageFit.COVER, repeat=ft.ImageRepeat.NO_REPEAT, opacity=0.5),
        bgcolor='#111418',
        margin=ft.margin.only(top=30),
        content=ft.ResponsiveRow(
            columns=12,
            vertical_alignment=ft.CrossAxisAlignment.END,
            controls=[
                ft.Container(
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
                                            color=ft.Colors.PRIMARY,
                                            weight=ft.FontWeight.W_900,
                                            size=20,
                                        )
                                    ),
                                    ft.Container(
                                        content=ft.Text(
                                            ".",
                                            style=ft.TextStyle(
                                                color=ft.Colors.PRIMARY,
                                                weight=ft.FontWeight.W_900,
                                                size=40,  # O tamanho maior do ponto
                                            )
                                        ),
                                        offset=ft.transform.Offset(0, -0.2),
                                    ),
                                    ft.Text(
                                        date_description,
                                        style=ft.TextStyle(
                                            color=ft.Colors.WHITE,
                                            size=18,
                                        )
                                    ),
                                ],
                            ),
                        ],
                        spacing=30,
                        alignment=ft.MainAxisAlignment.CENTER,
                    )
                ),
                ft.Container(
                    col={'md': 12, 'lg': 4},
                    content=ft.Image(
                        src='images/face-2.png',
                        width=20,
                        # scale=ft.Scale(scale=1.8, alignment=ft.alignment.bottom_center),
                    )
                )
            ]
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
        # padding=ft.padding.all(20),
    )

    def on_click_registrar(e):
        print(e.control)

    def on_click_status(e):
        print(e.control)

    def on_click_nfce(e):
        print(e.control)

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
            spacing=30,
            run_spacing=30,
        ),
        col={"xs": 12, "md": 7, "lg": 8, "xxl": 9},
        expand=True,
        bgcolor="#111418",
        border_radius=10,
        alignment=ft.alignment.center,
        margin=ft.margin.symmetric(vertical=40),
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
            padding=ft.padding.symmetric(vertical=20),
            content=ft.Text(value=title, theme_style=ft.TextThemeStyle.HEADLINE_MEDIUM),
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
        ),
        bgcolor="#111418",
        padding=ft.padding.all(30),
    )
