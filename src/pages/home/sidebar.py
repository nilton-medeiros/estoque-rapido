import asyncio
import logging
import os
import flet as ft

from src.presentation.components.functionality_graphics import FiscalProgressBar, Functionalities
from src.controllers.user_controller import handle_update_photo_user
from src.services.aws.s3_file_manager import S3FileManager
from src.utils.gen_uuid import get_uuid
from src.utils.message_snackbar import MessageType, message_snackbar

logger = logging.getLogger(__name__)


def sidebar_header(page: ft.Page):
    page.user_name_text.theme_style = ft.TextThemeStyle.BODY_LARGE
    page.user_name_text.visible = True
    page.company_name_text_btn.theme_style = ft.TextThemeStyle.BODY_MEDIUM
    page.company_name_text_btn.visible = True

    current_user = page.app_state.user
    profile = ft.Text(
        value=current_user['profile'], theme_style=ft.TextThemeStyle.BODY_SMALL)
    user_photo = None

    if current_user['photo']:
        user_photo = ft.Image(
            src=current_user['photo'],
            error_content=ft.Text(current_user['name'].iniciais),
            repeat=ft.ImageRepeat.NO_REPEAT,
            fit=ft.ImageFit.FILL,
            border_radius=ft.border_radius.all(100),
            width=100,
            height=100,
        )
    else:
        user_photo = ft.Text(current_user['name'].iniciais)

    current_company = page.app_state.company

    if current_company["id"]:
        page.company_name_text_btn.tooltip = "Empresa selecionada"
    else:
        page.company_name_text_btn.tooltip = "Clique aqui e preencha os dados da empresa"

    status_text = ft.Text()
    progress_bar = ft.ProgressBar(visible=False)

    def show_image_dialog(e):
        user_avatar.bgcolor = ft.Colors.TRANSPARENT
        user_avatar.update()

        previous_user_photo = current_user['photo']

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
                cnpj = current_company["cnpj"]
                prefix = cnpj.raw_cnpj if cnpj else current_user["id"]
                file_uid = get_uuid()

                _, dot_extension = os.path.splitext(file_name)
                dot_extension = dot_extension.lower()

                file_s3_name = f"{prefix}/user_img_{file_uid}{dot_extension}"
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

                s3_manager = S3FileManager()
                s3_manager.upload(local_path=local_file, key=file_s3_name)

                photo_url = s3_manager.get_url()

                # Atualiza a foto do usuário
                result = await handle_update_photo_user(user_id=current_user["id"], photo=photo_url)

                # Debug:
                # print(" ")
                # print(" ")
                # print("DEBUG-154 ====================================================")
                # print(f"file_s3_name: {file_s3_name}")
                # print(f"local_file: {local_file}")
                # print(f"photo_url: {photo_url}")
                # print(f"result: {str(result)}")
                # print("DEBUG-154 ====================================================")
                # print(" ")
                # print(" ")

                if result["is_error"]:
                    # Photo não pode ser salva no database, remove do s3
                    s3_manager.delete(key=file_s3_name)
                else:
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
                            s3_manager.delete(key)

                    # Atualiza a foto na página
                    user_photo = ft.Image(
                        src=photo_url,
                        error_content=ft.Text(current_user['name'].iniciais),
                        repeat=ft.ImageRepeat.NO_REPEAT,
                        fit=ft.ImageFit.FILL,
                        border_radius=ft.border_radius.all(100),
                        width=100,
                        height=100,
                    )


                    user_avatar.content = user_photo
                    user_avatar.update()
                    user = result["user"]

                    await page.app_state.set_user({
                        "id": user.id,
                        "name": user.name,
                        "email": user.email,
                        "phone_number": user.phone_number,
                        "profile": user.profile,
                        "companies": user.companies,
                        "photo": user.photo,
                    })

                    page.pubsub.send_all("user_updated")

                color = MessageType.ERROR if result["is_error"] else MessageType.SUCCESS
                message_snackbar(
                    page=page, message=result["message"], message_type=color)

                # Limpa o arquivo local após o upload
                try:
                    os.remove(local_file)
                except:
                    pass  # Ignora erros na limpeza do arquivo

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
            print(f"Tipo alterado para: {image_type_dd.value}")
            url_field.visible = image_type_dd.value == "url"
            page.update()

        image_type_dd.on_change = type_changed

        def update_image(e):
            print(f"Atualizando imagem...")
            selected_type = image_type_dd.value
            if selected_type == "arquivo":
                pick_files_dialog.pick_files(
                    allow_multiple=False,
                    allowed_extensions=["png", "jpg", "jpeg", "svg"]
                )
            else:
                if url_field.value:
                    print(f"URL da imagem: {url_field.value}")
                    # Implementar lógica de atualização com URL
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

    def on_click_cpny_btn(e):
        page.go('/company/form')

    page.company_name_text_btn.on_click = on_click_cpny_btn

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
    current_company = page.app_state.company

    store = ft.Column(
        controls=[
            ft.Row(
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Text(value='Loja:',
                            theme_style=ft.TextThemeStyle.BODY_LARGE),
                    ft.Text(value=current_company['store_name'],
                            theme_style=ft.TextThemeStyle.BODY_MEDIUM),
                ],
            ),
            ft.Row(
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Text(value='CNPJ:',
                            theme_style=ft.TextThemeStyle.BODY_LARGE),
                    ft.Text(value=current_company['cnpj'],
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
                        value=current_company['ie'], theme_style=ft.TextThemeStyle.BODY_MEDIUM),
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

    def change_primary_color(e):
        e.page.theme.color_scheme.primary = e.control.data
        e.page.session.set("user_color", e.control.data)
        e.page.update()

    def on_click_business_btn(e):
        page.go('/company/form')

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
                            data='deeppurple',
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
                            data='purple',
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
                            data='indigo',
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
                            data='blue',
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
                            data='teal',
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
                            data='green',
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
                            data='yellow',
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
                            data='orange',
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
                            data='deeporange',
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
                            data='pink',
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
                            data='red',
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

    return sidebar
