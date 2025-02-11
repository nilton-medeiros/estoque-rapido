import flet as ft
from datetime import datetime
from src.domain.models.cnpj import CNPJ
from src.domain.models.phone_number import PhoneNumber
from src.domain.models.company_size import CompanySize


class CompanyForm(ft.Container):
    def __init__(self, company_data: dict = None):
        super().__init__()
        self.bgcolor = "#111418"
        self.width = 1500
        self.height = 850
        self.company_data = company_data
        self.padding = 20
        self.scroll = ft.ScrollMode.ALWAYS
        self._create_form_fields()

        self.content = ft.Column(
            [
                ft.Text("Dados da Empresa", size=20, weight=ft.FontWeight.BOLD),
                ft.Row([self.doc], wrap=True),
                ft.Row([self.name, self.corporate_name], wrap=True),
                ft.Row([self.phone, self.ie, self.im], wrap=True),

                ft.Divider(),
                ft.Text("Endereço", size=20, weight=ft.FontWeight.BOLD),
                ft.Row([self.street, self.number], wrap=True),
                ft.Row([self.complement, self.neighborhood], wrap=True),
                ft.Row([self.city, self.state, self.postal_code], wrap=True),

                ft.Divider(),
                ft.Text("Informações Adicionais", size=20,
                        weight=ft.FontWeight.BOLD),
                ft.Row([self.size, self.crt], wrap=True),
            ],
            scroll=ft.ScrollMode.AUTO,
        )

    def _create_form_fields(self):
        """Cria todos os campos do formulário"""

        # Informações Básicas
        self.name = ft.TextField(
            label="Nome Fantasia",
            border=ft.InputBorder.UNDERLINE,
            width=400,
        )
        self.corporate_name = ft.TextField(
            label="Razão Social",
            border=ft.InputBorder.UNDERLINE,
            width=400,
        )
        self.doc = ft.TextField(
            label="CNPJ/CPF",
            keyboard_type=ft.KeyboardType.NUMBER,
            border=ft.InputBorder.UNDERLINE,
            width=200,
        )
        self.ie = ft.TextField(
            label="Inscrição Estadual",
            border=ft.InputBorder.UNDERLINE,
            width=200,
        )
        self.im = ft.TextField(
            label="Inscrição Municipal",
            border=ft.InputBorder.UNDERLINE,
            width=200,
        )
        # Informações de Contato
        self.email = ft.TextField(
            label="Email",
            keyboard_type=ft.KeyboardType.EMAIL,
            border=ft.InputBorder.UNDERLINE,
            width=400,
        )
        self.phone = ft.TextField(
            label="Telefone",
            border=ft.InputBorder.UNDERLINE,
            width=200,
            hint_text="+55(11)99999-9999"
        )
        self.website = ft.TextField(
            label="Website",
            border=ft.InputBorder.UNDERLINE,
            width=400,
        )

        # Endereço
        self.street = ft.TextField(
            label="Rua",
            border=ft.InputBorder.UNDERLINE,
            width=300,
        )
        self.number = ft.TextField(
            label="Número",
            border=ft.InputBorder.UNDERLINE,
            width=100,
        )
        self.complement = ft.TextField(
            label="Complemento",
            border=ft.InputBorder.UNDERLINE,
            width=200,
        )
        self.neighborhood = ft.TextField(
            label="Bairro",
            border=ft.InputBorder.UNDERLINE,
            width=200,
        )
        self.city = ft.TextField(
            label="Cidade",
            border=ft.InputBorder.UNDERLINE,
            width=200,
        )
        self.state = ft.TextField(
            label="Estado",
            border=ft.InputBorder.UNDERLINE,
            width=100,
        )
        self.postal_code = ft.TextField(
            label="CEP",
            border=ft.InputBorder.UNDERLINE,
            width=150,
        )

        # Porte da Empresa
        self.size = ft.Dropdown(
            label="Porte da Empresa",
            width=200,
            options=[
                ft.dropdown.Option(key=size.name, text=size.value)
                for size in CompanySize
            ],
        )

        # Dados Fiscais
        self.crt = ft.Dropdown(
            label="Regime Tributário",
            width=300,
            options=[
                ft.dropdown.Option("1", "Simples Nacional"),
                ft.dropdown.Option("2", "Simples Nacional - Excesso sublimite"),
                ft.dropdown.Option("3", "Regime Normal"),
                ft.dropdown.Option("4", "Simples Nacional - MEI"),
            ],
        )

    def did_mount(self):
        """Chamado quando o controle é montado"""
        self.populate_form() if self.company_data else self.clear_form()
        self.update()

    def before_update(self):
        """Atualiza o conteúdo do container antes de renderizar"""
        print("Debug | before_update foi chamado")
        self.content = ft.Column([
            ft.Text("Dados da Empresa", size=20, weight=ft.FontWeight.BOLD),
            ft.Row([self.name, self.corporate_name], wrap=True),
            ft.Row([self.cnpj, self.phone], wrap=True),
            ft.Row([self.ie, self.im], wrap=True),

            ft.Divider(),
            ft.Text("Endereço", size=20, weight=ft.FontWeight.BOLD),
            ft.Row([self.street, self.number], wrap=True),
            ft.Row([self.complement, self.neighborhood], wrap=True),
            ft.Row([self.city, self.state, self.postal_code], wrap=True),

            ft.Divider(),
            ft.Text("Informações Adicionais", size=20,
                    weight=ft.FontWeight.BOLD),
            ft.Row([self.size, self.crt], wrap=True),
        ], scroll=ft.ScrollMode.AUTO)
        print(f"Debug | Content definido: {self.content}")

    def clear_form(self):
        """Limpa todos os campos do formulário"""
        for field in self.__dict__.values():
            if isinstance(field, (ft.TextField, ft.Dropdown)):
                field.value = None
                if hasattr(field, 'error_text'):
                    field.error_text = None

    def populate_form(self):
        """Preenche o formulário com os dados existentes da empresa"""
        # Informações Básicas
        self.name.value = self.company_data.get('name', '')
        self.corporate_name.value = self.company_data.get('corporate_name', '')
        self.cnpj.value = str(self.company_data.get('cnpj', ''))
        self.phone.value = str(self.company_data.get('phone', ''))
        self.ie.value = self.company_data.get('ie', '')
        self.im.value = self.company_data.get('im', '')

        # Endereço
        if address := self.company_data.get('address'):
            self.street.value = address.get('street', '')
            self.number.value = address.get('number', '')
            self.complement.value = address.get('complement', '')
            self.neighborhood.value = address.get('neighborhood', '')
            self.city.value = address.get('city', '')
            self.state.value = address.get('state', '')
            self.postal_code.value = address.get('postal_code', '')

        # Informações Adicionais
        if size := self.company_data.get('size'):
            self.size.value = size.name

        if fiscal := self.company_data.get('fiscal'):
            self.crt.value = str(fiscal.get('crt', '3'))

    def get_form_data(self) -> dict:
        """Obtém os dados do formulário como um dicionário"""
        try:
            # Analisa e valida os dados
            cnpj_obj = CNPJ(self.cnpj.value)
            phone_obj = PhoneNumber(
                self.phone.value) if self.phone.value else None

            return {
                "name": self.name.value,
                "corporate_name": self.corporate_name.value,
                "cnpj": cnpj_obj,
                "ie": self.ie.value,
                "im": self.im.value,
                "address": {
                    "street": self.street.value,
                    "number": self.number.value,
                    "complement": self.complement.value,
                    "neighborhood": self.neighborhood.value,
                    "city": self.city.value,
                    "state": self.state.value,
                    "postal_code": self.postal_code.value
                },
                "size": CompanySize[self.size.value] if self.size.value else None,
                "fiscal": {
                    "crt": int(self.crt.value) if self.crt.value else 3
                }
            }
        except ValueError as e:
            raise ValueError(f"Erro ao validar dados do formulário: {str(e)}")
