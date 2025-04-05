import asyncio
import logging
import os

import flet as ft

from src.controllers.bucket_controllers import handle_upload_bucket
from src.controllers.dfe_controller import handle_upload_certificate_a1
from src.services.apis.consult_cnpj_api import consult_cnpj_api
from src.shared import get_uuid, MessageType, message_snackbar
from src.domains.empresas import CNPJ, CodigoRegimeTributario, EmpresaSize, Environment

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

        self.content = self._build_content()

    def _create_form_fields(self):
        """Cria todos os campos do formulário"""

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
        self.certificate_a1_subject_name = ft.TextField(
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
        self.certificate_a1_file_name = ft.TextField(
            label="Nome do arquivo A1",
            read_only=True,
            border=ft.InputBorder.UNDERLINE,
            width=300,
        )

        # Definindo o evento on_hover_logo
        def on_hover_logo(e):
            # control = e.control
            # Atualiza o ícone da câmera
            ci = self.camera_icon
            lf = self.logo_frame

        # Construção do campo Logo do emitente de NFCe
        self.camera_icon = ft.Container(
            content=ft.Icon(
                name=ft.Icons.ADD_A_PHOTO_OUTLINED,
                size=20,
                color=ft.Colors.PRIMARY,
            ),
            margin=ft.margin.only(top=-15),
            ink=True,
            on_hover=on_hover_logo,
            on_click=self._show_logo_dialog,
            border_radius=ft.border_radius.all(10),
            padding=8,
        )

        self.logo_url: str = None

        logo = ft.Text("Logo", italic=True)

        self.logo_frame = ft.Container(
            content=logo,
            bgcolor=ft.Colors.TRANSPARENT,
            padding=10,
            alignment=ft.alignment.center,
            width=300,
            height=200,
            border=ft.border.all(color=ft.Colors.PRIMARY, width=1),
            border_radius=ft.border_radius.all(10),
            on_hover=on_hover_logo,
            on_click=self._show_logo_dialog,  # Também permite clicar na imagem
        )

        self.logo_section = ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                self.logo_frame,
                self.camera_icon,
            ]
        )

    # Mostra um diálogo para selecionar o arquivo PFX/P12
    def _show_certificate_dialog(self, e):

        async def pick_file_certificate_result(e: ft.FilePickerResultEvent):
            if not e.files:
                self.certificate_a1_file_name.value = "Nenhum arquivo selecionado"
                self.certificate_a1_file_name.update()
                return

            # Atualiza o nome do arquivo selecionado
            self.certificate_a1_file_name.value = e.files[0].name
            self.certificate_a1_file_name.update()

            # Inicia o upload do arquivo
            await upload_certificate(e.files)

        def handle_upload_progress(e: ft.FilePickerProgressEvent):
            # Atualiza a barra de progresso
            if e.progress == 1:
                self._progress_bar.visible = False
                self.certificate_a1_file_name.value = "Upload concluído!"
                self._progress_bar.vallue = e.progress

            self.certificate_a1_file_name.update()
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
                server_file_path = os.path.join("uploads", file_name)

                # Lê o conteúdo binário do arquivo
                with open(server_file_path, "rb") as file:
                    file_content = file.read()

                # Envia o certificado para a API do provedor (DFe Provider)
                cnpj = self.cnpj.value

                response = handle_upload_certificate_a1(
                    cnpj=cnpj,
                    certificate_content=file_content,
                    a1_password=self.certificate_a1_password.value,
                    ambiente=Environment(self.nfce_environment.value)
                )

                if response.get('is_error', False):
                    # Exibe mensagem de erro
                    error_message = response.get("message", "Erro desconhecido")
                    message_snackbar(page=self.page, message=f"Erro ao enviar certificado: {error_message}", message_type=MessageType.ERROR)
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

    def _show_logo_dialog(self, e):
        lf = self.logo_frame
        lf.border = ft.border.all(color=ft.Colors.PRIMARY, width=1)
        self.update()

        print("Entrou em _show_logo_dialog")

        async def handle_file_picker_result(e: ft.FilePickerResultEvent):
            if not e.files:
                self._status_text.value = "Nenhum Logo selecionado"
                self._status_text.update()
                return

            # Atualiza o texto com o nome do arquivo selecionado
            self._status_text.value = f"Logo selecionado: {e.files[0].name}"
            self._status_text.update()

            # Inicia o upload do arquivo
            await upload_file(e.files)

        def handle_upload_progress(e: ft.FilePickerUploadEvent):
            # Atualiza a barra de progresso
            if e.progress == 1:
                self._progress_bar.visible = False
                self._status_text.value = "Upload concluído!"
                self._progress_bar.value = e.progress

            self._status_text.update()
            self._progress_bar.update()

        # Cria o FilePicker
        pick_files_dialog = ft.FilePicker(
            on_result=handle_file_picker_result,
            on_upload=handle_upload_progress
        )

        async def upload_file(files):
            self._progress_bar.visible = True
            self._progress_bar.value = 0
            self._progress_bar.update()

            file_name = files[0].name
            # Gera uma URL assinada para upload (válida por 60 segundos)
            upload_url = self.page.get_upload_url(file_name, 60)

            # Configura o upload
            upload_files = [
                ft.FilePickerUploadFile(
                    name=file_name,
                    upload_url=upload_url
                )
            ]

            # Inicia o upload para o servidor do estoquerapido
            # Criamos uma Promise para aguardar a conclusão do upload
            upload_complete = False

            def on_upload_completed(e):
                nonlocal upload_complete
                if e.progress == 1:
                    upload_complete = True

            pick_files_dialog.on_upload = on_upload_completed
            pick_files_dialog.upload(upload_files)

            # Aguarda até que o upload seja concluído
            while not upload_complete:
                # Pequena pausa para não sobrecarregar o CPU
                await asyncio.sleep(0.1)

            # Agora que o upload está concluído, podemos prosseguir com o upload para S3
            # pegar cnpj, devem estar preenchidos

            cnpj = self.cnpj.value

            if not cnpj:
                # Cancelar o upload
                return

            prefix = cnpj
            file_uid = get_uuid()

            _, dot_extension = os.path.splitext(file_name)
            dot_extension = dot_extension.lower()

            file_name_bucket = f"{prefix}/cia_logo_{file_uid}{dot_extension}"
            local_file = f"uploads/{file_name}"

            # Adiciona uma verificação extra para garantir que o arquivo existe
            max_retries = 10
            retry_count = 0
            while not os.path.exists(local_file) and retry_count < max_retries:
                # Espera meio segundo entre tentativas
                await asyncio.sleep(0.5)
                retry_count += 1

            if not os.path.exists(local_file):
                logger.debug(f"Arquivo {local_file} não foi encontrado após {max_retries} tentativas")
                raise FileNotFoundError(
                    f"Arquivo {local_file} não foi encontrado após {max_retries} tentativas")

            message_snackbar = "Logo carregado com sucesso!"
            message_type = MessageType.INFO

            try:
                self.logo_url = await handle_upload_bucket(local_path=local_file, key=file_name_bucket)
                # O logo só será salvo no database quando o usuário clicar no botão salvar, para salvar todos os dados do formulário

            except ValueError as e:
                logger.error(str(e))
                self.logo_url = None
                message_snackbar = f"Erro: {str(e)}"
                message_type = MessageType.ERROR
            except RuntimeError as e:
                logger.error(str(e))
                self.logo_url=None
                message_snackbar = f"Erro no upload: {str(e)}"
                message_type = MessageType.ERROR

            message_snackbar(page=self.page, message=message_snackbar, message_type=message_type)

            # Limpa o arquivo local independente do upload ou falha
            try:
                os.remove(local_file)
            except:
                pass  # Ignora erros na limpeza do arquivo

            self.page.close(dialog)


        # Adiciona o FilePicker ao overlay da página
        self.page.overlay.append(pick_files_dialog)

        # Dropdown para escolher tipo de imagem
        image_type_dd = ft.Dropdown(
            width=200,
            options=[
                ft.dropdown.Option("arquivo", "Arquivo Local"),
                ft.dropdown.Option("url", "URL da Web"),
            ],
            value="arquivo",
            label="Tipo de Imagem",
        )

        url_field = ft.TextField(
            label="URL da Imagem",
            width=200,
            visible=False
        )

        def type_changed(e):
            url_field.visible = image_type_dd.value == "url"
            self.page.update()

        image_type_dd.on_change = type_changed

        def update_image(e):
            print(f"Atualizando imagem...")

            selected_type = image_type_dd.value
            if selected_type == "arquivo":
                pick_files_dialog.pick_files(
                    allow_multiple=False,
                    allowed_extensions=["png", "jpg", "jpeg", "svg"]
                )
                """
                O Logo só será salvo no database quando o usuário clicar no botão salvar
                do formulário para salvar todos os dados.
                """
                self.logo_url = url_field.value
                self.page.close(dialog)

        def close_dialog(e):
            self.page.close(dialog)
            if self.page.overlay:
                self.page.overlay.pop()
                self.page.update()

        # Criando o diálogo
        dialog = ft.AlertDialog(
            modal=True,  # Garante que o diálogo bloqueie interações com a página
            title=ft.Text("Selecionar Imagem Logo"),
            content=ft.Column(
                controls=[
                    image_type_dd,
                    url_field,
                    self._status_text,
                ],
                height=150,
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=close_dialog),
                ft.TextButton("Selecionar", on_click=update_image),
            ],
        )

        # Abrindo o diálogo
        self.page.open(dialog)

    def _build_content(self):
        """Constrói o conteúdo do formulário"""
        build_content = ft.Column(
            [
                ft.Text("Logo na NFCe", size=20, weight=ft.FontWeight.BOLD),
                ft.Row([self.logo_section], alignment=ft.MainAxisAlignment.SPACE_EVENLY, spacing=20, run_spacing=20, wrap=True),

                ft.Divider(),
                ft.Text("Dados da Empresa", size=20, weight=ft.FontWeight.BOLD),
                ft.Row([self.cnpj, self.consult_cnpj_button], alignment=ft.MainAxisAlignment.SPACE_EVENLY, spacing=20, run_spacing=20, wrap=True),
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
                ft.Row([self.certificate_a1_subject_name, self.certificate_a1_file_name], alignment=ft.MainAxisAlignment.SPACE_EVENLY, spacing=20, run_spacing=20, wrap=True),
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
            self.consult_cnpj_button.disabled = False
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
                            self.size.value = EmpresaSize.MICRO
                        case 3:
                            self.size.value = EmpresaSize.SMALL
                        case 5:
                            self.size.value = EmpresaSize.OTHER

                    # Mostra mensagem de sucesso
                    message_snackbar(page=self.page, message="Dados do CNPJ carregados com sucesso!", message_type=MessageType.SUCCESS)
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
        """Chamado quando o controle é montado a pagina"""
        if self.company_data:
            self.populate_form()
        # Configura o estado inicial dos campos baseado no tipo de documento padrão
        self._handle_doc_type_change(None)
        self.update()

    def populate_form(self):
        # ToDo: Incompleto: Concluir preenchimento de todos os campos do form
        """Preenche o formulário com os dados existentes"""

        # Define o tipo de documento baseado nos dados
        self.cnpj.value = str(self.company_data.get('cnpj', ''))
        self.name.value = self.company_data.get('name', '')
        self.corporate_name.value = self.company_data.get('corporate_name', '')
        self.ie.value = self.company_data.get('ie', '')
        self.im.value = self.company_data.get('im', '')
        self.store_name.value = self.company_data.get("store_name", '')
        self.email.value = self.company_data.get("email", '')
        self.phone.value = str(self.company_data.get('phone', ''))

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

        # Logo
        if self.company_data.get('logo_url'):
            self.logo_url = self.company_data.get('logo_url')
            self.logo_frame.content = ft.Image(
                src=self.logo_url,
                error_content=ft.Text(self.company_data.get("initials_corporate_name")),
                repeat=ft.ImageRepeat.NO_REPEAT,
                fit=ft.ImageFit.FILL,
                border_radius=ft.border_radius.all(10),
                width=300,
                height=300,
            )

        if fiscal := self.company_data.get('fiscal'):
            if crt_enum := fiscal.get('crt'):
                self.crt.value = crt_enum.name  # Seta o default Dropdown pelo name do enum

            self.nfce_series.value = fiscal.get('nfce_series')
            self.nfce_number.value = fiscal.get('nfce_number')

        # ToDo: Implementar dados do certificado aqui

        # Atualiza os labels e visibilidade após popular
        self._handle_doc_type_change(None)

    def get_form_data(self) -> dict:
        """Obtém os dados do formulário como um dicionário"""
        try:
            # Base do dicionário
            form_data = {
                "name": self.name.value,
                "corporate_name": self.corporate_name.value,
                "email": self.email.value,
            }

            # Adiciona campos específicos baseado no tipo de documento
            form_data.update({
                "cnpj": CNPJ(self.cnpj.value),
                "ie": self.ie.value,
                "im": self.im.value,
            })

            form_data.update({
                "logo_url": self.logo_url
            })

            crt = None

            if self.crt.value:
                # Obtem o Enum selecionado pelo usuário
                crt = CodigoRegimeTributario(self.crt.value)
                crt = CodigoRegimeTributario.REGIME_NORMAL

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
                "crt": crt,
                "nfce_series": self.nfce_series.value,
                "nfce_number": self.nfce_number.value,
                "nfce_environment": Environment(self.nfce_environment.value),
                "nfce_sefaz_id_csc": self.nfce_sefaz_id_csc.value,
                "nfce_sefaz_csc": self.nfce_sefaz_csc.value,
            })

            # Adiciona dados do Certificado Digital A1
            if self.certificate_a1_status.value == "ATIVO":
                form_data.update({
                    "certificate_a1": {
                        "serial_number": self.certificate_a1_serial_number.value,
                        "issuer_name": self.certificate_a1_issuer_name.value,
                        "not_valid_before": self.certificate_a1_not_valid_before.value,
                        "not_valid_after": self.certificate_a1_not_valid_after.value,
                        "subject_name": self.certificate_a1_subject_name.value,
                        "file_name": self.certificate_a1_file_name.value,
                        "password": self.certificate_a1_password.value,
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
            ft.Text("Logo na NFCe", size=20, weight=ft.FontWeight.BOLD),
            ft.Row([self.logo_section], alignment=ft.MainAxisAlignment.SPACE_EVENLY, spacing=20, run_spacing=20, wrap=True),
            ft.Divider(),
            ft.Text("Dados da Empresa", size=20, weight=ft.FontWeight.BOLD),
        ]

        # Adiciona campos específicos de CNPJ se necessário
        base_fields.append(ft.Row([self.cnpj, self.consult_cnpj_button], alignment=ft.MainAxisAlignment.SPACE_EVENLY, spacing=20, run_spacing=20, wrap=True))
        base_fields.append(ft.Row([self.ie, self.im], alignment=ft.MainAxisAlignment.SPACE_EVENLY, spacing=20, run_spacing=20, wrap=True))
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
            ft.Row([self.certificate_a1_subject_name, self.certificate_a1_file_name], alignment=ft.MainAxisAlignment.SPACE_EVENLY, spacing=20, run_spacing=20, wrap=True),
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

        # Atualiza os labels e visibilidade
        self._handle_doc_type_change(None)
