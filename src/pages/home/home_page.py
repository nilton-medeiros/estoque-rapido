import flet as ft

from src.pages.home.sidebar import sidebar_container
from src.pages.home.content import main_content

# Thema da aplicação que começa em home


class AppTheme:
    theme = ft.Theme(
        color_scheme=ft.ColorScheme(
            background='#111418',
            on_background='#2d2d3a',
            on_inverse_surface='#2d2d3a',
            primary=ft.Colors.INDIGO,
        ),
        text_theme=ft.TextTheme(
            body_large=ft.TextStyle(
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.WHITE,
                size=14,
            ),
            body_medium=ft.TextStyle(
                weight=ft.FontWeight.NORMAL,
                color=ft.Colors.GREY,
                size=14,
            ),
            headline_large=ft.TextStyle(
                weight=ft.FontWeight.W_900,
                color=ft.Colors.WHITE,
                size=50,
            ),
            label_large=ft.TextStyle(
                weight=ft.FontWeight.W_700,
                color=ft.Colors.WHITE,
                size=16,
            ),
            headline_medium=ft.TextStyle(
                weight=ft.FontWeight.W_700,
                color=ft.Colors.WHITE,
                size=30,
            )
        ),
        scrollbar_theme=ft.ScrollbarTheme(
            track_visibility=False,
            thumb_visibility=False,
            track_color={
                ft.ControlState.DEFAULT: ft.Colors.TRANSPARENT,
            },
            thumb_color={
                ft.ControlState.HOVERED: ft.Colors.TRANSPARENT,
                ft.ControlState.DEFAULT: ft.Colors.TRANSPARENT,
            }
        )
    )


def home_page(page: ft.Page):
    """Página Home do usuário logado"""
    page.theme = AppTheme.theme
    page.bgcolor = ft.Colors.BLACK

    sidebar = sidebar_container(page)
    content = main_content()

    layout = ft.ResponsiveRow(
        columns=12,
        controls=[
            ft.Container(
                content=sidebar,
                col={"xs": 12, "md": 3, "lg": 3, "xxl": 3},
            ),
            ft.Container(
                content=content,
                col={"xs": 12, "md": 9, "lg": 9, "xxl": 9},
            ),
        ],
    )

    return ft.Container(
        content=layout,
        bgcolor=ft.Colors.BLACK,
        expand=True,
    )