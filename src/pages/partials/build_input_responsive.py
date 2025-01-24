import flet as ft


def build_input_field(sizes: dict, label: str, icon: str, hint_text: str = None, password: bool = False) -> ft.TextField:
    return ft.TextField(
        label=label,
        hint_text=hint_text,
        width=sizes["input_width"],
        text_size=sizes["font_size"],
        password=password,
        can_reveal_password=password,
        border_color=ft.Colors.YELLOW_ACCENT_400,
        focused_border_color=ft.Colors.YELLOW_ACCENT,
        prefix=ft.Icon(
            name=icon,
            color=ft.Colors.YELLOW_ACCENT_400,
            size=sizes["icon_size"]
        ),
        text_align=ft.TextAlign.LEFT,
        bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
        label_style=ft.TextStyle(
            color=ft.Colors.YELLOW_ACCENT_400,          # Cor do label igual à borda
            weight=ft.FontWeight.W_500                  # Label um pouco mais grosso
        ),
        hint_style=ft.TextStyle(
            color=ft.Colors.YELLOW_ACCENT_200,          # Cor do placeholder mais visível
            weight=ft.FontWeight.W_300                  # Placeholder um pouco mais fino
        ),
        cursor_color=ft.Colors.YELLOW_ACCENT_400,
        focused_color=ft.Colors.YELLOW_ACCENT,
        text_style=ft.TextStyle(                        # Estilo do texto digitado
            color=ft.Colors.WHITE,
            weight=ft.FontWeight.W_400
        )
    )
