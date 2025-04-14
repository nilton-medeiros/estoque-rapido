import asyncio
import logging
import os
from typing import Optional
import validators
import flet as ft

logger = logging.getLogger(__name__)


class UploadFile:
    def __init__(self, page: ft.Page, title_dialog: str, allowed_extensions: list, upload_timeout: int = 60) -> None:
        self.page = page
        self.title_dialog = title_dialog
        self.allowed_extensions = allowed_extensions
        # Adiciona um tempo limite de upload como parâmetro configurável em segundos
        self.upload_timeout = upload_timeout
        self.is_url_web = False
        # url do arquivo no diretório uploads/ do projeto (aplicativo) ou url da web
        self.url_file = None
        self.upload_completed = False
        self.progress_bar = ft.ProgressBar(visible=False)
        self.picker_dialog = ft.FilePicker(
            on_result=self._pick_files_result,
            on_upload=self._pick_files_progress,
        )
        self.dialog = self._create_dialog()
        self.message_error = None

        # Adiciona o FilePicker ao overlay da página
        self.page.overlay.append(self.picker_dialog)

        # Abrindo o diálogo para o usuário na page
        self.page.open(self.dialog)

    def _validate_url(self, url: str) -> bool:
        """Validar URL web antes do upload"""
        try:
            # Verifica se a URL é válida e acessível
            return validators.url(url) and validators.contains_url(url) is not None
        except Exception as e:
            logger.error(f"Erro ao validar URL: {str(e)}")
            return False

    def get_url_error(self) -> Optional[str]:
        """Recuperar mensagem de erro de upload, se disponível"""
        return self.message_error or ""

    def _create_dialog(self) -> ft.AlertDialog:
        # Dropdown para escolher origem do arquivo (local ou URL web)
        url_field = ft.TextField(
            label="URL do arquivo",
            width=300,
            visible=False,
        )

        def on_change_file_source(e):
            url_field.visible = file_source.value == "url"
            self.is_url_web = file_source.value == "url"
            self.page.update()

        file_source = ft.Dropdown(
            label="Origem do arquivo",
            width=300,
            options=[
                ft.dropdown.Option("aquivo", "Arquivo Local"),
                ft.dropdown.Option("url", "URL da Web"),
            ],
            value='arquivo',
            on_change=on_change_file_source,
        )

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(self.title_dialog),
            content=ft.Column(
                controls=[
                    file_source,
                    url_field,
                    self.progress_bar,
                ],
                width=350,
                height=200,
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=self.cancel_dialog),
                ft.TextButton("Selecionar", on_click=self.update_file_source),
            ]
        )

        return dialog

    def update_file_source(self, e):
        if self.is_url_web:
            # Acessa o campo de URL
            url = self.dialog.controls[1].value.strip()

            if not url:
                self.message_error = "URL não pode estar vazia"
                return

            if not self._validate_url(url):
                self.message_error = "URL inválida ou inacessível"
                return

            self.url_file = url
        else:
            self.picker_dialog.pick_files(
                allow_multiple=False,
                allowed_extensions=self.allowed_extensions,
            )
            # Self.url_file definido na def _upload_files

    def cancel_dialog(self, e):
        self.message_error = "Obtenção do Logo cancelado pelo usuário"
        self.close_dialog()

    def close_dialog(self):
        self.page.close(self.dialog)
        self.page.update()

    async def _pick_files_result(self, e: ft.FilePickerResultEvent) -> None:
        if not e.files:
            return   # Nenhum arquivo selecionado
        # Inicia o upload do arquivo
        await self._upload_files(e.files)
        self.close_dialog()

    async def _upload_files(self, files: list) -> None:
        try:
            self.progress_bar.visible = True
            self.progress_bar.value = 0
            self.progress_bar.update()

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
            self.picker_dialog.upload(upload_files)

            # Aguarda até que o upload seja concluído
            while not self.upload_completed:
                # Pequena pausa para não sobrecarregar o CPU
                await asyncio.sleep(0.1)

            # Agora que o upload está concluído, podemos salvar a url do arquivo local no servidor do app
            self.url_file = f"uploads/{file_name}"
            self.is_url_web = False

            # Adiciona uma verificação extra para garantir que o arquivo existe em uploads/
            max_retries = 10
            retry_count = 0
            while not os.path.exists(self.url_file) and retry_count < max_retries:
                await asyncio.sleep(1)
                retry_count += 1

            if not os.path.exists(self.url_file):
                self.message_error = f"Arquivo {self.url_file} não foi encontrado após {max_retries} tentativas"
                logger.debug(self.message_error)
                raise FileNotFoundError(self.message_error)

        except Exception as e:
            self.message_error = f"Erro ao fazer upload do arquivo: {str(e)}"
            logger.error(self.message_error)

    def _pick_files_progress(self, e: ft.FilePickerUploadEvent) -> None:
        # Atualiza a barra de progresso
        if e.progress == 1:
            self.upload_completed = True
            self.progress_bar.visible = False
        else:
            self.upload_completed = False
            self.progress_bar.visible = True
            self.progress_bar.value = e.progress

        self.progress_bar.update()
