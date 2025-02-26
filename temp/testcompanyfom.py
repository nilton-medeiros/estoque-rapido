import flet as ft
from src.domain.models.cnpj import CNPJ
from src.domain.models.cpf import CPF
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
        
        # Bind the dropdown change event
        self.tipo_doc.on_change = self._handle_doc_type_change
        
        self.content = ft.Column(
            [
                ft.Text("Dados da Empresa", size=20, weight=ft.FontWeight.BOLD),
                ft.Row([self.tipo_doc], wrap=True),
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
        
        # Tipo de Documento
        self.tipo_doc = ft.Dropdown(
            label="Tipo de Documento",
            width=200,
            value="CNPJ",  # Default value
            options=[
                ft.dropdown.Option("CNPJ"),
                ft.dropdown.Option("CPF"),
            ],
        )

        # Campos de nome com labels iniciais (CNPJ por padrão)
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
        

    def _handle_doc_type_change(self, e):
        """Atualiza os labels e visibilidade dos campos baseado no tipo de documento"""
        if self.tipo_doc.value == "CPF":
            # Atualiza labels para pessoa física
            self.name.label = "Nome/Apelido"
            self.corporate_name.label = "Nome Completo"
            # Oculta campos específicos de empresa
            self.ie.visible = False
            self.im.visible = False
        else:  # CNPJ
            # Atualiza labels para pessoa jurídica
            self.name.label = "Nome Fantasia"
            self.corporate_name.label = "Razão Social"
            # Mostra campos específicos de empresa
            self.ie.visible = True
            self.im.visible = True
        
        # Atualiza a UI
        self.update()

    def did_mount(self):
        """Chamado quando o controle é montado"""
        if self.company_data:
            self.populate_form()
        else:
            self.clear_form()
        # Configura o estado inicial dos campos baseado no tipo de documento padrão
        self._handle_doc_type_change(None)
        self.update()

    def populate_form(self):
        """Preenche o formulário com os dados existentes"""
        # Define o tipo de documento baseado nos dados
        self.tipo_doc.value = "CPF" if self.company_data.get('cpf') else "CNPJ"
        
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

        # Atualiza os labels e visibilidade após popular
        self._handle_doc_type_change(None)

    def get_form_data(self) -> dict:
        """Obtém os dados do formulário como um dicionário"""
        try:
            # Base do dicionário
            form_data = {
                "name": self.name.value,
                "corporate_name": self.corporate_name.value,
                "phone": PhoneNumber(self.phone.value) if self.phone.value else None,
            }
            
            # Adiciona campos específicos baseado no tipo de documento
            if self.tipo_doc.value == "CNPJ":
                form_data.update({
                    "cnpj": CNPJ(self.cnpj.value),
                    "ie": self.ie.value,
                    "im": self.im.value,
                })
            else:  # CPF
                form_data["cpf"] = self.cnpj.value  # Assumindo que você tem validação de CPF
            
            crt = self.crt.value

            if not crt:
                # Padrão
                if self.tipo_doc.value == "CNPJ":
                    crt = 3  # Regime Normal
                else:
                    crt = 1  # Simples Nacional
            
            # Adiciona endereço e outros campos comuns
            form_data.update({
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
                    "crt": crt
                }
            })
            
            return form_data
            
        except ValueError as e:
            raise ValueError(f"Erro ao validar dados do formulário: {str(e)}")


    def before_update(self):
        """Atualiza o conteúdo do container antes de renderizar"""
        # Cria uma lista de campos que sempre aparecem
        base_fields = [
            ft.Text("Dados da Empresa", size=20, weight=ft.FontWeight.BOLD),
            ft.Row([self.tipo_doc], wrap=True),
            ft.Row([self.name, self.corporate_name], wrap=True),
            ft.Row([self.phone], wrap=True),  # Phone sempre visível
        ]
        
        # Adiciona campos específicos de CNPJ se necessário
        if self.tipo_doc.value == "CNPJ":
            base_fields.append(ft.Row([self.ie, self.im], wrap=True))
        
        # Adiciona o resto dos campos comuns
        base_fields.extend([
            ft.Divider(),
            ft.Text("Endereço", size=20, weight=ft.FontWeight.BOLD),
            ft.Row([self.street, self.number], wrap=True),
            ft.Row([self.complement, self.neighborhood], wrap=True),
            ft.Row([self.city, self.state, self.postal_code], wrap=True),

            ft.Divider(),
            ft.Text("Informações Adicionais", size=20, weight=ft.FontWeight.BOLD),
            ft.Row([self.size, self.crt], wrap=True),
        ])
        
        # Atualiza o conteúdo
        self.content = ft.Column(base_fields, scroll=ft.ScrollMode.AUTO)

    def clear_form(self):
        """Limpa todos os campos do formulário"""
        for field in self.__dict__.values():
            if isinstance(field, (ft.TextField, ft.Dropdown)):
                field.value = None
                if hasattr(field, 'error_text'):
                    field.error_text = None
        
        # Reseta o tipo de documento para CNPJ (valor padrão)
        self.tipo_doc.value = "CNPJ"
        # Atualiza os labels e visibilidade
        self._handle_doc_type_change(None)
