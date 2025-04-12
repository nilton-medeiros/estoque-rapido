import flet as ft

# Thema da aplicação. Inicia em home
class AppTheme:
    theme = ft.Theme(
        color_scheme=ft.ColorScheme(
            background='#111418',
            on_background='#2d2d3a',
            on_inverse_surface='#2d2d3a',
            primary=ft.Colors.BLUE,
            primary_container=ft.Colors.BLUE_200,
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
                ft.ControlState.DEFAULT: ft.Colors.WHITE10,
            },
            thumb_color={
                ft.ControlState.HOVERED: ft.Colors.WHITE10,
                ft.ControlState.DEFAULT: ft.Colors.WHITE10,
            }
        )
    )
