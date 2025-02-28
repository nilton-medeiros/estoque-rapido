import asyncio
import logging
import os

import flet as ft

from src.controllers.dfe_controller import handle_upload_certificate_a1
from src.domain.models.cnpj import CNPJ
from src.domain.models.cpf import CPF
from src.domain.models.phone_number import PhoneNumber
from src.domain.models.company_subclass import CompanySize, CodigoRegimeTributario, Environment
from src.services.apis.consult_cnpj_api import consult_cnpj_api
from src.utils.message_snackbar import MessageType, message_snackbar

logger = logging.getLogger(__name__)


class CompanyForm(ft.Container):
    def __init__(self, page: ft.Page, company_data: dict = None):
        super().__init__()
        self.page = page
        self.bgcolor = "#111418"
        self.width = 1500
        self.height = 850
        self.company_data = company_data
        self.padding = 20
        self.scroll = ft.ScrollMode.ALWAYS
        self._create_form_fields()
        self._progress_bar = ft.ProgressBar(visible=False)
        self._status_text = ft.Text()

        # Bind the dropdown change event
        self.tipo_doc.on_change = self._handle_doc_type_change

        self.content = self._build_content()

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
        # Adiciona o campo CNPJ e o botão de consulta
        self.cnpj = ft.TextField(
            label="CNPJ",
            border=ft.InputBorder.UNDERLINE,
            width=200,
            on_change=self._handle_cnpj_change
        )
        self.consult_cnpj_button = ft.IconButton(
            icon=ft.Icons.SEARCH,
            tooltip="Consultar CNPJ",
            visible=False,
            disabled=True,
            on_click=self._consult_cnpj
        )
        # Adiciona o campo CPF
        self.cpf = ft.TextField(
            label="CPF",
            border=ft.InputBorder.UNDERLINE,
            width=200,
            on_change=self._handle_cpf_change
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
        self.store_name = ft.TextField(
            label="Nome da Loja",
            hint_text="Loja Moema, Loja Iguatemi-0325",
            hint_style=ft.TextStyle(
                color=ft.Colors.WHITE30,          # Cor do placeholder mais visível
                weight=ft.FontWeight.W_100        # Placeholder um pouco mais fino
            ),
             hint_fade_duration=5,
            border=ft.InputBorder.UNDERLINE,
            width=400,
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
            hint_text="+55(99)99999-9999",
            hint_style=ft.TextStyle(
                color=ft.Colors.WHITE30,          # Cor do placeholder mais visível
                weight=ft.FontWeight.W_100        # Placeholder um pouco mais fino
            ),
        )

        # Endereço
        self.street = ft.TextField(
            label="Rua",
            border=ft.InputBorder.UNDERLINE,
            width=400,
        )
        self.number = ft.TextField(
            label="Número",
            border=ft.InputBorder.UNDERLINE,
            width=100,
        )
        self.complement = ft.TextField(
            label="Complemento",
            border=ft.InputBorder.UNDERLINE,
            width=400,
        )
        self.neighborhood = ft.TextField(
            label="Bairro",
            border=ft.InputBorder.UNDERLINE,
            width=300,
        )
        self.city = ft.TextField(
            label="Cidade",
            border=ft.InputBorder.UNDERLINE,
            width=400,
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
            width=400,
            options=[
                ft.dropdown.Option(key=size.name, text=size.value)
                for size in CompanySize
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
            border=ft.InputBorder.UNDERLINE,
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
            border=ft.InputBorder.UNDERLINE,
            width=300,
        )
        # Tipo de Ambiente
        self.nfce_environment = ft.Dropdown(
            label="Ambiente",
            hint_content="Ambiente de emissão da NFC-e (Homologação ou Produção)",
            width=200,
            value=Environment.HOMOLOGACAO,  # Default value
            options=[
                ft.dropdown.Option(key=ambiente.name, text=ambiente.value)
                for ambiente in Environment
            ],
        )
        self.nfce_sefaz_id_csc = ft.TextField(
            label="Identificação do CSC",
            hint_text="Id. Código Segurança do Contribuínte",
            hint_style=ft.TextStyle(
                color=ft.Colors.WHITE30,          # Cor do placeholder mais visível
                weight=ft.FontWeight.W_100        # Placeholder um pouco mais fino
            ),
            keyboard_type=ft.KeyboardType.NUMBER,
            border=ft.InputBorder.UNDERLINE,
            width=400,
        )
        self.nfce_sefaz_csc = ft.TextField(
            label="Código do CSC",
            hint_text="Código Segurança do Contribuínte",
            hint_style=ft.TextStyle(
                color=ft.Colors.WHITE30,          # Cor do placeholder mais visível
                weight=ft.FontWeight.W_100        # Placeholder um pouco mais fino
            ),
            border=ft.InputBorder.UNDERLINE,
            width=400,
        )

        # Certificado A1 (PFX/P12)

        self.certificate_a1_btn = ft.ElevatedButton(
            text="Carregar Certificado A1 (PFX/P12)",
            tooltip="Certificado digital no formato PFX ou P12",
            icon=ft.Icons.CLOUD_UPLOAD,
            on_click=self._show_certificate_dialog,
        )

        """Os componentes abaixo são apenas para exibição de informações do certificado digital."""
        self.certificate_a1_status = ft.TextField(
            value="VAZIO",
            label="Status Certificado",
            read_only=True,
            border=ft.InputBorder.UNDERLINE,
            width=200,
        )
        self.certificate_a1_serial_number = ft.TextField(
            label="Número de Série",
            read_only=True,
            border=ft.InputBorder.UNDERLINE,
            width=200,
        )
        self.certificate_a1_issuer_name = ft.TextField(
            label="Emissor do certificado",
            read_only=True,
            border=ft.InputBorder.UNDERLINE,
            width=200,
        )
        self.certificate_a1_not_valid_before = ft.TextField(
            label="Válido a partir de",
            read_only=True,
            border=ft.InputBorder.UNDERLINE,
            width=200,
        )
        self.certificate_a1_not_valid_after = ft.TextField(
            label="Expira em",
            read_only=True,
            border=ft.InputBorder.UNDERLINE,
            width=200,
        )
        self.subject_name = ft.TextField(
            label="Nome Assunto",
            read_only=True,
            border=ft.InputBorder.UNDERLINE,
            width=200,
        )
        self.certificate_a1_password = ft.TextField(
            label="Senha do Certificado",
            hint_text="Senha do certificado digital",
            hint_style=ft.TextStyle(
                color=ft.Colors.WHITE30,          # Cor do placeholder mais visível
                weight=ft.FontWeight.W_100        # Placeholder um pouco mais fino
            ),
            password=True,
            can_reveal_password=True,
            border=ft.InputBorder.UNDERLINE,
            width=300,
        )
        self.certificate_a1_file = ft.TextField(
            label="Arquivo do Certificado",
            read_only=True,
            border=ft.InputBorder.UNDERLINE,
            width=300,
        )

        # ToDo: Implementar upload de arquivo para logotipo da empresa
        self.logo_btn = ft.ElevatedButton()

    # Mostra um diálogo para selecionar o arquivo PFX/P12
    def _show_certificate_dialog(self, e):

        async def pick_file_certificate_result(e: ft.FilePickerResultEvent):
            if not e.files:
                self.certificate_a1_file.value = "Nenhum arquivo selecionado"
                self.certificate_a1_file.update()
                return

            # Atualiza o nome do arquivo selecionado
            self.certificate_a1_file.value = e.files[0].name
            self.certificate_a1_file.update()

            # Inicia o upload do arquivo
            await upload_certificate(e.files)

        def handle_upload_progress(e: ft.FilePickerProgressEvent):
            # Atualiza a barra de progresso
            if e.progress == 1:
                self._progress_bar.visible = False
                self.certificate_a1_file.value = "Upload concluído!"
            else:
                self._progress_bar.visible = True
                self._progress_bar.vallue = e.progress

            self.certificate_a1_file.update()
            self._progress_bar.update()

        # Cria o FilePicker
        picker_dialog = ft.FilePicker(
            accept=".pfx,.p12",
            on_result=pick_file_certificate_result,
            on_progress=handle_upload_progress,
        )

        async def upload_certificate(files):
            self._progress_bar.visible = True
            self._progress_bar.value = 0
            self._progress_bar.update()

            file_name = files[0].name

            try:
                # Gera uma URL assinada para upload (válida por 60 segundos)
                upload_url = self.page.get_upload_url(file_name, 60)

                # Configura o upload
                upload_files = [
                    ft.FilePickerUploadFile(
                        name=file_name,
                        upload_url=upload_url
                    )
                ]

                # Inicia o upload para o servidor
                # Criamos uma Promise para aguardar a conclusão do upload
                upload_complete = False

                def on_upload_completed(e):
                    nonlocal upload_complete
                    if e.progress == 1:
                        upload_complete = True

                picker_dialog.on_upload = on_upload_completed
                picker_dialog.upload(upload_files)

                # Aguarda até que o upload seja concluído
                while not upload_complete:
                    # Pequena pausa para não sobrecarregar o CPU
                    await asyncio.sleep(0.1)

                # ToDo: Estudar se aqui é o local para verificar se a senha do certificado está preenchida
                if not self.certificate_a1_password.value:
                    message_snackbar(page=self.page, message="Senha do certificado não informada!", message_type=MessageType.ERROR)
                    return

                # Caminho do arquivo no servidor após o upload
                server_file_path = os.path.join(self.page.views_storage_path, "uploads", file_name)

                # Lê o conteúdo binário do arquivo
                with open(server_file_path, "rb") as file:
                    file_content = file.read()

                # Envia o certificado para a API do provedor (DFe Provider)
                cpf_cnpj = self.cnpj.value if self.tipo_doc.value == "CNPJ" else self.cpf.value

                response = handle_upload_certificate_a1(
                    cpf_cnpj=cpf_cnpj,
                    certificate_content=file_content,
                    a1_password=self.certificate_a1_password.value,
                    ambiente=Environment(self.nfce_environment.value)
                )

                if response.get('is_error', False):
                    # Exibe mensagem de erro
                    error_message = response.get("message", "Erro desconhecido")
                    message_snackbar(page=self.page, message=f"Erro ao enviar certificado: {error_message}", message_type=MessageType.ERROR)
                else:
                    # Processa a resposta
                    data = response.get('certificate')

                    # Atualiza os campos da interface com as informações do certificado
                    self.certificate_a1_serial_number.value = data.get("serial_number", "")
                    self.certificate_a1_issuer_name.value = data.get("issuer_name", "")
                    self.certificate_a1_not_valid_before.value = data.get("not_valid_before", "")
                    self.certificate_a1_not_valid_after.value = data.get("not_valid_after", "")
                    self.certificate_a1_status.value = "ATIVO"

                    # Exibe mensagem de sucesso
                    success_message = response.get('message', 'Certificado enviado com sucesso!')
                    message_snackbar(page=self.page, message=success_message, message_type=MessageType.SUCCESS)

            except Exception as error:
                logger.error(f"Erro ao carregar certificado: {str(error)}")
                # Exibe mensagem de erro
                message_snackbar(page=self.page, message=f"Erro ao carregar certificado: {str(error)}", message_type=MessageType.ERROR)

            finally:
                # Atualiza a barra de progresso
                self._progress_bar.visible = False
                self._progress_bar.update()

        # Adiciona o FilePicker ao overlay
        self.page.overlay.append(picker_dialog)

        # Mostra o diálogo para selecionar o arquivo PFX/P12
        picker_dialog.pick_files(
            allow_multiple=False,
            allowed_extensions=[".pfx", ".p12"],
        )

    def _build_content(self):
        """Constrói o conteúdo do formulário"""
        build_content = ft.Column(
            [
                ft.Text("Dados da Empresa", size=20, weight=ft.FontWeight.BOLD),
                ft.Row([self.tipo_doc, self.cnpj, self.consult_cnpj_button], alignment=ft.MainAxisAlignment.SPACE_EVENLY, spacing=20, run_spacing=20, wrap=True),
                ft.Row([self.cpf], alignment=ft.MainAxisAlignment.SPACE_EVENLY, spacing=20, run_spacing=20, wrap=True),
                ft.Row([self.ie, self.im], alignment=ft.MainAxisAlignment.SPACE_EVENLY, spacing=20, run_spacing=20, wrap=True),
                ft.Row([self.name, self.corporate_name], alignment=ft.MainAxisAlignment.SPACE_EVENLY, spacing=20, run_spacing=20, wrap=True),
                ft.Row([self.store_name, self.phone, self.email], alignment=ft.MainAxisAlignment.SPACE_EVENLY, spacing=20, run_spacing=20, wrap=True),

                ft.Divider(),
                ft.Text("Endereço", size=20, weight=ft.FontWeight.BOLD),
                ft.Row([self.street, self.number], alignment=ft.MainAxisAlignment.SPACE_EVENLY, spacing=20, run_spacing=20, wrap=True),
                ft.Row([self.complement, self.neighborhood], alignment=ft.MainAxisAlignment.SPACE_EVENLY, spacing=20, run_spacing=20, wrap=True),
                ft.Row([self.city, self.state, self.postal_code], alignment=ft.MainAxisAlignment.SPACE_EVENLY, spacing=20, run_spacing=20, wrap=True),

                ft.Divider(),
                ft.Text("Informações Fiscais - Obrigatório se for emitir Nota ao Consumidor (NFC-e)", size=20,
                        weight=ft.FontWeight.BOLD),
                ft.Text("Consulte o seu contador para obter dados corretos", size=16),
                ft.Row([self.size, self.crt], alignment=ft.MainAxisAlignment.SPACE_EVENLY, spacing=20, run_spacing=20, wrap=True),
                ft.Row([self.nfce_series, self.nfce_number], alignment=ft.MainAxisAlignment.SPACE_EVENLY, spacing=20, run_spacing=20, wrap=True),
                ft.Row([self.nfce_environment, self.nfce_sefaz_id_csc, self.nfce_sefaz_csc], alignment=ft.MainAxisAlignment.SPACE_EVENLY, spacing=20, run_spacing=20, wrap=True),

                ft.Divider(),
                ft.Text("Certificado Digital A1 (PFX/P12)", size=20, weight=ft.FontWeight.BOLD),
                ft.Row([self.certificate_a1_password, self.certificate_a1_btn, self.certificate_a1_status], alignment=ft.MainAxisAlignment.SPACE_EVENLY, spacing=20, run_spacing=20, wrap=True),
                ft.Row([self.certificate_a1_serial_number, self.certificate_a1_issuer_name], alignment=ft.MainAxisAlignment.SPACE_EVENLY, spacing=20, run_spacing=20, wrap=True),
                ft.Row([self.certificate_a1_not_valid_before, self.certificate_a1_not_valid_after], alignment=ft.MainAxisAlignment.SPACE_EVENLY, spacing=20, run_spacing=20, wrap=True),
                ft.Row([self.subject_name, self.certificate_a1_file], alignment=ft.MainAxisAlignment.SPACE_EVENLY, spacing=20, run_spacing=20, wrap=True),
            ],
            spacing=20,
            run_spacing=20,
            scroll=ft.ScrollMode.AUTO,
        )

        return ft.Container(
            build_content,
            padding=ft.padding.all(20),
        )

    def _handle_doc_type_change(self, e):
        """Atualiza os labels e visibilidade dos campos baseado no tipo de documento"""
        is_cnpj = self.tipo_doc.value == "CNPJ"

        if not is_cnpj:
            # Atualiza labels para pessoa física
            self.name.label = "Nome/Apelido"
            self.corporate_name.label = "Nome Completo"
            # Oculta campos específicos de empresa
            self.cnpj.visible = False
            self.cpf.visible = True
            self.ie.visible = False
            self.im.visible = False
            self.consult_cnpj_button.visible = False
        else:  # CNPJ
            # Atualiza labels para pessoa jurídica
            self.name.label = "Nome Fantasia"
            self.corporate_name.label = "Razão Social"
            # Mostra campos específicos de empresa
            self.cnpj.visible = True
            self.cpf.visible = False
            self.ie.visible = True
            self.im.visible = True
            self.consult_cnpj_button.visible = True
            # Atualiza estado do botão baseado no CNPJ
            self._handle_cnpj_change(None)

        # Atualiza a UI
        self.update()

    def _handle_cnpj_change(self, e):
        """Atualiza o estado do botão de consulta baseado no valor do CNPJ"""
        cnpj_clean = ''.join(filter(str.isdigit, self.cnpj.value))

        if not self.consult_cnpj_button.disabled and len(cnpj_clean) < 14:
            self.consult_cnpj_button.disabled = True
            self.update()
        elif len(cnpj_clean) == 14:
            self.cnpj.value = cnpj_clean
            self.consult_cnpj_button.disabled = not self.tipo_doc.value == "CNPJ"
            self.update()

    def _handle_cpf_change(self, e):
        cpf_clean =  ''.join(filter(str.isdigit, self.cpf.value))
        if len(cpf_clean) == 11:
            self.cpf.value = cpf_clean
            self.update()

    async def _consult_cnpj(self, e):
        """Consulta o CNPJ na API da Receita"""
        try:
            # Mostra loading no botão
            self.consult_cnpj_button.icon = ft.Icons.PENDING
            self.consult_cnpj_button.disabled = True
            self.update()

            response = await consult_cnpj_api(self.cnpj.value)

            if response['is_error']:
                # Mostra erro
                message_snackbar(
                    page=self.page,
                    message="Erro ao consultar CNPJ. Verifique o número e tente novamente.",
                    message_type=MessageType.ERROR
                )
            else:
                local_response = response.get('response')
                data = response.get('data')

                if local_response.status in (200, 304):
                    # Preenche os campos com os dados retornados
                    self.name.value = data.get('nome_fantasia', '')
                    self.corporate_name.value = data.get('razao_social', '')
                    self.phone.value = data.get('ddd_telefone_1', '')

                    # Endereço
                    self.street.value = data.get('logradouro', '')
                    self.number.value = data.get('numero', '')
                    self.complement.value = data.get('complemento', '')
                    self.neighborhood.value = data.get('bairro', '')
                    self.city.value = data.get('municipio', '')
                    self.state.value = data.get('uf', '')
                    self.postal_code.value = data.get('cep', '')

                    # Fiscal
                    porte = data.get('codigo_porte', 0)

                    match porte:
                        case 1:
                            self.size.value = CompanySize.MICRO
                        case 3:
                            self.size.value = CompanySize.SMALL
                        case 5:
                            self.size.value = CompanySize.OTHER

                    # Mostra mensagem de sucesso
                    message_snackbar(page=self.page, message="Dados do CNPJ carregados com sucesso!", message_type=MessageType.SUCCESS)
                else:
                    # Mostra erro
                    message_snackbar(
                        page=self.page,
                        message="Erro ao consultar CNPJ. Verifique o número e tente novamente.",
                        message_type=MessageType.ERROR
                    )

        except Exception as error:
            # Mostra erro genérico
            logger.error(f"Erro ao consultar CNPJ: {str(error)}")
            message_snackbar(
                page=self.page,
                message=f"Erro ao consultar CNPJ: {str(error)}",
                message_type=MessageType.ERROR
            )

        finally:
            # Restaura o botão
            self.consult_cnpj_button.icon = ft.Icons.SEARCH
            self.consult_cnpj_button.disabled = not bool(self.cnpj.value)
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
        # ToDo: Incompleto: Concluir preenchimento de todos os campos do form
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
        # ToDo: Verificar, talvez esteja incompleto
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
                    "cnpj": self.cnpj.value,
                    "ie": self.ie.value,
                    "im": self.im.value,
                })
            else:  # CPF
                form_data["cpf"] = CPF(self.cnpj.value)

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
            logger.error(f"Erro ao validar dados do formulário: {str(e)}")
            raise ValueError(f"Erro ao validar dados do formulário: {str(e)}")


    def before_update(self):
        """Atualiza o conteúdo do container antes de renderizar"""
        # Cria uma lista de campos que sempre aparecem
        base_fields = [
            ft.Text("Dados da Empresa", size=20, weight=ft.FontWeight.BOLD),
            ft.Row([self.tipo_doc], alignment=ft.MainAxisAlignment.SPACE_EVENLY, spacing=20, run_spacing=20, wrap=True),
        ]

        # Adiciona campos específicos de CNPJ se necessário
        if self.tipo_doc.value == "CNPJ":
            base_fields.append(ft.Row([self.cnpj, self.consult_cnpj_button], alignment=ft.MainAxisAlignment.SPACE_EVENLY, spacing=20, run_spacing=20, wrap=True))
            base_fields.append(ft.Row([self.ie, self.im], alignment=ft.MainAxisAlignment.SPACE_EVENLY, spacing=20, run_spacing=20, wrap=True))
        else:
            base_fields.append(ft.Row([self.cpf], alignment=ft.MainAxisAlignment.SPACE_EVENLY, spacing=20, run_spacing=20, wrap=True))

        base_fields.append(ft.Row([self.name, self.corporate_name], alignment=ft.MainAxisAlignment.SPACE_EVENLY, spacing=20, run_spacing=20, wrap=True))
        base_fields.append(ft.Row([self.store_name, self.phone, self.email], alignment=ft.MainAxisAlignment.SPACE_EVENLY, spacing=20, run_spacing=20, wrap=True))

        # Adiciona o resto dos campos comuns
        base_fields.extend([
            ft.Divider(),
            ft.Text("Endereço", size=20, weight=ft.FontWeight.BOLD),
            ft.Row([self.street, self.number], alignment=ft.MainAxisAlignment.SPACE_EVENLY, spacing=20, run_spacing=20, wrap=True),
            ft.Row([self.complement, self.neighborhood], alignment=ft.MainAxisAlignment.SPACE_EVENLY, spacing=20, run_spacing=20, wrap=True),
            ft.Row([self.city, self.state, self.postal_code], alignment=ft.MainAxisAlignment.SPACE_EVENLY, spacing=20, run_spacing=20, wrap=True),

            ft.Divider(),
            ft.Text("Informações Fiscais - Obrigatório se for emitir Nota ao Consumidor (NFC-e)", size=20,
                        weight=ft.FontWeight.BOLD),
            ft.Text("Consulte o seu contador para obter dados corretos", size=16),
            ft.Row([self.size, self.crt], alignment=ft.MainAxisAlignment.SPACE_EVENLY, spacing=20, run_spacing=20, wrap=True),
            ft.Row([self.nfce_series, self.nfce_number], alignment=ft.MainAxisAlignment.SPACE_EVENLY, spacing=20, run_spacing=20, wrap=True),
            ft.Row([self.nfce_environment, self.nfce_sefaz_id_csc, self.nfce_sefaz_csc], alignment=ft.MainAxisAlignment.SPACE_EVENLY, spacing=20, run_spacing=20, wrap=True),

            ft.Divider(),
            ft.Text("Certificado Digital A1 (PFX/P12)", size=20, weight=ft.FontWeight.BOLD),
            ft.Row([self.certificate_a1_password, self.certificate_a1_btn, self.certificate_a1_status], alignment=ft.MainAxisAlignment.SPACE_EVENLY, spacing=20, run_spacing=20, wrap=True),
            ft.Row([self.certificate_a1_serial_number, self.certificate_a1_issuer_name], alignment=ft.MainAxisAlignment.SPACE_EVENLY, spacing=20, run_spacing=20, wrap=True),
            ft.Row([self.certificate_a1_not_valid_before, self.certificate_a1_not_valid_after], alignment=ft.MainAxisAlignment.SPACE_EVENLY, spacing=20, run_spacing=20, wrap=True),
            ft.Row([self.subject_name, self.certificate_a1_file], alignment=ft.MainAxisAlignment.SPACE_EVENLY, spacing=20, run_spacing=20, wrap=True),
        ])

        # Atualiza o conteúdo
        content = ft.Column(base_fields, spacing=20, run_spacing=20, scroll=ft.ScrollMode.AUTO)
        self.content = ft.Container(
            content=content,
            padding=ft.padding.all(20),
        )

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
