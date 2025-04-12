import asyncio
import logging
import os
import flet as ft

import src.controllers.bucket_controllers as bucket_controllers

from src.presentation.components.functionality_graphics import FiscalProgressBar, Functionalities
from src.domains.usuarios import handle_update_photo_usuarios, handle_update_color_usuarios
from src.shared import get_uuid, MessageType, message_snackbar

logger = logging.getLogger(__name__)


def sidebar_header(page: ft.Page):
    page.user_name_text.theme_style = ft.TextThemeStyle.BODY_LARGE
    page.user_name_text.visible = True
    page.company_name_text_btn.theme_style = ft.TextThemeStyle.BODY_MEDIUM
    page.company_name_text_btn.visible = True

    current_user = page.app_state.usuario
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

    current_company = page.app_state.empresa
    if current_company.get('id'):
        page.company_name_text_btn.tooltip = "Empresa selecionada"
    else:
        page.company_name_text_btn.tooltip = "Clique aqui e preencha os dados da empresa"

    status_text = ft.Text()
    progress_bar = ft.ProgressBar(visible=False)

    def show_image_dialog(e):
        user_avatar.bgcolor = ft.Colors.TRANSPARENT
        user_avatar.update()

        previous_user_photo = current_user['photo_url']

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
            on_result=handle_file_picker_result,
            on_upload=handle_upload_progress
        )

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
                prefix = None

                if cnpj := current_company.get('cnpj'):
                    prefix = cnpj.raw_cnpj
                else:
                    prefix = current_user.get("id")

                file_uid = get_uuid()

                _, dot_extension = os.path.splitext(file_name)
                dot_extension = dot_extension.lower()

                file_name_bucket = f"{prefix}/user_img_{file_uid}{dot_extension}"
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
                    result = await handle_update_photo_usuarios(id=current_user.get("id"), photo_url=avatar_url)

                    if result["is_error"]:
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
                        user_updated = result["usuario"]

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

                    page.app_state.set_usuario(user_updated.to_dict())

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

                color = MessageType.ERROR if result["is_error"] else MessageType.SUCCESS
                message_snackbar(
                    page=page, message=result["message"], message_type=color)

                page.close(dialog)

            except Exception as e:
                logger.error(f"Erro de upload: {str(e)}")
                message_snackbar(
                    page=page,
                    message=f"Erro de upload: {str(e)}",
                    message_type=MessageType.ERROR
                )
                page.close(dialog)

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
                    result = await handle_update_photo_usuarios(id=current_user["id"], photo_url=url_field.value)
                    if not result["is_error"]:
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
                                    await bucket_controllers.handle_delete_bucket(key)
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
                        usuario = result["usuario"]

                        page.app_state.set_usuario(usuario.to_dict())

                        page.pubsub.send_all("usuario_updated")

                    color = MessageType.ERROR if result["is_error"] else MessageType.SUCCESS
                    message_snackbar(
                        page=page, message=result["message"], message_type=color)
                    page.close(dialog)

        def close_dialog(e):
            page.close(dialog)
            if page.overlay:
                page.overlay.pop()
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
            # Se já existe uma empresa, seta a empresa atual para o form
            page.app_state.set_empresa_form(current_company)
        else:
            # Se não existe empresa, limpa o form
            page.app_state.clear_empresa_form_data()
        page.go('/empresas/form')

    page.company_name_text_btn.on_click = on_click_empresa_btn

    return ft.Container(
        content=ft.Column(
            controls=[
                photo_section,
                page.user_name_text,
                page.company_name_text_btn,
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
    current_company = page.app_state.empresa

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
                        value=current_company.get('ie',''), theme_style=ft.TextThemeStyle.BODY_MEDIUM),
                ],
            ),
        ]
    )

    circle_praphs = ft.Row(
        controls=[
            Functionalities(title='Estoque', value=1),
            Functionalities(title='Recebíveis', value=1),
            Functionalities(title='Pagamentos', value=0.5),
        ]
    )

    line_graphics = ft.Column(
        controls=[
            FiscalProgressBar(title='CADASTRO FISCAL', value=1),
            FiscalProgressBar(title='CETIFICADO', value=1),
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

    manual = ft.TextButton(
        text='MANUAL RÁPIDO',
        style=ft.ButtonStyle(color=ft.Colors.GREY),
        icon=ft.Icons.DOWNLOAD,
        icon_color=ft.Colors.GREY,
        url='https://drive.google.com/uc?export=download&id=1vHKz5-tKDC_HMwqaGYMbsAicGrKPwyFL',

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


def sidebar_footer(page: ft.Page):
    def logoff_user(e):
        page.go('/logout')

    async def change_primary_color(e):
        # Atualiza a cor primária da interface no thema do app
        e.page.theme.color_scheme.primary = e.control.data.get('primary')
        e.page.theme.color_scheme.primary_container = e.control.data.get('primary_container')

        user = page.app_state.usuario
        msg_error = None

        try:
            result = await handle_update_color_usuarios(id=user.get('id'), color=e.control.data)
            if result["is_error"]:
                msg_error = result["message"]
                return

            user.update({'user_color': e.control.data})
            page.app_state.set_usuario(user)

        except ValueError as e:
            logger.error(str(e))
            msg_error = f"Erro: {str(e)}"
        except RuntimeError as e:
            logger.error(str(e))
            msg_error = f"Erro no upload: {str(e)}"

        if msg_error:
            message_snackbar(page=page, message=msg_error,
                         message_type=MessageType.ERROR)
        e.page.update()

    def on_click_business_btn(e):
        page.go('/empresas/table')

    return ft.Container(
        padding=ft.padding.symmetric(vertical=20),
        content=ft.Row(
            controls=[
                ft.IconButton(
                    icon=ft.Icons.POWER_SETTINGS_NEW,
                    icon_color="white",
                    height=18,
                    on_click=logoff_user,
                ),
                ft.IconButton(
                    icon=ft.Icons.BUSINESS,
                    icon_color="white",
                    height=18,
                    on_click=on_click_business_btn,
                ),
                ft.IconButton(
                    icon=ft.Icons.GROUPS,
                    icon_color="white",
                    height=18,
                    # on_click=,
                ),
                ft.Container(
                    expand=True,
                ),
                ft.PopupMenuButton(
                    tooltip="Cor principal",
                    expand=True,
                    content=ft.Icon(
                        name=ft.Icons.COLOR_LENS_OUTLINED,
                        color=ft.Colors.PRIMARY,
                        size=22,
                    ),
                    items=[
                        ft.PopupMenuItem(
                            content=ft.Row(
                                controls=[
                                    ft.Container(
                                        height=10,
                                        width=10,
                                        bgcolor=ft.Colors.DEEP_PURPLE
                                    ),
                                    ft.Text(value='Deep Purple')
                                ]
                            ),
                            data={'primary': 'deeppurple', 'primary_container': 'deeppurple_200'},
                            on_click=change_primary_color,
                        ),
                        ft.PopupMenuItem(
                            content=ft.Row(
                                controls=[
                                    ft.Container(
                                        height=10,
                                        width=10,
                                        bgcolor=ft.Colors.PURPLE
                                    ),
                                    ft.Text(value='Purple')
                                ]
                            ),
                            data={'primary': 'purple', 'primary_container': 'purple_200'},
                            on_click=change_primary_color,
                        ),
                        ft.PopupMenuItem(
                            content=ft.Row(
                                controls=[
                                    ft.Container(
                                        height=10,
                                        width=10,
                                        bgcolor=ft.Colors.INDIGO
                                    ),
                                    ft.Text(value='Indigo')
                                ]
                            ),
                            data={'primary': 'indigo', 'primary_container': 'indigo_200'},
                            on_click=change_primary_color,
                        ),
                        ft.PopupMenuItem(
                            content=ft.Row(
                                controls=[
                                    ft.Container(
                                        height=10,
                                        width=10,
                                        bgcolor=ft.Colors.BLUE
                                    ),
                                    ft.Text(value='Blue (default)')
                                ]
                            ),
                            data={'primary': 'blue', 'primary_container': 'blue_200'},
                            on_click=change_primary_color,
                        ),
                        ft.PopupMenuItem(
                            content=ft.Row(
                                controls=[
                                    ft.Container(
                                        height=10,
                                        width=10,
                                        bgcolor=ft.Colors.TEAL
                                    ),
                                    ft.Text(value='Teal')
                                ]
                            ),
                            data={'primary': 'teal', 'primary_container': 'teal_200'},
                            on_click=change_primary_color,
                        ),
                        ft.PopupMenuItem(
                            content=ft.Row(
                                controls=[
                                    ft.Container(
                                        height=10,
                                        width=10,
                                        bgcolor=ft.Colors.GREEN
                                    ),
                                    ft.Text(value='Green')
                                ]
                            ),
                            data={'primary': 'green', 'primary_container': 'green_200'},
                            on_click=change_primary_color,
                        ),
                        ft.PopupMenuItem(
                            content=ft.Row(
                                controls=[
                                    ft.Container(
                                        height=10,
                                        width=10,
                                        bgcolor=ft.Colors.YELLOW
                                    ),
                                    ft.Text(value='Yellow')
                                ]
                            ),
                            data={'primary': 'yellow', 'primary_container': 'yellow_200'},
                            on_click=change_primary_color,
                        ),
                        ft.PopupMenuItem(
                            content=ft.Row(
                                controls=[
                                    ft.Container(
                                        height=10,
                                        width=10,
                                        bgcolor=ft.Colors.ORANGE
                                    ),
                                    ft.Text(value='Orange')
                                ]
                            ),
                            data={'primary': 'orange', 'primary_container': 'orange_200'},
                            on_click=change_primary_color,
                        ),
                        ft.PopupMenuItem(
                            content=ft.Row(
                                controls=[
                                    ft.Container(
                                        height=10,
                                        width=10,
                                        bgcolor=ft.Colors.DEEP_ORANGE
                                    ),
                                    ft.Text(value='Deep orange')
                                ]
                            ),
                            data={'primary': 'deeporange', 'primary_container': 'deeporange_200'},
                            on_click=change_primary_color,
                        ),
                        ft.PopupMenuItem(
                            content=ft.Row(
                                controls=[
                                    ft.Container(
                                        height=10,
                                        width=10,
                                        bgcolor=ft.Colors.PINK
                                    ),
                                    ft.Text(value='Pink')
                                ]
                            ),
                            data={'primary': 'pink', 'primary_container': 'pink_200'},
                            on_click=change_primary_color,
                        ),
                        ft.PopupMenuItem(
                            content=ft.Row(
                                controls=[
                                    ft.Container(
                                        height=10,
                                        width=10,
                                        bgcolor=ft.Colors.RED
                                    ),
                                    ft.Text(value='Red')
                                ]
                            ),
                            data={'primary': 'red', 'primary_container': 'red_200'},
                            on_click=change_primary_color,
                        ),
                    ],
                ),
            ]
        )
    )


def sidebar_container(page: ft.Page):
    sidebar = ft.Container(
        col={"xs": 0, "md": 5, "lg": 4, "xxl": 3},
        expand=True,
        bgcolor="#111418",
        border_radius=10,
        content=ft.Column(
            controls=[
                sidebar_header(page),
                sidebar_content(page),
                sidebar_footer(page),
            ]
        )
    )
    print("Retornando sidebar")
    return sidebar
