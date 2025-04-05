import logging
import os
from typing import Optional
import src.shared.utils.tools as tools
import src.controllers.bucket_controllers as bucket_controllers
import flet as ft

from src.shared.utils.gen_uuid import get_uuid
from src.domains.empresas.models.empresa_subclass import CodigoRegimeTributario, EmpresaSize, Environment
from src.services.upload.upload_files import UploadFile
from src.services.apis.consult_cnpj_api import consult_cnpj_api
from src.shared.utils.message_snackbar import MessageType, message_snackbar

logger = logging.getLogger(__name__)

class EmpresaView:
    def __init__(self, page: ft.Page):
        self.page = page
        self._create_form_fields()
        self.form = self.build_form()
        self.page.on_resized = self.page_resized
        self.page.update()

    def _create_form_fields(self):
        """Cria todos os campos do formulário"""

        # Adiciona o campo CNPJ e o botão de consulta
        self.cnpj = ft.TextField(
            label="CNPJ",
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

                # Campos de nome com labels iniciais (CNPJ por padrão)
        self.name = ft.TextField(
            label="Nome Fantasia",
            width=400,
        )
        self.corporate_name = ft.TextField(
            label="Razão Social",
            width=400,
        )

        self.ie = ft.TextField(
            label="Inscrição Estadual",
            width=200,
        )
        self.im = ft.TextField(
            label="Inscrição Municipal",
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
            width=400,
        )

        # Informações de Contato
        self.email = ft.TextField(
            label="Email",
            keyboard_type=ft.KeyboardType.EMAIL,
            width=400,
        )
        self.phone = ft.TextField(
            label="Telefone",
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
            width=400,
        )
        self.number = ft.TextField(
            label="Número",
            width=100,
        )
        self.complement = ft.TextField(
            label="Complemento",
            width=400,
        )
        self.neighborhood = ft.TextField(
            label="Bairro",
            width=300,
        )
        self.city = ft.TextField(
            label="Cidade",
            width=400,
        )
        self.state = ft.TextField(
            label="Estado",
            width=100,
        )
        self.postal_code = ft.TextField(
            label="CEP",
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

        # Certificado A1 (PFX/P12)
        self.certificate_a1_btn = ft.ElevatedButton(
            text="Carregar Certificado A1 (PFX/P12)",
            tooltip="Certificado digital no formato PFX ou P12",
            icon=ft.Icons.CLOUD_UPLOAD,
            # on_click=self._show_certificate_dialog,
        )

        """Os componentes abaixo são apenas para exibição de informações do certificado digital."""
        self.certificate_a1_status = ft.TextField(
            value="VAZIO",
            label="Status Certificado",
            read_only=True,
            width=200,
        )
        self.certificate_a1_serial_number = ft.TextField(
            label="Número de Série",
            read_only=True,
            width=200,
        )
        self.certificate_a1_issuer_name = ft.TextField(
            label="Emissor do certificado",
            read_only=True,
            width=200,
        )
        self.certificate_a1_not_valid_before = ft.TextField(
            label="Válido a partir de",
            read_only=True,
            width=200,
        )
        self.certificate_a1_not_valid_after = ft.TextField(
            label="Expira em",
            read_only=True,
            width=200,
        )
        self.certificate_a1_subject_name = ft.TextField(
            label="Nome Assunto",
            read_only=True,
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
            width=300,
        )
        self.certificate_a1_file_name = ft.TextField(
            label="Nome do arquivo A1",
            read_only=True,
            width=300,
        )

        # URL do Logo da empresa emititente para NFCe
        self.logo_url: str = None
        self.previous_logo_url: str = None

        def on_hover_logo(e):
            icon_container = e.control
            icon_container.content.color = ft.Colors.PRIMARY if e.data == "true" else ft.Colors.GREY_400
            self.logo_frame.bgcolor = ft.Colors.PRIMARY if e.data == "true" else ft.Colors.TRANSPARENT
            icon_container.update()
            self.logo_frame.update()

        # Campo Logo do emitente de NFCe
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
            disabled=self.consult_cnpj_button.disabled,
        )
        self.logo_frame = ft.Container(
            content=ft.Text("Logo", italic=True),
            bgcolor=ft.Colors.TRANSPARENT,
            padding=10,
            alignment=ft.alignment.center,
            width=300,
            height=200,
            border=ft.border.all(color=ft.Colors.PRIMARY, width=1),
            border_radius=ft.border_radius.all(10),
            on_click=self._show_logo_dialog,  # Também permite clicar na imagem
            disabled=self.consult_cnpj_button.disabled,
        )

        self.logo_section = ft.Column(
            controls=[self.logo_frame, self.camera_icon],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0,
        )

    def _show_logo_dialog(self, e) -> None:
        cnpj_clean = ''.join(filter(str.isdigit, self.cnpj.value))
        if len(cnpj_clean) < 14:
            message_snackbar(page=self.page, message="Preencha corretamente o CNPJ da empresa", message_type=MessageType.WARNING)
            return

        self.logo_frame.border = ft.border.all(color=ft.Colors.PRIMARY, width=1)
        self.update()

        upload_file = UploadFile(
            page=self.page,
            title_dialog="Selecionar imagem do Logo",
            allowed_extensions=["png", "jpg", "jpeg", "svg"]
        )

        msg_error = upload_file.get_url_error()
        if msg_error:
            message_snackbar(page=self.page, message=msg_error, message_type=MessageType.ERROR)
            return

        initials_corporate_name = "Logo"
        corporate_name = self.corporate_name.value.strip()

        if corporate_name:
            initials_corporate_name = tools.initials(corporate_name)

        # O arquivo ou URL do logo foi obtido. Não há erros.
        if upload_file.is_url_web:
            # Obtem a url do arquivo para o logo, atualiza a tela com o logo e termina
            self.logo_url = upload_file.url_file

            logo_img = ft.Image(
                src=self.logo_url,
                error_content=ft.Text(initials_corporate_name),
                repeat=ft.ImageRepeat.NO_REPEAT,
                fit=ft.ImageFit.COVER,
                border_radius=ft.border_radius.all(100),
                width=300,
                height=200,
            )
            self.logo_frame.content = logo_img
            self.logo_section.update()
            message_snackbar(page=self.page, message="Logo carregado com sucesso!", duration=3000)
            return

        """
        O arquivo Logo está salvo no diretório local do servidor em uploads/ do projeto e está em upload_file.url_file.
        Preparação do upload do servidor do aplicativo para o Bucket e mostra ao usuário o logo na tela. Caso o usuário
        não salvar os dados da empresa, o logo será removido do Bucket de armazenamento.
        """
        local_file = upload_file.url_file
        cnpj = ''.join(filter(str.isdigit, self.cnpj.value))
        prefix = cnpj.strip()
        file_uid = get_uuid()

        _, dot_extension = os.path.splitext(local_file)
        dot_extension = dot_extension.lower()  # Padroniza a extensão para caracteres minúsculos

        # A lógica aqui depende do Bucket utilizado, neste caso é o S3 da AWS, usamos o CNPJ como diretório no bucket.
        file_name_bucket = f"{prefix}/logo_img_{file_uid}{dot_extension}"

        try:
            self.logo_url = bucket_controllers.handle_upload_bucket(local_path=local_file, key=file_name_bucket)
            if self.logo_url:
                # Atualiza logo na tela
                logo_img = ft.Image(
                    src=self.logo_url,
                    error_content=ft.Text(initials_corporate_name),
                    repeat=ft.ImageRepeat.NO_REPEAT,
                    fit=ft.ImageFit.COVER,
                    border_radius=ft.border_radius.all(100),
                    width=300,
                    height=200,
                )
                self.logo_frame.content = logo_img
                self.logo_section.update()
                message_snackbar(page=self.page, message="Logo carregado com sucesso!", duration=3000)
                return

            # O Logo não é válido, URL não foi gerada, mantém o logo anterior se houver
            if self.previous_logo_url:
                self.logo_url = self.previous_logo_url

            message_snackbar(page=self.page, message="Não foi possível carregar Logo!", message_type=MessageType.ERROR)

        except ValueError as e:
            msg = f"Erro de validação ao carregar o logo: {str(e)}"
            message_snackbar(page=self.page, message=msg, message_type=MessageType.ERROR)
            logger.error(msg)
        except RuntimeError as e:
            msg = f"Erro ao carregar o logo: {str(e)}"
            message_snackbar(page=self.page, message=msg, message_type=MessageType.ERROR)
            logger.error(msg)
        finally:
            # Independente de sucesso, remove o arquivo de logo do diretório local uploads/
            try:
                os.remove(local_file)
            except:
                pass  # Ignora erros na limpeza do arquivo

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

    async def _consult_cnpj(self, e):
        """Consulta o CNPJ na API da Receita"""
        try:
            # Mostra loading no botão
            self.consult_cnpj_button.icon = ft.Icons.PENDING
            self.consult_cnpj_button.disabled = True
            self.update()

            result = await consult_cnpj_api(self.cnpj.value)

            if result['is_error']:
                # Mostra erro
                message_snackbar(
                    page=self.page,
                    message="Erro ao consultar CNPJ. Verifique o número e tente novamente.",
                    message_type=MessageType.ERROR
                )
                return

            data = result.get('data')
            response = result.get('response')

            if response.status in (200, 304):
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





    def build_login_button(self, sizes: dict) -> ft.OutlinedButton:
        return ft.OutlinedButton(
            content=ft.Row(
                controls=[
                    ft.Icon(
                        ft.Icons.APP_REGISTRATION,
                        color=ft.Colors.WHITE,
                        size=sizes["icon_size"]
                    ),
                    ft.Text(
                        value="Entrar",
                        size=sizes["font_size"],
                        text_align=ft.TextAlign.CENTER,
                        weight=ft.FontWeight.W_500
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=sizes["spacing"],
                tight=True
            ),
            width=sizes["button_width"],
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                side=ft.BorderSide(
                    color=ft.Colors.YELLOW_ACCENT_400,
                    width=sizes["border_width"]
                ),
                padding=ft.padding.symmetric(
                    horizontal=sizes["spacing"] * 2,
                    vertical=sizes["spacing"]
                )
            ),
            on_click=self.handle_login,
        )

    def build_form(self) -> ft.Container:
        sizes = get_responsive_sizes(self.page.width)

        self.email_input = build_input_field(
            sizes=sizes, label="Email", icon=ft.Icons.EMAIL)
        self.password_input = build_input_field(
            sizes=sizes, label="Senha", icon=ft.Icons.LOCK, password=True)
        self.login_button = self.build_login_button(sizes)
        self.error_text = ft.Text(
            color=ft.Colors.RED_400, size=sizes["font_size"], visible=False)

        # Debug: Dados Fakes como hardcord, remover isto em produção
        self.email_input.value = 'ajolie@gmail.com'
        self.password_input.value = 'Aj#45678'

        self.page.user_name_text.visible = False  # Invisible, sem uso
        self.page.company_name_text_btn.visible = False  # Invisible, sem uso

        return ft.Container(
            alignment=ft.alignment.center,
            bgcolor=ft.Colors.BLACK,
            opacity=0.75,
            padding=ft.padding.all(sizes["form_padding"]),
            border_radius=10,  # Suaviza as bordas
            border=ft.border.all(color=ft.Colors.YELLOW_ACCENT_400, width=1),
            shadow=ft.BoxShadow(
                offset=ft.Offset(2, 2),  # Deslocamento horizontal e vertical
                blur_radius=16,  # Raio de desfoque
                spread_radius=0,  # Raio de propagação
                color="#F5F5F5",  # Cor da sombra
            ),
            width=500,
            height=700,
            content=ft.Column(
                controls=[
                    ft.Text(
                        "Bem-vindo",
                        size=sizes["font_size"] * 2,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.WHITE
                    ),
                    ft.Text(
                        "Faça o login para entrar",
                        size=sizes["font_size"],
                        color=ft.Colors.WHITE70,
                        weight=ft.FontWeight.W_300
                    ),
                    ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                    self.email_input,
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    self.password_input,
                    self.error_text,
                    self.page.user_name_text,   # Invisible, sem uso
                    self.page.company_name_text_btn,   # Invisible, sem uso
                    ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                    self.login_button,
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    ft.TextButton(
                        content=ft.Text(value="Criar uma conta",
                                        color=ft.Colors.YELLOW_ACCENT_400),
                        on_click=lambda _: self.page.go('/signup'),
                    ),
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    ft.TextButton(
                        text="Voltar",
                        icon=ft.CupertinoIcons.BACK,
                        icon_color=ft.Colors.PRIMARY,
                        style=ft.ButtonStyle(
                            color=ft.Colors.YELLOW_ACCENT_400),
                        on_click=lambda _: self.page.go('/'),
                    )
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
        )

    def validate_form(self) -> Optional[str]:
        email = self.email_input.value
        email = email.strip().lower()

        if not email:
            return "Por favor, insira seu email"
        if not validate_email(email):
            return "Email inválido"

        self.email_input.value = email

        # ToDo: Passar esta responsabilidade para a classe Password
        password = self.password_input.value

        if len(password) < 8:
            return "A senha deve ter:\n• pelo menos 8 caracteres"

        return None

    async def handle_login(self, _):
        # Desabilita o botão imediatamente para evitar múltiplos cliques
        self.login_button.disabled = True
        self.login_button.update()

        # Detalhes de UX, com o estado de carregamento do botão
        try:
            # Faz a validação dos campos
            error = self.validate_form()
            if error:
                # Erro na validação dos campos, retorna sem fazer o login
                self.error_text.value = error
                self.error_text.visible = True
                self.error_text.update()
                return

            # Campos validados, segue com login
            # Oculta texto de mensagens de erro.
            self.error_text.visible = False
            self.error_text.update()

            result = await usuarios_controllers.handle_login_usuarios(
                email=self.email_input.value, password=self.password_input.value)

            if result["is_error"]:
                message_snackbar(
                    page=self.page, message=result["message"], message_type=MessageType.ERROR)
                return

            # Atualiza o estado do app com o novo usuário antes da navegação
            user = result["authenticated_user"]

            if user.empresa_id is None:
                await self.page.app_state.clear_empresa_data()
                return

            # Usuário tem empresa(s) registrada(s), obtem os dados da última empresa utilizada
            result = await empresas_controllers.handle_get_empresas(id=user.empresa_id)

            if result["is_error"]:
                message_snackbar(
                    page=self.page, message=result["message"], message_type=MessageType.ERROR)
                return

            cia: Empresa = result["empresa"]

            # Adiciona o empresa_id no state e publíca-a
            await self.page.app_state.set_empresa({
                "id": cia.empresa_id,
                "name": cia.name,
                "corporate_name": cia.corporate_name,
                "cnpj": cia.cnpj,
                "ie": cia.ie,
                "store_name": cia.store_name,
                "im": cia.im,
                "contact": cia.contact,
                "address": cia.address,
                "size": cia.size,
                "fiscal": cia.fiscal,
                "logo_url": cia.logo_url,
                "payment_gateway": cia.payment_gateway,
            })

            self.page.on_resized = None
            self.page.go('/home')

        finally:
            # Reabilita o botão independente do resultado
            self.login_button.disabled = False
            self.login_button.update()

    def page_resize(self, e):
        sizes = get_responsive_sizes(e.page.width)

        # Atualiza tamanhos dos inputs
        self.email_input.width = sizes["input_width"]
        self.email_input.text_size = sizes["font_size"]

        self.password_input.width = sizes["input_width"]
        self.password_input.text_size = sizes["font_size"]

        # Atualiza o botão
        icon_control = self.login_button.content.controls[0]
        icon_control.size = sizes["icon_size"]

        text_control = self.login_button.content.controls[1]
        text_control.size = sizes["font_size"]

        self.login_button.content.spacing = sizes["spacing"]
        self.login_button.width = sizes["button_width"]

        self.login_button.style = ft.ButtonStyle(
            color=ft.Colors.WHITE,
            side=ft.BorderSide(
                color=ft.Colors.PRIMARY,
                width=sizes["border_width"]
            ),
            padding=ft.padding.symmetric(
                horizontal=sizes["spacing"] * 2,
                vertical=sizes["spacing"]
            )
        )

        # Atualiza o container principal
        form_column = self.form.content
        form_column.controls[0].size = sizes["font_size"] * 2  # Título
        form_column.controls[1].size = sizes["font_size"]      # Subtítulo

        self.error_text.size = sizes["font_size"]

        # Atualiza o padding do container
        self.form.padding = ft.padding.all(sizes["form_padding"])

        self.form.update()

    def build(self) -> ft.Container:
        return self.form


def empresas_form(page: ft.Page):
    empresa_view = EmpresaView(page)
    form_container = empresa_view.build()

    async def save_form_empresa(e):
        form_data = empresa_view.get_form_data()  # Obtem os dados do formulário

        if id := page.app_state.empresa_form.get('id'):
            form_data["id"] = id

        print(f"Dados do formulário Empresas: {form_data}")  # Debug
        # ToDo: Implementar a lógica de salvar os dados da empresa
        # try:
        #     pass
        #     # Transferir arquivos do diretório upload como logo e (pfx, p12) para api NFCe e Bucket
        # except ValueError as e:
        #     logger.error(f"Erro de validação ao salvar os dados da empresa: {str(e)}")
        # except Exception as e:
        #     logger.error(f"Erro ao salvar os dados da empresa: {str(e)}")

    def exit_form_empresa(e):
        # ToDo: Apagar possíveis arquivos de logo e (pfx, p12) do diretório upload do sistema
        page.go('/home')

    # Adiciona os botões "Salvar" & "Cancelar"
    save_btn = ft.ElevatedButton("Salvar", on_click=save_form_empresa)
    exit_btn = ft.ElevatedButton("Cancelar", on_click=exit_form_empresa)

    return ft.Column(
        controls=[
            form_container,
            ft.Divider(height=5),
            ft.ResponsiveRow(
                controls=[save_btn, exit_btn],
                expand=True,
                alignment=ft.MainAxisAlignment.END,
                spacing=20,
                run_spacing=20,
            ),
        ],
    )
