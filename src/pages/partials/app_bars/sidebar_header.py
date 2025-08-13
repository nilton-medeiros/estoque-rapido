import flet as ft
import os
import asyncio
import logging
from typing import Callable

import src.controllers.bucket_controllers as bucket_controllers
from src.domains.shared.context.session import get_current_user, get_current_company
import src.domains.usuarios.controllers.usuarios_controllers as user_controllers
from src.domains.usuarios.models.usuarios_model import Usuario
from src.services.states.app_state_manager import AppStateManager
from src.shared.utils.messages import message_snackbar, MessageType
from src.shared.utils.file_helpers import generate_unique_bucket_filename

logger = logging.getLogger(__name__)

def create_sidebar_header(page: ft.Page) -> ft.Container:
    """
    Cria o container do cabeçalho da barra lateral com a foto do usuário, nome, perfil e nome da empresa.
    Inclui funcionalidade de upload de imagem de perfil.
    """
    current_user = get_current_user(page)

    # Se o usuário não está logado, retorna um cabeçalho placeholder
    if not current_user:
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(name=ft.Icons.ACCOUNT_CIRCLE, size=100, color=ft.Colors.WHITE),
                    ft.Text("Usuário não logado", theme_style=ft.TextThemeStyle.BODY_LARGE, color=ft.Colors.WHITE),
                    ft.Text("Selecione uma empresa", theme_style=ft.TextThemeStyle.BODY_MEDIUM, color=ft.Colors.WHITE),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.symmetric(vertical=20, horizontal=20),
            alignment=ft.alignment.center,
        )

    profile = ft.Text(
        value=current_user.profile.value,
        theme_style=ft.TextThemeStyle.BODY_SMALL,
        color=ft.Colors.WHITE
    )

    # Configuração da foto do usuário
    user_photo = _create_user_photo(current_user)

    _update_company_text_btn(page)

    # Componentes para upload
    status_text = ft.Text()
    progress_bar = ft.ProgressBar(visible=False)

    # Container da foto com ícone de câmera
    user_avatar, camera_icon = _create_user_avatar(page, user_photo, status_text, progress_bar)

    # Configuração inicial dos componentes de texto
    app_state: AppStateManager = page.app_state  # type: ignore [attr-defined]
    app_state.user_name_text.value = current_user.name.primeiro_e_ultimo_nome
    app_state.user_name_text.theme_style = ft.TextThemeStyle.BODY_LARGE
    app_state.user_name_text.visible = True
    app_state.company_name_text_btn.style = ft.ButtonStyle(
        text_style=ft.TextStyle(
            color=ft.Colors.WHITE, size=14, weight=ft.FontWeight.BOLD)
    )
    app_state.company_name_text_btn.visible = True

    # Ação do botão de empresa
    app_state.company_name_text_btn.on_click = lambda e: _on_click_empresa_btn(page)

    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Column(
                    controls=[user_avatar, camera_icon],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=0,
                ),
                app_state.user_name_text,
                profile,
                app_state.company_name_text_btn,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.padding.symmetric(vertical=20, horizontal=20),
        alignment=ft.alignment.center,
    )

def _create_user_photo(current_user: Usuario) -> ft.Control:
    """Cria o componente de foto do usuário ou iniciais como fallback."""
    user_name = current_user.name
    photo_url = current_user.photo_url

    if photo_url:
        return ft.Image(
            src=photo_url,
            error_content=ft.Icon(ft.Icons.PERSON_OFF_OUTLINED), # Fallback em caso de erro no carregamento da imagem
            repeat=ft.ImageRepeat.NO_REPEAT,
            fit=ft.ImageFit.COVER,
            border_radius=ft.border_radius.all(100),
            width=100,
            height=100,
        )
    # Se não tem foto, mostra as iniciais. Se não tem nome, mostra um ícone.
    return ft.Text(user_name.iniciais) if user_name else ft.Icon(ft.Icons.PERSON)

def _update_company_text_btn(page: ft.Page):
    """Atualiza o texto e tooltip do botão de empresa."""
    current_company = get_current_company(page)
    app_state: AppStateManager = page.app_state  # type: ignore [attr-defined]

    if current_company.get('id'):
        app_state.company_name_text_btn.tooltip = "Empresa selecionada"  # type: ignore [attr-defined]
        cia_name = current_company.get('trade_name') or current_company.get('corporate_name', 'EMPRESA NÃO DEFINIDA')
        app_state.company_name_text_btn.text = cia_name  # type: ignore [attr-defined]
    else:
        app_state.company_name_text_btn.tooltip = "Clique aqui e preencha os dados da empresa"  # type: ignore [attr-defined]
        app_state.company_name_text_btn.text = "NENHUMA EMPRESA SELECIONADA"  # type: ignore [attr-defined]

def _on_click_empresa_btn(page: ft.Page):
    """Gerencia o clique no botão de empresa."""
    current_company = get_current_company(page)

    if current_company.get('id'):
        page.go('/home/empresas/grid')
    else:
        page.app_state.clear_form_data()  # type: ignore [attr-defined]
        page.go('/home/empresas/form/principal')

def _create_user_avatar(page: ft.Page, user_photo: ft.Control, status_text: ft.Text, progress_bar: ft.ProgressBar) -> tuple[ft.Container, ft.Container]:
    """Cria o container da foto do usuário com o ícone de câmera e funcionalidade de upload."""
    user_avatar = ft.Container(
        content=user_photo,
        bgcolor=ft.Colors.TRANSPARENT,
        padding=10,
        alignment=ft.alignment.center,
        width=100,
        height=100,
        border_radius=ft.border_radius.all(100),
        on_click=lambda e: _show_image_dialog(page, user_avatar, status_text, progress_bar),
    )

    camera_icon = ft.Container(
        content=ft.Icon(
            name=ft.Icons.ADD_A_PHOTO_OUTLINED,
            size=20,
            color=ft.Colors.GREY_400,
        ),
        margin=ft.margin.only(top=-15),
        ink=True,
        on_hover=lambda e: _on_hover_icon(e, user_avatar),
        on_click=lambda e: _show_image_dialog(page, user_avatar, status_text, progress_bar),
        border_radius=ft.border_radius.all(20),
        padding=8,
    )

    return user_avatar, camera_icon

def _on_hover_icon(e: ft.ControlEvent, user_avatar: ft.Container):
    """Gerencia o efeito de hover no ícone da câmera."""
    icon_container = e.control
    icon_container.content.color = ft.Colors.PRIMARY if e.data == "true" else ft.Colors.GREY_400
    user_avatar.bgcolor = ft.Colors.PRIMARY if e.data == "true" else ft.Colors.TRANSPARENT

    # Verifica se os controles estão associados à página antes de atualizar
    if icon_container.page:
        icon_container.update()
    # else:
    #     logger.warning("icon_container não está associado à página, ignorando update")

    if user_avatar.page:
        user_avatar.update()
    # else:
    #     logger.warning("user_avatar não está associado à página, ignorando update")

def _show_image_dialog(page: ft.Page, user_avatar: ft.Container, status_text: ft.Text, progress_bar: ft.ProgressBar):
    """Exibe o diálogo para upload de imagem de perfil."""
    current_user = get_current_user(page)
    previous_user_photo = current_user.photo_url

    # Cria o FilePicker
    pick_files_dialog = ft.FilePicker(
        on_result=lambda e: asyncio.run(_handle_file_picker_result(e, page, user_avatar, status_text, progress_bar, pick_files_dialog, dialog)),
        on_upload=_handle_upload_progress(status_text, progress_bar)
    )
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
            if url_field.value and url_field.value.strip() and current_user.id:
                result = user_controllers.handle_update_photo(id=current_user.id, photo_url=url_field.value)
                _handle_update_result(page, user_avatar, result, previous_user_photo, dialog)
                # A função _handle_update_result agora fecha o diálogo

    def close_dialog(e = None):
        if pick_files_dialog in page.overlay:
            page.overlay.remove(pick_files_dialog)
        page.close(dialog)

    dialog = ft.AlertDialog(
        modal=True,
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

    page.open(dialog)

async def _handle_file_picker_result(e: ft.FilePickerResultEvent, page: ft.Page, user_avatar: ft.Container, status_text: ft.Text, progress_bar: ft.ProgressBar, pick_files_dialog: ft.FilePicker, dialog: ft.AlertDialog):
    """Gerencia o resultado do FilePicker."""
    if not e.files:
        status_text.value = "Nenhum arquivo selecionado"
        status_text.update()
        return

    status_text.value = f"Arquivo selecionado: {e.files[0].name}"
    status_text.update()
    current_user = get_current_user(page)
    previous_user_photo = current_user.photo_url

    try:
        file_name = e.files[0].name
        upload_url = page.get_upload_url(file_name, 60)
        upload_files = [ft.FilePickerUploadFile(name=file_name, upload_url=upload_url)]
        upload_complete = False

        def on_upload_completed(e: ft.FilePickerUploadEvent):
            nonlocal upload_complete
            if e.progress == 1:
                upload_complete = True

        pick_files_dialog.on_upload = on_upload_completed  # type: ignore [attr-defined]
        pick_files_dialog.upload(upload_files)

        while not upload_complete:
            await asyncio.sleep(0.1)

        local_file = f"Uploads/{file_name}"
        file_name_bucket = generate_unique_bucket_filename(original_filename=local_file, prefix="usuarios")

        max_retries = 10
        retry_count = 0
        while not os.path.exists(local_file) and retry_count < max_retries:
            await asyncio.sleep(0.1)
            retry_count += 1

        if not os.path.exists(local_file):
            logger.debug(f"Arquivo {local_file} não foi encontrado após {max_retries} tentativas")
            raise FileNotFoundError(f"Arquivo {local_file} não foi encontrado após {max_retries} tentativas")

        avatar_url = bucket_controllers.handle_upload_bucket(local_path=local_file, key=file_name_bucket)
        if not avatar_url:
            page.close(dialog)
            message_snackbar(
                page=page,
                message="Erro: URL da imagem não foi gerada corretamente",
                message_type=MessageType.ERROR,
                duration=4000,
                center=True
            )
            return

        if not current_user.id:
            # Condição improvável
            logger.warning("current_id.id não está definido")
            return
        result = user_controllers.handle_update_photo(id=current_user.id, photo_url=avatar_url)

        # Se a atualização no banco de dados falhar, remove o arquivo recém-enviado do bucket.
        if result.get("status") == "error":
            try:
                bucket_controllers.handle_delete_bucket(key=file_name_bucket)
            except Exception as exc_delete:
                logger.error(f"Falha ao limpar arquivo do bucket após erro no DB: {exc_delete}")

        _handle_update_result(page, user_avatar, result, previous_user_photo, dialog)

        try:
            os.remove(local_file)
        except:
            pass

    except Exception as exc:
        logger.error(f"Erro de upload: {str(exc)}")
        message_snackbar(
            page=page,
            message=f"Erro de upload: {str(exc)}",
            message_type=MessageType.ERROR,
            duration=4000,
            center=True
        )
        page.close(dialog)

def _handle_upload_progress(status_text: ft.Text, progress_bar: ft.ProgressBar) -> Callable[[ft.FilePickerUploadEvent], None]:
    """Gerencia o progresso do upload."""
    def on_upload(e: ft.FilePickerUploadEvent) -> None:
        if e.progress == 1:
            progress_bar.visible = False
            status_text.value = "Upload concluído!"
            status_text.update()
        else:
            progress_bar.visible = True
            progress_bar.value = e.progress
            progress_bar.update()
    return on_upload

def _handle_update_result(page: ft.Page, user_avatar: ft.Container, result: dict, previous_user_photo: str | None, dialog: ft.AlertDialog):
    """Gerencia o resultado da atualização da foto do usuário."""
    if result["status"] == "error":
        page.close(dialog)
        message_snackbar(
            page=page,
            message=result["message"],
            message_type=MessageType.ERROR,
            duration=4000,
            center=True
        )
        return

    user_updated = result["data"]["usuario"]
    user_photo = ft.Image(
        src=user_updated.photo_url or None,
        error_content=ft.Text(user_updated.name.iniciais),
        repeat=ft.ImageRepeat.NO_REPEAT,
        fit=ft.ImageFit.FILL,
        border_radius=ft.border_radius.all(100),
        width=100,
        height=100,
    )

    user_avatar.content = user_photo
    user_avatar.update()
    page.app_state.set_usuario(user_updated)  # type: ignore [attr-defined]

    if previous_user_photo and previous_user_photo != user_updated.photo_url:
        parts = previous_user_photo.split("public/")
        if len(parts) > 1:
            try:
                bucket_controllers.handle_delete_bucket(parts[1])
            except Exception as e:
                logger.error(f"Erro ao deletar imagem antiga do bucket: {e}")

    page.close(dialog)

    message_snackbar(
        page=page,
        message="Avatar carregado com sucesso!",
        message_type=MessageType.SUCCESS,
        duration=4000,
        center=True
    )
