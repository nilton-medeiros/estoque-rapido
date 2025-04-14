import flet as ft

from src.pages.partials.get_responsive_sizes import get_responsive_sizes


def build_input_field(page_width: int, col: dict = None, icon: str = None, **kwargs) -> ft.TextField:
    sizes = get_responsive_sizes(page_width)
    prefix = None
    if icon:
        # O container garante um padding entre o ícone e o input
        # O padding é aplicado apenas no lado direito
        prefix = ft.Container(
            content=ft.Icon(
                name=icon, color=ft.Colors.PRIMARY, size=sizes["icon_size"]),
            padding=ft.padding.only(right=10),
        )

    # Debug

    return ft.TextField(
        col=col,
        **kwargs,
        width=sizes["input_width"],
        text_size=sizes["font_size"],
        border_color=ft.Colors.PRIMARY,
        focused_border_color=ft.Colors.PRIMARY_CONTAINER,
        prefix=prefix,
        text_align=ft.TextAlign.LEFT,
        bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
        label_style=ft.TextStyle(
            color=ft.Colors.PRIMARY,          # Cor do label igual à borda
            weight=ft.FontWeight.W_500                  # Label um pouco mais grosso
        ),
        hint_style=ft.TextStyle(
            color=ft.Colors.GREY_500,          # Cor do placeholder mais visível
            weight=ft.FontWeight.W_300                  # Placeholder um pouco mais fino
        ),
        # Duração do fade do placeholder
        cursor_color=ft.Colors.PRIMARY,
        focused_color=ft.Colors.GREY_500,
        text_style=ft.TextStyle(                        # Estilo do texto digitado
            color=ft.Colors.WHITE,
            weight=ft.FontWeight.W_400
        ),
    )
