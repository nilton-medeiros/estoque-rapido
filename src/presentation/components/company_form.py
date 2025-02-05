import flet as ft
from datetime import datetime
from src.domain.models.cnpj import CNPJ
from src.domain.models.phone_number import PhoneNumber
from src.domain.models.company_size import CompanySize


class CompanyForm(ft.Container):
    def __init__(self, company_data: dict = None):
        super().__init__()
        self.bgcolor = "blue"
        self.width = 500
        self.height = 500
        self.company_data = company_data
        self.padding = 20
        self._create_form_fields()

        self.content = ft.Column([
            ft.Text("Dados da Empresa", size=20, weight=ft.FontWeight.BOLD),
            ft.Row([self.name, self.corporate_name], wrap=True),
            ft.Row([self.cnpj, self.state_registration,
                   self.municipal_registration], wrap=True),
            ft.Row([self.legal_nature, self.founding_date], wrap=True),

            ft.Divider(),
            ft.Text("Contato", size=20, weight=ft.FontWeight.BOLD),
            ft.Row([self.email, self.website], wrap=True),
            ft.Row([self.phone1, self.phone2], wrap=True),

            ft.Divider(),
            ft.Text("Endereço", size=20, weight=ft.FontWeight.BOLD),
            ft.Row([self.street, self.number], wrap=True),
            ft.Row([self.complement, self.neighborhood], wrap=True),
            ft.Row([self.city, self.state, self.postal_code], wrap=True),

            ft.Divider(),
            ft.Text("Informações Adicionais", size=20,
                    weight=ft.FontWeight.BOLD),
            ft.Row([self.size, self.tax_regime], wrap=True),
        ], scroll=ft.ScrollMode.AUTO)

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
        self.cnpj = ft.TextField(
            label="CNPJ",
            border=ft.InputBorder.UNDERLINE,
            width=200,
        )
        self.state_registration = ft.TextField(
            label="Inscrição Estadual",
            border=ft.InputBorder.UNDERLINE,
            width=200,
        )
        self.legal_nature = ft.TextField(
            label="Natureza Jurídica",
            border=ft.InputBorder.UNDERLINE,
            width=400,
        )
        self.municipal_registration = ft.TextField(
            label="Inscrição Municipal",
            border=ft.InputBorder.UNDERLINE,
            width=200,
        )
        self.founding_date = ft.TextField(
            label="Data de Fundação",
            border=ft.InputBorder.UNDERLINE,
            width=200,
            hint_text="DD/MM/AAAA"
        )

        # Informações de Contato
        self.email = ft.TextField(
            label="Email",
            border=ft.InputBorder.UNDERLINE,
            width=400,
        )
        self.phone1 = ft.TextField(
            label="Telefone 1",
            border=ft.InputBorder.UNDERLINE,
            width=200,
            hint_text="+55(11)99999-9999"
        )
        self.phone2 = ft.TextField(
            label="Telefone 2",
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
        self.tax_regime = ft.Dropdown(
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
            ft.Row([self.cnpj, self.state_registration,
                   self.municipal_registration], wrap=True),
            ft.Row([self.legal_nature, self.founding_date], wrap=True),

            ft.Divider(),
            ft.Text("Contato", size=20, weight=ft.FontWeight.BOLD),
            ft.Row([self.email, self.website], wrap=True),
            ft.Row([self.phone1, self.phone2], wrap=True),

            ft.Divider(),
            ft.Text("Endereço", size=20, weight=ft.FontWeight.BOLD),
            ft.Row([self.street, self.number], wrap=True),
            ft.Row([self.complement, self.neighborhood], wrap=True),
            ft.Row([self.city, self.state, self.postal_code], wrap=True),

            ft.Divider(),
            ft.Text("Informações Adicionais", size=20,
                    weight=ft.FontWeight.BOLD),
            ft.Row([self.size, self.tax_regime], wrap=True),
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
        self.state_registration.value = self.company_data.get(
            'state_registration', '')
        self.legal_nature.value = self.company_data.get('legal_nature', '')
        self.municipal_registration.value = self.company_data.get(
            'municipal_registration', '')

        # Formata a data de fundação se existir
        if founding_date := self.company_data.get('founding_date'):
            self.founding_date.value = founding_date.strftime('%d/%m/%Y')

        # Informações de Contato
        if contact := self.company_data.get('contact'):
            self.email.value = contact.get('email', '')
            self.phone1.value = str(contact.get('phone1', ''))
            self.phone2.value = str(contact.get('phone2', ''))
            self.website.value = contact.get('website', '')

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
            self.tax_regime.value = str(fiscal.get('tax_regime', '3'))

    def get_form_data(self) -> dict:
        """Obtém os dados do formulário como um dicionário"""
        try:
            # Analisa e valida os dados
            cnpj_obj = CNPJ(self.cnpj.value)
            phone1_obj = PhoneNumber(
                self.phone1.value) if self.phone1.value else None
            phone2_obj = PhoneNumber(
                self.phone2.value) if self.phone2.value else None

            # Analisa a data de fundação
            founding_date = None
            if self.founding_date.value:
                founding_date = datetime.strptime(
                    self.founding_date.value, '%d/%m/%Y'
                ).date()

            return {
                "name": self.name.value,
                "corporate_name": self.corporate_name.value,
                "cnpj": cnpj_obj,
                "state_registration": self.state_registration.value,
                "legal_nature": self.legal_nature.value,
                "municipal_registration": self.municipal_registration.value,
                "founding_date": founding_date,
                "contact": {
                    "email": self.email.value,
                    "phone1": phone1_obj,
                    "phone2": phone2_obj,
                    "website": self.website.value
                },
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
                    "tax_regime": int(self.tax_regime.value) if self.tax_regime.value else 3
                }
            }
        except ValueError as e:
            raise ValueError(f"Erro ao validar dados do formulário: {str(e)}")
