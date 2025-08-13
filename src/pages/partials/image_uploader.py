import logging
import os
import base64
import mimetypes
from typing import Callable

import flet as ft

import src.controllers.bucket_controllers as bucket_controllers
from src.services import UploadFile
from src.shared.utils import MessageType, message_snackbar
from src.shared.utils.file_helpers import generate_unique_bucket_filename
from src.domains.shared.context.session import get_session_colors
from src.shared.utils.find_project_path import find_project_root

logger = logging.getLogger(__name__)

class ImageUploadHandler:
    """
    Encapsula a lógica de upload e exibição de imagens para formulários.
    """
    def __init__(
        self,
        page: ft.Page,
        image_frame: ft.Container,
        bucket_prefix: str,
        on_image_loaded: Callable[[], None] | None = None
    ):
        self.page = page
        self.image_frame = image_frame
        self.bucket_prefix = bucket_prefix
        self.on_image_loaded = on_image_loaded
        self.app_colors = get_session_colors(page)

        # State
        self.image_url: str | None = None
        self.is_web_url = False
        self.previous_image_url: str | None = None
        self.local_upload_path: str | None = None

    async def open_dialog(self, e=None):
        """Abre o diálogo de upload e processa o resultado."""
        self.image_frame.border = ft.border.all(color=self.app_colors["primary"], width=1)
        self.image_frame.update()

        upload_file_service = UploadFile(
            page=self.page,
            title_dialog="Selecionar Imagem",
            allowed_extensions=["png", "jpg", "jpeg", "svg"],
        )

        local_path = await upload_file_service.open_dialog()

        self.is_web_url = upload_file_service.is_url_web
        self.image_url = None # Reset image_url to prioritize new selection

        if self.is_web_url:
            self.image_url = upload_file_service.url_file
            self.local_upload_path = None
            if self.image_url:
                self._display_image_from_url(self.image_url)
        elif local_path:
            self.local_upload_path = local_path
            self._display_image_from_local_path(local_path)

        if self.on_image_loaded:
            self.on_image_loaded()

    def _display_image_from_url(self, url: str):
        """Exibe uma imagem a partir de uma URL."""
        image_control = ft.Image(
            src=url,
            error_content=ft.Text("Erro ao carregar URL!"),
            repeat=ft.ImageRepeat.NO_REPEAT,
            fit=ft.ImageFit.CONTAIN,
            border_radius=ft.border_radius.all(20),
        )
        self.image_frame.content = image_control
        self.image_frame.update()

    def _display_image_from_local_path(self, local_path: str):
        """Lê um arquivo local, converte para base64 e exibe."""
        project_root = find_project_root(__file__)
        img_file = project_root / local_path

        try:
            with open(img_file, "rb") as f_img:
                img_data = f_img.read()

            base64_data = base64.b64encode(img_data).decode('utf-8')
            image_control = ft.Image(
                src_base64=base64_data,
                error_content=ft.Text("Erro ao carregar (base64)!"),
                repeat=ft.ImageRepeat.NO_REPEAT,
                fit=ft.ImageFit.CONTAIN,
                border_radius=ft.border_radius.all(20),
            )
        except Exception as ex:
            logger.error(f"Erro ao ler arquivo de imagem {img_file} para base64: {ex}")
            image_control = ft.Image(error_content=ft.Text(f"Erro crítico: {ex}"))

        self.image_frame.content = image_control
        self.image_frame.update()

    def set_initial_image(self, image_url: str | None):
        """Define a imagem inicial ao carregar um formulário existente."""
        if image_url:
            self.image_url = image_url
            self.previous_image_url = image_url
            self._display_image_from_url(image_url)

    def send_to_bucket(self) -> bool:
        """Faz o upload do arquivo local para o bucket e atualiza o image_url."""
        if not self.local_upload_path:
            return False

        try:
            file_name_bucket = generate_unique_bucket_filename(original_filename=self.local_upload_path, prefix=self.bucket_prefix)
            uploaded_url = bucket_controllers.handle_upload_bucket(local_path=self.local_upload_path, key=file_name_bucket)

            if uploaded_url:
                self.image_url = uploaded_url
                return True
            else:
                self.image_url = self.previous_image_url
                message_snackbar(self.page, "Não foi possível carregar a imagem!", MessageType.ERROR)
                return False
        except (ValueError, RuntimeError) as e:
            msg = f"Erro ao carregar imagem: {str(e)}"
            message_snackbar(self.page, msg, MessageType.ERROR)
            logger.error(msg)
            return False
        finally:
            self.cleanup_local_file()

    def cleanup_local_file(self):
        """Remove o arquivo local temporário."""
        if self.local_upload_path:
            try:
                os.remove(self.local_upload_path)
                self.local_upload_path = None
            except OSError as e:
                logger.warning(f"Erro ao limpar arquivo temporário {self.local_upload_path}: {e}")

    def get_final_image_url(self) -> str | None:
        """Retorna a URL final da imagem a ser salva."""
        return self.image_url