from decimal import Decimal, ROUND_HALF_UP # Importe ROUND_HALF_UP
import flet as ft

from .responsive_sizes import get_responsive_sizes


class MonetaryTextField:
    def __init__(self, page_width: int | float, app_colors: dict[str, str], label: str = "Valor (R$)", prefix_text: str = "R$ ", col: None | dict = None):
        """
         Inicializa o campo de entrada monetária com formatação automática.

         Args:
             label (str): Rótulo do campo de entrada. Padrão é "Valor (R$)".
             col (int | dict[str, int]) ResponsiveNumber: Número de colunas para o campo de entrada.
         """
        self.updating = False  # Flag para evitar loops infinitos
        self.prefix_text = prefix_text

        sizes = get_responsive_sizes(page_width)

        # TextField principal
        self.text_field = ft.TextField(
            label=label,
            value="0,00",
            text_align=ft.TextAlign.RIGHT,
            text_size=sizes["font_size"],
            border_color=app_colors["primary"],
            focused_border_color=app_colors["container"],
            bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
            label_style=ft.TextStyle(
                color=app_colors["primary"], # type: ignore # Cor do label igual à borda
                weight=ft.FontWeight.W_500 # Label um pouco mais grosso
            ),
            hint_style=ft.TextStyle(
                color=ft.Colors.GREY_500, # type: ignore # Cor do placeholder mais visível
                weight=ft.FontWeight.W_300 # Placeholder um pouco mais fino
            ),
            # Duração do fade do placeholder
            cursor_color=app_colors["primary"],
            focused_color=ft.Colors.GREY_500,
            text_style=ft.TextStyle(                        # Estilo do texto digitado
                color=ft.Colors.WHITE,
                weight=ft.FontWeight.W_400
            ),
            on_change=self.on_monetary_change,
            keyboard_type=ft.KeyboardType.NUMBER,
            prefix_text=self.prefix_text,
            col=col,
            width=sizes["input_width"],
        )

    def format_monetary_value(self, raw_value) -> str:
        """
        Formata o valor monetário seguindo a lógica:
        - Remove tudo que não é dígito
        - Adiciona zeros à esquerda se necessário
        - Insere a vírgula nas duas últimas posições
        """
        # Remove tudo exceto dígitos
        # digits_only = re.sub(r'\D', '', raw_value)
        digits_only = ''.join(filter(str.isdigit, raw_value))

        # Se não há dígitos, retorna 0,00
        if not digits_only:
            return "0,00"

        # Garante pelo menos 3 dígitos (para ter centavos)
        digits_only = digits_only.zfill(3)

        # Separa reais e centavos
        centavos = digits_only[-2:]
        reais = digits_only[:-2]

        # Remove zeros à esquerda dos reais (mas mantém pelo menos um)
        reais = reais.lstrip('0') or '0'

        # Adiciona pontos para milhares nos reais se necessário
        if len(reais) > 3:
            # Converte para int, formata com pontos e volta para string
            reais_int = int(reais)
            reais = f"{reais_int:,}".replace(',', '.')

        return f"{reais},{centavos}"

    def on_monetary_change(self, e) -> None:
        """Evento chamado quando o usuário digita no campo"""
        if self.updating:
            return

        self.updating = True

        # Pega o valor atual e formata
        current_value = e.control.value or ""
        formatted_value = self.format_monetary_value(current_value)

        # Atualiza o campo com o valor formatado
        e.control.value = formatted_value

        # Move o cursor para o final
        e.control.selection = ft.TextSelection(
            base_offset=len(formatted_value),
            extent_offset=len(formatted_value)
        )

        self.updating = False
        self.text_field.update()

    def get_numeric_value(self) -> Decimal:
        """Retorna o valor numérico (Decimal) do campo"""
        value_str: str = self.text_field.value.replace('.', '').replace(',', '.')   # type: ignore [attr-defined]
        try:
            return Decimal(value_str)
        except ValueError:
            return Decimal(0.0)

    def get_value_as_int(self) -> int:
        """Retorna o valor numérico (int) do campo"""
        value_str: str = self.text_field.value.replace('.', '').replace(',', '.')   # type: ignore [attr-defined]
        try:
            return int(Decimal(value_str) * 100)
        except ValueError:
            return 0

    def set(self, value: Decimal | float | int, prefix_text: str = "R$ "): # Aceita Decimal, float ou int
        """Define o valor do campo"""
        self.prefix_text = prefix_text

        # Garante que o valor seja Decimal antes de quantizar
        if isinstance(value, float):
            value = Decimal(str(value)) # Converte float para Decimal através de string para precisão
        elif isinstance(value, int):
            value = Decimal(value) # Converte int para Decimal

        # Arredonda para duas casas decimais
        # ROUND_HALF_UP arredonda para o vizinho mais próximo, com empates arredondados para longe de zero.
        quantizer = Decimal("0.01")
        # Agora 'value' é garantidamente um Decimal, então Pylance não deve reclamar.
        rounded_value = value.quantize(quantizer, rounding=ROUND_HALF_UP)
        self.text_field.value = str(rounded_value).replace('.', ',')
