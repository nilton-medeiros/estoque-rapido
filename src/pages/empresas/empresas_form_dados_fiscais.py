

        # Porte da Empresa
        self.size = ft.Dropdown(
            label="Porte da Empresa",
            width=400,
            options=[
                ft.dropdown.Option(key=size.name, text=size.value)
                for size in EmpresaSize
            ],
        )

        # Dados Fiscais
        self.crt = ft.Dropdown(
            label="Regime Tributário",
            width=400,
            options=[
                ft.dropdown.Option(key=regime.name,  text=regime.value[1])
                for regime in CodigoRegimeTributario
            ],
        )
        self.nfce_series = ft.TextField(
            label="Série NFC-e",
            keyboard_type=ft.KeyboardType.NUMBER,
            width=100,
        )
        self.nfce_number = ft.TextField(
            label="Número NFC-e",
            hint_text="Próximo número a ser emitido",
            hint_style=ft.TextStyle(
                color=ft.Colors.WHITE30,          # Cor do placeholder mais visível
                weight=ft.FontWeight.W_100        # Placeholder um pouco mais fino
            ),
            keyboard_type=ft.KeyboardType.NUMBER,
            width=300,
        )
        # Tipo de Ambiente
        self.nfce_environment = ft.Dropdown(
            label="Ambiente",
            hint_text="Ambiente de emissão da NFC-e (Homologação ou Produção)",
            width=200,
            value=Environment.HOMOLOGACAO,  # Default value
            options=[
                ft.dropdown.Option(key=ambiente.name, text=ambiente.value)
                for ambiente in Environment
            ],
        )
        # Credenciais Sefaz concedido ao emissor de NFCe
        self.nfce_sefaz_id_csc = ft.TextField(
            label="Identificação do CSC",
            hint_text="Id. Código Segurança do Contribuínte",
            hint_style=ft.TextStyle(
                color=ft.Colors.WHITE30,          # Cor do placeholder mais visível
                weight=ft.FontWeight.W_100        # Placeholder um pouco mais fino
            ),
            keyboard_type=ft.KeyboardType.NUMBER,
            width=400,
        )
        self.nfce_sefaz_csc = ft.TextField(
            label="Código do CSC",
            hint_text="Código Segurança do Contribuínte",
            hint_style=ft.TextStyle(
                color=ft.Colors.WHITE30,          # Cor do placeholder mais visível
                weight=ft.FontWeight.W_100        # Placeholder um pouco mais fino
            ),
            width=400,
        )
