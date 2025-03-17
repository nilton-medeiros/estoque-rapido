import flet as ft


def empresas_form(page: ft.Page, empresa: dict):
    pass

    return


def criar_overlay_edicao(self, contrato):
    def get_safe_value(key, default=""):
        return str(contrato.get(key, default))

    def format_money(val):
        try:
            return locale.currency(float(val), grouping=True, symbol=False)
        except:
            return "0,00"

    self.nome_cliente_field = ft.TextField(
        label="Nome", value=contrato.get('nome_cliente', ''), read_only=True)
    self.numero_contato_field = ft.TextField(
        label="Número", value=contrato.get('numero_contato', ''), read_only=True)

    self.valor_contrato_field = ft.TextField(
        label="Valor do Contrato",
        prefix_text="R$ ",
        value=format_money(contrato.get('valor_contrato', 0)),
        on_change=self.calcular_edicao
    )

    self.juros_field = ft.TextField(
        label="Juros (%)",
        value=str(contrato.get('juros', '0')),
        on_change=self.calcular_edicao
    )

    self.qtd_parcelas_field = ft.TextField(
        label="Qtd. Parcelas",
        value=str(contrato.get('qtd_parcelas', '0')),
        on_change=self.calcular_edicao
    )

    self.tipo_parcela = ft.Dropdown(
        label="Tipo Parcela",
        options=[
            ft.dropdown.Option("Semanal"),
            ft.dropdown.Option("Quinzenal"),
            ft.dropdown.Option("Mensal")
        ],
        value=contrato.get('tipo_parcela', 'Mensal'),
        on_change=self.atualizar_data_vencimento_edicao
    )

    self.diaria_field = ft.TextField(
        label="Valor Diária",
        value=format_money(contrato.get('diaria_valor', 0)),
        on_change=self.calcular_edicao
    )

    self.valor_parcela_field = ft.TextField(
        label="Valor Parcela",
        prefix_text="R$ ",
        value=format_money(contrato.get('valor_parcela', 0)),
        read_only=True
    )

    self.valor_total_field = ft.TextField(
        label="Valor Total",
        prefix_text="R$ ",
        value=format_money(contrato.get('valor_total', 0)),
        read_only=True
    )

    self.lucro_field = ft.TextField(
        label="Lucro",
        prefix_text="R$ ",
        value=format_money(contrato.get('lucro', 0)),
        read_only=True
    )

    if contrato['tipo_contrato'] == 'Venda':
        self.item_a_venda_field = ft.TextField(
            label="Item Vendido",
            value=contrato.get('item_a_venda', '')
        )
        self.valor_compra_field = ft.TextField(
            label="Custo do Item",
            prefix_text="R$ ",
            value=format_money(contrato.get('valor_compra', 0)),
            on_change=self.calcular_edicao
        )
        self.entrada_field = ft.TextField(
            label="Entrada",
            prefix_text="R$ ",
            value=format_money(contrato.get('entrada', 0)),
            on_change=self.calcular_edicao
        )

    controls = [
        ft.Row([self.nome_cliente_field, self.numero_contato_field]),
        ft.Row([self.valor_contrato_field, self.juros_field]),
        ft.Row([self.qtd_parcelas_field, self.tipo_parcela]),
        ft.Row([self.diaria_field, self.valor_parcela_field]),
        ft.Row([self.valor_total_field, self.lucro_field])
    ]

    if contrato['tipo_contrato'] == 'Venda':
        controls.insert(3, ft.Row([self.item_a_venda_field]))
        controls.insert(
            4, ft.Row([self.valor_compra_field, self.entrada_field]))

    btn_salvar = ft.TextButton("Salvar", on_click=self.salvar_edicao)
    btn_cancelar = ft.TextButton("Cancelar", on_click=lambda e: (
        self.page.overlay.clear(), self.page.update()))


overlay = ft.Container(
    content=ft.Container(
        content=ft.Column([
            ft.Text("Editar Contrato", size=20, weight="bold"),
            *controls,
            ft.Row([btn_cancelar, btn_salvar], alignment="end")
        ], spacing=15, scroll=ft.ScrollMode.AUTO),
        width=700,  # Largura fixa para evitar ocupar a tela toda
        padding=20,
        bgcolor=ft.Colors.WHITE,
        border_radius=10
    ),
    alignment=ft.alignment.center,
    bgcolor=ft.Colors.with_opacity(0.5, ft.Colors.BLACK)
)

return overlay
