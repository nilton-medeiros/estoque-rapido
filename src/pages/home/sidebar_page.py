import asyncio
import logging
import os
import flet as ft

import src.controllers.bucket_controllers as bucket_controllers
import src.domains.usuarios.controllers.usuarios_controllers as user_controllers

from src.presentation.components import FiscalProgressBar, Functionalities
from src.shared.utils import get_uuid, MessageType, message_snackbar
from src.shared.config import get_app_colors

logger = logging.getLogger(__name__)


def sidebar_header(page: ft.Page):
    page.user_name_text.theme_style = ft.TextThemeStyle.BODY_LARGE  # type: ignore [attr-defined]
    page.user_name_text.visible = True  # type: ignore [attr-defined]
    page.company_name_text_btn.theme_style = ft.TextThemeStyle.BODY_MEDIUM  # type: ignore [attr-defined]
    page.company_name_text_btn.visible = True  # type: ignore [attr-defined]

    current_user = page.app_state.usuario  # type: ignore [attr-defined]
    profile = ft.Text(
        value=current_user['profile'], theme_style=ft.TextThemeStyle.BODY_SMALL)
    user_photo = None

    if current_user['photo_url']:
        user_photo = ft.Image(
            src=current_user['photo_url'],
            error_content=ft.Text(current_user['name'].iniciais),
            repeat=ft.ImageRepeat.NO_REPEAT,
            fit=ft.ImageFit.COVER,
            border_radius=ft.border_radius.all(100),
            width=100,
            height=100,
        )
    else:
        user_photo = ft.Text(current_user['name'].iniciais)

    current_company = page.app_state.empresa  # type: ignore
    cia_name = None
    if current_company.get('id'):
        page.company_name_text_btn.tooltip = "Empresa selecionada"  # type: ignore
        cia_name = current_company.get(
            'trade_name') or current_company.get('corporate_name', 'EMPRESA NÃO DEFINIDA')
        page.company_name_text_btn.text = cia_name  # type: ignore
    else:
        page.company_name_text_btn.tooltip = "Clique aqui e preencha os dados da empresa"  # type: ignore
        page.company_name_text_btn.text = "NENHUMA EMPRESA SELECIONADA"  # type: ignore

    # page.company_name_text_btn.update()

    status_text = ft.Text()
    progress_bar = ft.ProgressBar(visible=False)

    def show_image_dialog(e):
        user_avatar.bgcolor = ft.Colors.TRANSPARENT
        user_avatar.update()

        previous_user_photo = current_user['photo_url']

        async def upload_file(files):
            try:
                progress_bar.visible = True
                progress_bar.value = 0
                progress_bar.update()

                file_name = files[0].name
                # Gera uma URL assinada para upload (válida por 60 segundos)
                upload_url = page.get_upload_url(file_name, 60)

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

                def on_upload_completed(e: ft.FilePickerUploadEvent):
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
                file_uid = get_uuid()
                _, dot_extension = os.path.splitext(file_name)
                dot_extension = dot_extension.lower()

                prefix = "usuarios"
                file_name_bucket = f"{prefix}/{current_user['id']}_img_{file_uid}{dot_extension}"
                local_file = f"uploads/{file_name}"

                # Adiciona uma verificação extra para garantir que o arquivo existe
                max_retries = 10
                retry_count = 0
                while not os.path.exists(local_file) and retry_count < max_retries:
                    # Espera meio segundo entre tentativas
                    await asyncio.sleep(0.5)
                    retry_count += 1

                if not os.path.exists(local_file):
                    logger.debug(
                        f"Arquivo {local_file} não foi encontrado após {max_retries} tentativas")
                    raise FileNotFoundError(
                        f"Arquivo {local_file} não foi encontrado após {max_retries} tentativas")

                msg_snack = "Avatar carregado com sucesso!"
                message_type = MessageType.INFO
                is_success = True
                user_updated = None

                try:
                    avatar_url = bucket_controllers.handle_upload_bucket(
                        local_path=local_file, key=file_name_bucket)

                    # Verificar se o avatar_url é válido antes de continuar
                    if not avatar_url:
                        message_snackbar(
                            page=page,
                            message="Erro: URL da imagem não foi gerada corretamente",
                            message_type=MessageType.ERROR
                        )
                        page.close(dialog)
                        return

                    # Agora que temos uma URL válida, atualizar o usuário
                    result = user_controllers.handle_update_photo(id=current_user.get("id"), photo_url=avatar_url)

                    if result["status"] == "error":
                        message_type = MessageType.ERROR
                        msg_snack = result["message"]
                        is_success = False
                        # Photo não pode ser salva no database, remove do Bucket Storage a nova se não for a mesma anterior
                        if not previous_user_photo or previous_user_photo != avatar_url:
                            try:
                                bucket_controllers.handle_delete_bucket(
                                    key=file_name_bucket)
                            except Exception as e:
                                logger.error(f"{e}")
                    else:
                        user_updated = result["data"]["usuario"]

                except ValueError as e:
                    logger.error(str(e))
                    msg_snack = f"Erro: {str(e)}"
                    message_type = MessageType.ERROR
                    is_success = False
                except RuntimeError as e:
                    logger.error(str(e))
                    msg_snack = f"Erro no upload: {str(e)}"
                    message_type = MessageType.ERROR
                    is_success = False

                # Limpa o arquivo local após o upload
                try:
                    os.remove(local_file)
                except:
                    pass  # Ignora erros na limpeza do arquivo

                message_snackbar(page=page, message=msg_snack,
                                 message_type=message_type)

                # Nova foto salva no database, remover a antiga do Bucket Storage se existir
                if is_success:
                    # Atualiza a foto na página
                    user_photo = ft.Image(
                        src=avatar_url,
                        error_content=ft.Text(current_user['name'].iniciais),
                        repeat=ft.ImageRepeat.NO_REPEAT,
                        fit=ft.ImageFit.FILL,
                        border_radius=ft.border_radius.all(100),
                        width=100,
                        height=100,
                    )

                    user_avatar.content = user_photo
                    user_avatar.update()

                    page.app_state.set_usuario(  # type: ignore
                        user_updated.to_dict())  # type: ignore

                    # Remover a foto anterior do bucket se não for a mesma
                    if previous_user_photo and previous_user_photo != avatar_url:
                        # String completa
                        url = previous_user_photo
                        # Dividindo a string pelo termo "public/"
                        parts = url.split("public/")
                        # Extraindo a parte desejada (key)
                        key = parts[1]
                        # Excluíndo do bucket
                        if key:
                            try:
                                bucket_controllers.handle_delete_bucket(key)
                            except Exception as e:
                                logger.error(f"{e}")


                color = MessageType.SUCCESS
                msg = "Avatar carregado com sucesso!"
                if result["status"] == "error":
                    color = MessageType.ERROR
                    msg = result["message"]

                message_snackbar(page=page, message=msg, message_type=color)

                page.close(dialog)

            except Exception as e:
                logger.error(f"Erro de upload: {str(e)}")
                message_snackbar(
                    page=page,
                    message=f"Erro de upload: {str(e)}",
                    message_type=MessageType.ERROR
                )
                page.close(dialog)

        async def handle_file_picker_result(e: ft.FilePickerResultEvent):
            if not e.files:
                status_text.value = "Nenhum arquivo selecionado"
                status_text.update()
                return

            # Atualiza o texto com o nome do arquivo selecionado
            status_text.value = f"Arquivo selecionado: {e.files[0].name}"
            status_text.update()

            # Inicia o upload do arquivo
            await upload_file(e.files)

        def handle_upload_progress(e: ft.FilePickerUploadEvent):
            # Atualiza a barra de progresso
            if e.progress == 1:
                progress_bar.visible = False
                status_text.value = "Upload concluído!"
            else:
                progress_bar.visible = True
                progress_bar.value = e.progress

            status_text.update()
            progress_bar.update()

        # Cria o FilePicker
        pick_files_dialog = ft.FilePicker(
            on_result=handle_file_picker_result,  # type: ignore
            on_upload=handle_upload_progress
        )

        # Adiciona o FilePicker ao overlay da página
        page.overlay.append(pick_files_dialog)

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
            page.update()

        image_type_dd.on_change = type_changed

        async def update_image(e):
            selected_type = image_type_dd.value
            if selected_type == "arquivo":
                pick_files_dialog.pick_files(
                    allow_multiple=False,
                    allowed_extensions=["png", "jpg", "jpeg", "svg"]
                )
            else:
                if url_field.value and url_field.value.strip():
                    result = user_controllers.handle_update_photo(id=current_user["id"], photo_url=url_field.value)
                    if result["status"] == "success":
                        # Nova foto salva no database, remover a antiga do s3 se existir
                        if previous_user_photo:
                            # String completa
                            url = previous_user_photo
                            # Dividindo a string pelo termo "public/"
                            parts = url.split("public/")
                            # Extraindo a parte desejada (key)
                            key = parts[1]
                            # Excluíndo do bucket
                            if key:
                                try:
                                    bucket_controllers.handle_delete_bucket(
                                        key)
                                except Exception as e:
                                    logger.error(f"{e}")

                        # Atualiza a foto na página
                        user_photo = ft.Image(
                            src=url_field.value,
                            error_content=ft.Text(
                                current_user['name'].iniciais),
                            repeat=ft.ImageRepeat.NO_REPEAT,
                            fit=ft.ImageFit.FILL,
                            border_radius=ft.border_radius.all(100),
                            width=100,
                            height=100,
                        )

                        user_avatar.content = user_photo
                        user_avatar.update()
                        usuario = result["data"]["usuario"]

                        page.app_state.set_usuario(  # type: ignore
                            usuario.to_dict())

                    color = MessageType.SUCCESS
                    msg = "Avatar carregado com sucesso!"
                    if result["status"] == "error":
                        color = MessageType.ERROR
                        msg = result["message"]

                    message_snackbar(page=page, message=msg, message_type=color)
                    page.close(dialog)

        def close_dialog(e):
            # Mark the dialog to be closed
            dialog.open = False

            # Remove the FilePicker from the overlay.
            # It was added using page.overlay.append(pick_files_dialog).
            # Using .remove() is more explicit than .pop().
            if pick_files_dialog in page.overlay:
                page.overlay.remove(pick_files_dialog)

            # Send all changes (dialog closing, overlay modification) in a single update
            page.update()

        # Criando o diálogo
        dialog = ft.AlertDialog(
            modal=True,  # Garante que o diálogo bloqueie interações com a página
            title=ft.Text("Selecionar Imagem de Perfil"),
            content=ft.Column(
                controls=[
                    image_type_dd,
                    url_field,
                    status_text,
                    progress_bar,
                ],
                height=150,
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=close_dialog),
                ft.TextButton("Selecionar", on_click=update_image),
            ],
        )

        # Abrindo o diálogo
        page.open(dialog)

    # Criamos uma função para atualizar a cor do ícone
    def on_hover_icon(e):
        icon_container = e.control
        icon_container.content.color = ft.Colors.PRIMARY if e.data == "true" else ft.Colors.GREY_400
        icon_container.update()
        user_avatar.bgcolor = ft.Colors.PRIMARY if e.data == "true" else ft.Colors.TRANSPARENT
        user_avatar.update()

    # Container do ícone com hover effect
    camera_icon = ft.Container(
        content=ft.Icon(
            name=ft.Icons.ADD_A_PHOTO_OUTLINED,
            size=20,
            color=ft.Colors.GREY_400,
        ),
        margin=ft.margin.only(top=-15),
        ink=True,
        on_hover=on_hover_icon,
        on_click=show_image_dialog,
        # Opcional: adiciona um border radius para melhorar o efeito ink
        border_radius=ft.border_radius.all(20),
        padding=8,  # Opcional: adiciona um padding para aumentar a área clicável
    )

    user_avatar = ft.Container(
        content=user_photo,
        bgcolor=ft.Colors.TRANSPARENT,
        padding=10,
        alignment=ft.alignment.center,
        width=100,
        height=100,
        border_radius=ft.border_radius.all(100),
        on_click=show_image_dialog,  # Também permite clicar na imagem
    )

    photo_section = ft.Column(
        controls=[
            user_avatar,
            camera_icon
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=0,
    )

    def on_click_empresa_btn(e):
        if current_company.get('id'):
            # Se já existe uma empresa, redireciona para a grade de empresas
            page.go('/home/empresas/grid')
        else:
            # Se não existe empresa, limpa o form
            page.app_state.clear_form_data()  # type: ignore
            page.go('/home/empresas/form/principal')

    page.company_name_text_btn.on_click = on_click_empresa_btn  # type: ignore

    return ft.Container(
        content=ft.Column(
            controls=[
                photo_section,
                page.user_name_text,  # type: ignore
                page.company_name_text_btn,  # type: ignore
                status_text,
                progress_bar,
                profile,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.padding.symmetric(vertical=20, horizontal=40),
        alignment=ft.alignment.center,
    )


def sidebar_content(page: ft.Page):
    current_company = page.app_state.empresa  # type: ignore

    store = ft.Column(
        controls=[
            ft.Row(
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Text(value='Loja:',
                            theme_style=ft.TextThemeStyle.BODY_LARGE),
                    ft.Text(value=current_company.get('store_name', 'LOJA NÃO DEFINIDA'),
                            theme_style=ft.TextThemeStyle.BODY_MEDIUM),
                ],
            ),
            ft.Row(
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Text(value='CNPJ:',
                            theme_style=ft.TextThemeStyle.BODY_LARGE),
                    ft.Text(value=current_company.get('cnpj', ''),
                            theme_style=ft.TextThemeStyle.BODY_MEDIUM),
                ],
            ),
            ft.Row(
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Text(value='I.E.:',
                            theme_style=ft.TextThemeStyle.BODY_LARGE),
                    ft.Text(
                        value=current_company.get('ie', ''), theme_style=ft.TextThemeStyle.BODY_MEDIUM),
                ],
            ),
        ]
    )

    circle_praphs = ft.Row(
        controls=[
            Functionalities(title='Estoque', value=1),
            Functionalities(title='Recebíveis', value=0.5),
            Functionalities(title='Pagamentos', value=0),
        ]
    )

    line_graphics = ft.Column(
        controls=[
            FiscalProgressBar(title='CADASTRO FISCAL', value=0),
            FiscalProgressBar(title='CETIFICADO', value=0.5),
            FiscalProgressBar(title='NFC-e', value=1),
        ],
        alignment=ft.MainAxisAlignment.START,
        spacing=0,
    )

    check_list = ft.Column(
        controls=[
            ft.ListTile(
                leading=ft.Icon(name=ft.Icons.CHECK,
                                color=ft.Colors.PRIMARY),
                title=ft.Text(
                    value='Lista 1', theme_style=ft.TextThemeStyle.BODY_MEDIUM),
                bgcolor='#111418',
            ),
            ft.ListTile(
                leading=ft.Icon(name=ft.Icons.CHECK,
                                color=ft.Colors.PRIMARY),
                title=ft.Text(value='Lista 2',
                              theme_style=ft.TextThemeStyle.BODY_MEDIUM),
                bgcolor='#111418',
            ),
            ft.ListTile(
                leading=ft.Icon(name=ft.Icons.CHECK,
                                color=ft.Colors.PRIMARY),
                title=ft.Text(value='Lista 3',
                              theme_style=ft.TextThemeStyle.BODY_MEDIUM),
                bgcolor='#111418',
            ),
            ft.ListTile(
                leading=ft.Icon(name=ft.Icons.CHECK,
                                color=ft.Colors.PRIMARY),
                title=ft.Text(value='Lista 4',
                              theme_style=ft.TextThemeStyle.BODY_MEDIUM),
                bgcolor='#111418',
            ),
            ft.ListTile(
                leading=ft.Icon(name=ft.Icons.CHECK,
                                color=ft.Colors.PRIMARY),
                title=ft.Text(value='Lista 5',
                              theme_style=ft.TextThemeStyle.BODY_MEDIUM),
                bgcolor='#111418',
            ),
        ],
        alignment=ft.MainAxisAlignment.START,
        spacing=0,
    )

    # ToDo: Criar um manual para o Estoque Rápido e atribuir o link do S3 do manual pdf
    manual = ft.TextButton(
        text='MANUAL RÁPIDO',
        style=ft.ButtonStyle(color=ft.Colors.GREY),
        icon=ft.Icons.DOWNLOAD,
        icon_color=ft.Colors.GREY,
        # url='https://drive.google.com/uc?export=download&id=1vHKz5-tKDC_HMwqaGYMbsAicGrKPwyFL',
        # https://sites.google.com/site/gdocs2direct/?pli=1
    )

    return ft.Container(
        bgcolor=ft.Colors.BLACK12,
        padding=ft.padding.all(20),
        expand=True,
        content=ft.Column(
            scroll=ft.ScrollMode.AUTO,
            controls=[
                store,
                ft.Divider(height=30),
                circle_praphs,
                ft.Divider(height=30),
                line_graphics,
                ft.Divider(height=30),
                check_list,
                ft.Divider(height=30),
                manual,
            ]
        )
    )


class PopupColorItem(ft.PopupMenuItem):
    def __init__(self, color: str, name: str):
        super().__init__()
        # super() tras o self.page por herança
        self.content = ft.Row(
            controls=[
                ft.Icon(name=ft.Icons.COLOR_LENS_OUTLINED, color=color),
                ft.Text(name),
            ],
        )
        self.on_click = self.seed_color_changed
        self.data: str = color

    def seed_color_changed(self, e):
        self.page.theme = self.page.dark_theme = ft.Theme(  # type: ignore
            color_scheme_seed=self.data)  # type: ignore
        user = self.page.app_state.usuario  # type: ignore
        msg_error = None
        colors = get_app_colors(self.data)
        try:
            result = user_controllers.handle_update_user_colors(id=user.get('id'), colors=colors)
            if result["status"] == "error":
                # Reverter a mudança de tema se a atualização falhar? Opcional.
                # page.theme = page.dark_theme = ft.Theme(color_scheme_seed=user.get('user_colors', {}).get('primary', 'blue'))
                # page.update()
                msg_error = result["message"]
                message_snackbar(page=self.page, message=msg_error,  # type: ignore
                                 message_type=MessageType.ERROR)
                return  # Não continua se houve erro

            # Atualiza o estado local ANTES de atualizar a UI globalmente
            # type: ignore  # Pega o dicionário atual
            user_dict = self.page.app_state.usuario  # type: ignore
            # Atualiza as cores no dicionário
            user_dict['user_colors'] = colors
            # type: ignore  # Atualiza o estado
            self.page.app_state.set_usuario(user_dict)  # type: ignore

        except ValueError as e:
            logger.error(str(e))
            msg_error = f"Erro: {str(e)}"
        except RuntimeError as e:
            logger.error(str(e))
            # Provavelmente um erro de digitação, deveria ser "Erro na atualização"
            msg_error = f"Erro no upload: {str(e)}"

        if msg_error:
            message_snackbar(page=self.page, message=msg_error,  # type: ignore
                             message_type=MessageType.ERROR)
        self.page.update()  # type: ignore


def sidebar_footer(page: ft.Page):
    def handle_icon_hover(e):
        """Muda o bgcolor do container no hover."""
        if isinstance(e.control, ft.Container):
            e.control.bgcolor = ft.Colors.with_opacity(
                0.1, ft.Colors.WHITE) if e.data == "true" else ft.Colors.TRANSPARENT
            e.control.update()

    icon_container_props = {
        "width": 40,
        "height": 40,
        "border_radius": ft.border_radius.all(20),
        "ink": True,
        "bgcolor": ft.Colors.TRANSPARENT,
        "alignment": ft.alignment.center,
        "on_hover": handle_icon_hover,
    }

    return ft.Container(
        padding=ft.padding.symmetric(vertical=10, horizontal=10),
        content=ft.Row(
            controls=[
                ft.Container(
                    **icon_container_props,
                    content=ft.Icon(ft.Icons.BUSINESS, color="white", size=22),
                    tooltip="Empresas",
                    on_click=lambda _: page.go('/home/empresas/grid'),
                ),
                ft.Container(
                    **icon_container_props,
                    content=ft.Icon(ft.Icons.GROUPS, color="white", size=22),
                    tooltip="Usuários",
                    on_click=lambda _: page.go('/home/usuarios/grid'),
                ),
                ft.Container(
                    **icon_container_props,
                    content=ft.Icon(ft.Icons.ASSIGNMENT_OUTLINED,
                                    color="white", size=22),
                    tooltip="Categorias de produtos" if page.app_state.empresa.get( # type: ignore [attr: defined]
                        'id') else "Categorias de produtos indisponíveis: Selecione uma empresa primeiro.",
                    on_click=lambda _: page.go('/home/produtos/categorias/grid'),
                    disabled=False if page.app_state.empresa.get( # type: ignore [attr: defined]
                        'id') else True,
                ),
                ft.Container(
                    **icon_container_props,
                    content=ft.Icon(ft.Icons.SHOPPING_BAG_OUTLINED,
                                    color="white", size=22),
                    tooltip="Produtos" if page.app_state.empresa.get( # type: ignore [attr: defined]
                        'id') else "Produtos indisponíveis: Selecione uma empresa primeiro.",
                    on_click=lambda _: page.go('/home/produtos/grid'),
                    disabled=False if page.app_state.empresa.get( # type: ignore [attr: defined]
                        'id') else True,
                ),
                ft.Container(
                    **icon_container_props,
                    content=ft.Icon(ft.Icons.FACT_CHECK_OUTLINED,
                                    color="white", size=22),
                    tooltip="Estoque" if page.app_state.empresa.get( # type: ignore [attr: defined]
                        'id') else "Estoque indisponíveis: Selecione uma empresa primeiro.",
                    disabled=False if page.app_state.empresa.get( # type: ignore [attr: defined]
                        'id') else True,
                ),
                ft.Container(
                    **icon_container_props,
                    content=ft.Icon(ft.Icons.POINT_OF_SALE_OUTLINED,
                                    color="white", size=22),
                    tooltip="Pedidos" if page.app_state.empresa.get( # type: ignore [attr: defined]
                        'id') else "Pedidos indisponíveis: Selecione uma empresa primeiro.",
                    on_click=lambda _: page.go('/home/pedidos/grid'),
                    disabled=False if page.app_state.empresa.get( # type: ignore [attr: defined]
                        'id') else True,
                ),
                ft.PopupMenuButton(
                    icon=ft.Icons.COLOR_LENS_OUTLINED,
                    items=[
                        PopupColorItem(color='deeppurple', name='Deep purple'),
                        PopupColorItem(color='purple', name='Purple'),
                        PopupColorItem(color='indigo', name='Indigo'),
                        PopupColorItem(color='blue', name='Blue (padrão)'),
                        PopupColorItem(color='teal', name='Teal'),
                        PopupColorItem(color='green', name='Green'),
                        PopupColorItem(color='yellow', name='Yellow'),
                        PopupColorItem(color='orange', name='Orange'),
                        PopupColorItem(color='deeporange', name='Deep orange'),
                        PopupColorItem(color='pink', name='Pink'),
                        PopupColorItem(color='red', name='Red'),
                    ],
                ),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            spacing=10,
            scroll=ft.ScrollMode.AUTO,  # Enable horizontal scrolling
        ),
    )

def sidebar_container(page: ft.Page):
    """Container Esquerdo vertical na Home page do usuário"""
    page.data = page.route  # Armazena a rota atual em `page.data` para uso pela função `page.back()` de navegação.

    sidebar = ft.Container(
        col={"xs": 0, "md": 5, "lg": 4, "xxl": 3},
        expand=True,
        bgcolor="#111418",
        border_radius=10,
        content=ft.Column(
            # Garante que o footer não seja espremido se o conteúdo crescer
            controls=[
                sidebar_header(page),
                # Conteúdo principal expansível
                ft.Container(content=sidebar_content(page), expand=True),
                sidebar_footer(page),  # Footer com altura fixa
            ]
        )
    )
    return sidebar
