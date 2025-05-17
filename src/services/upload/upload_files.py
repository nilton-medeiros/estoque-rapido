import asyncio
import logging
import os
from typing import Optional
import flet as ft

logger = logging.getLogger(__name__)


class UploadFile:
    def __init__(self, page: ft.Page, title_dialog: str, allowed_extensions: list, upload_timeout: int = 60) -> None:
        self.page = page
        self.title_dialog = title_dialog
        self.allowed_extensions = allowed_extensions
        self.upload_timeout = upload_timeout
        self.is_url_web = False
        self.url_file = None
        self.upload_completed = False
        self.progress_bar:ft.ProgressBar = ft.ProgressBar(visible=False)
        self.picker_dialog:ft.FilePicker = ft.FilePicker(
            on_result=self._pick_files_result, # type: ignore
            on_upload=self._pick_files_progress,
        )
        self.dialog = self._create_dialog()
        self.message_error = None
        self.future = None  # Future para sinalizar conclusão

        # Adiciona o FilePicker ao overlay da página
        self.page.overlay.append(self.picker_dialog)

    async def open_dialog(self) -> Optional[str]:
        """Abre o diálogo e aguarda a conclusão do upload."""
        self.future = asyncio.get_event_loop().create_future()
        self.page.open(self.dialog)
        try:
            await asyncio.wait_for(self.future, timeout=self.upload_timeout)
        except asyncio.TimeoutError:
            self.message_error = "Tempo limite excedido para upload"
            self.close_dialog()
        return self.url_file

    def _create_dialog(self) -> ft.AlertDialog:
        """Cria o diálogo para upload de arquivos ou inserção de URL."""
        return ft.AlertDialog(
            title=ft.Text(self.title_dialog),
            content=ft.Column(
                controls=[
                    ft.RadioGroup(
                        content=ft.Row(
                            [
                                ft.Radio(value="file", label="Arquivo"),
                                ft.Radio(value="url", label="URL"),
                            ]
                        ),
                        on_change=self._on_source_change,
                    ),
                    ft.TextField(label="URL do arquivo", visible=False),
                    self.progress_bar,
                ],
                width=350,
                height=200,
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=self.cancel_dialog),
                ft.TextButton("Confirmar", on_click=self.update_file_source),
            ],
        )

    def _on_source_change(self, e):
        """Atualiza a interface com base na fonte selecionada (arquivo ou URL)."""
        self.is_url_web = e.control.value == "url"
        self.dialog.content.controls[1].visible = self.is_url_web # type: ignore
        self.page.update()

    def update_file_source(self, e):
        if self.is_url_web:
            url = self.dialog.content.controls[1].value.strip() # type: ignore
            if not url:
                self.message_error = "URL não pode estar vazia"
                self.future.set_result(None) # type: ignore
                return
            self.url_file = url
            self.future.set_result(url) # type: ignore
        else:
            self.picker_dialog.pick_files(
                allow_multiple=False,
                allowed_extensions=self.allowed_extensions,
            )

    def cancel_dialog(self, e):
        self.message_error = "Obtenção do Logo cancelado pelo usuário"
        self.future.set_result(None) # type: ignore
        self.close_dialog()

    def close_dialog(self):
        self.page.close(self.dialog)
        self.page.update()

    async def _pick_files_result(self, e: ft.FilePickerResultEvent) -> None:
        if not e.files:
            self.future.set_result(None) # type: ignore
            return
        await self._upload_files(e.files)
        self.future.set_result(self.url_file) # type: ignore
        self.close_dialog()

    async def _upload_files(self, files: list) -> None:
        try:
            self.progress_bar.visible = True
            self.progress_bar.value = 0
            self.progress_bar.update()

            file_name = files[0].name
            upload_url = self.page.get_upload_url(file_name, 60)
            upload_files = [
                ft.FilePickerUploadFile(
                    name=file_name,
                    upload_url=upload_url
                )
            ]
            self.picker_dialog.upload(upload_files)
            while not self.upload_completed:
                await asyncio.sleep(0.1)
            self.url_file = f"uploads/{file_name}"
            self.is_url_web = False
            max_retries = 10
            retry_count = 0
            while not os.path.exists(self.url_file) and retry_count < max_retries:
                await asyncio.sleep(1)
                retry_count += 1
            if not os.path.exists(self.url_file):
                self.message_error = f"Arquivo {self.url_file} não foi encontrado após {max_retries} tentativas"
                raise FileNotFoundError(self.message_error)
        except Exception as e:
            self.message_error = f"Erro ao fazer upload do arquivo: {str(e)}"
            logger.error(self.message_error)

    def _pick_files_progress(self, e: ft.FilePickerUploadEvent) -> None:
        if e.progress == 1:
            self.upload_completed = True
            self.progress_bar.visible = False
        else:
            self.upload_completed = False
            self.progress_bar.visible = True
            self.progress_bar.value = e.progress
        self.progress_bar.update()
