from decimal import Decimal
import flet as ft


class MonetaryTextField:
    def __init__(self, page):
        self.page = page
        self.updating = False  # Flag para evitar loops infinitos

        # TextField principal
        self.text_field = ft.TextField(
            label="Valor (R$)",
            value="0,00",
            text_align=ft.TextAlign.RIGHT,
            on_change=self.on_monetary_change,
            keyboard_type=ft.KeyboardType.NUMBER,
            prefix_text="R$ ",
            width=200
        )

    def format_monetary_value(self, raw_value):
        """
        Formata o valor monetário seguindo a lógica:
        - Remove tudo que não é dígito
        - Adiciona zeros à esquerda se necessário
        - Insere a vírgula nas duas últimas posições
        """
        # Remove tudo exceto dígitos
        # digits_only = re.sub(r'\D', '', raw_value)
        digits_only =''.join(filter(str.isdigit, raw_value))

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

    def on_monetary_change(self, e):
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
        # self.page.update()
        self.text_field.update()


    def get_numeric_value(self):
        """Retorna o valor numérico (Decimal) do campo"""
        value_str = self.text_field.value if self.text_field.value else "0,00"
        value_str = value_str.replace('.', '').replace(',', '.')
        try:
            return Decimal(value_str)
        except ValueError:
            return 0.0


def main(page: ft.Page):
    page.title = "Campo Monetário - Flet"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window.width = 400
    page.window.height = 300

    # Instancia o campo monetário
    monetary_field = MonetaryTextField(page)

    # Função para mostrar o valor numérico
    def show_value(e):
        numeric_value = monetary_field.get_numeric_value()
        result_text.value = f"Valor numérico: {numeric_value}"
        # page.update()
        result_text.update()

    # Componentes da interface
    result_text = ft.Text("Valor numérico: 0.0")
    show_button = ft.ElevatedButton("Mostrar Valor", on_click=show_value)

    # Layout da página
    page.add(
        ft.Column([
            ft.Text("Digite um valor monetário:",
                    size=16, weight=ft.FontWeight.BOLD),
            ft.Text("Os números são inseridos da direita para a esquerda",
                    size=12, color=ft.colors.GREY_600),
            monetary_field.text_field,
            ft.Divider(),
            result_text,
            show_button,
        ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )


if __name__ == "__main__":
    ft.app(target=main)
