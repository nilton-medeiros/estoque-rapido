# ==========================================
# src/domains/produtos/components/product_card.py
# ==========================================
import flet as ft
from src.domains.produtos.models import ProdutoStatus
from src.domains.produtos.models.produtos_model import Produto

class ProductCard:
    """Componente reutilizável para card de produto"""

    @staticmethod
    def create(produto: Produto, on_action_callback) -> ft.Card:
        """Cria um card individual do produto"""
        return ft.Card(
            content=ft.Container(
                padding=15,
                content=ft.Column([
                    ProductCard._create_card_header(produto, on_action_callback),
                    ft.Text(produto.name, weight=ft.FontWeight.BOLD,
                           theme_style=ft.TextThemeStyle.BODY_MEDIUM,
                           no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Text(f"{produto.description.replace(chr(10), ' ')}" if produto.description else '',  # chr(10) is newline "\n",
                           theme_style=ft.TextThemeStyle.BODY_SMALL,
                           no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Text(f"{produto.sale_price}",
                           theme_style=ft.TextThemeStyle.BODY_SMALL),
                    ProductCard._create_status_row(produto),
                ])
            ),
            margin=ft.margin.all(5),
            col={"xs": 12, "sm": 6, "md": 4, "lg": 3}
        )

    @staticmethod
    def _create_card_header(produto: Produto, on_action_callback) -> ft.Row:
        """Cria o cabeçalho do card com imagem e menu"""
        return ft.Row(
            [
                ProductCard._create_product_image(produto),
                ft.Text(produto.categoria_name, weight=ft.FontWeight.BOLD,
                    theme_style=ft.TextThemeStyle.BODY_LARGE),
                ft.Container(expand=True),  # Spacer
                ProductCard._create_action_menu(produto, on_action_callback),
            ],
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )

    @staticmethod
    def _create_product_image(produto: Produto) -> ft.Container:
        """Cria o container da imagem do produto"""
        image_content = (
            ft.Image(
                src=produto.image_url,
                fit=ft.ImageFit.COVER,
                width=100, height=100,
                border_radius=ft.border_radius.all(10),
                error_content=ft.Icon(ft.Icons.IMAGE_NOT_SUPPORTED_OUTLINED,
                                    size=30, color=ft.Colors.ERROR)
            ) if produto.image_url
            else ft.Icon(ft.Icons.CATEGORY_OUTLINED, size=40, opacity=0.5)
        )

        return ft.Container(
            width=100, height=100,
            border_radius=ft.border_radius.all(10),
            border=ft.border.all(1, ft.Colors.OUTLINE) if not produto.image_url else None,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            alignment=ft.alignment.center,
            content=image_content
        )

    @staticmethod
    def _create_action_menu(produto: Produto, on_action_callback) -> ft.Container:
        """Cria o menu de ações do produto"""
        return ft.Container(
            content=ft.PopupMenuButton(
                icon=ft.Icons.MORE_VERT,
                tooltip="Mais Ações",
                items=[
                    ft.PopupMenuItem(
                        text="Editar produto",
                        icon=ft.Icons.EDIT_NOTE_OUTLINED,
                        on_click=lambda e: on_action_callback("EDIT", produto)
                    ),
                    ft.PopupMenuItem(
                        text="Excluir produto",
                        icon=ft.Icons.DELETE_OUTLINE,
                        on_click=lambda e: on_action_callback("SOFT_DELETE", produto)
                    ),
                ],
            ),
        )

    @staticmethod
    def _create_status_row(produto: Produto) -> ft.Row:
        """Cria a linha com status e informações de estoque"""
        return ft.Row([
            ft.Text(
                value=produto.status.value,
                theme_style=ft.TextThemeStyle.BODY_SMALL,
                color=ft.Colors.GREEN if produto.status == ProdutoStatus.ACTIVE else ft.Colors.RED,
            ),
            ft.Text(
                value=f"Estoque min: {produto.minimum_stock_level}, max: {produto.maximum_stock_level}, atual: {produto.quantity_on_hand}",
                theme_style=ft.TextThemeStyle.BODY_SMALL,
                color=ProductCard._get_stock_color(produto),
            )
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    @staticmethod
    def _get_stock_color(produto: Produto) -> str:
        """Determina a cor baseada no nível de estoque"""
        try:
            current = int(produto.quantity_on_hand)
            minimum = int(produto.minimum_stock_level)
            maximum = int(produto.maximum_stock_level)

            if current < minimum:
                return ft.Colors.RED
            elif current == minimum:
                return ft.Colors.ORANGE
            elif current >= maximum:
                return ft.Colors.BLUE
            else:
                return ft.Colors.GREEN
        except ValueError:
            return ft.Colors.GREY
