import flet as ft
import shutil
from pathlib import Path
import os

class UploadDialog(ft.AlertDialog):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.content_padding = 0
        self.actions_padding = 0
        self.scrollable = True
        self.files_progress = ft.ListView()
        self.pick_files_dialog = ft.FilePicker(on_result=self.pick_files, on_upload=self.upload_file_progress)
        self.page.overlay.append(self.pick_files_dialog)
        self.content = ft.Container(
            width=400,
            bgcolor=ft.Colors.WHITE,
            padding=ft.padding.all(30),
            border_radius=ft.border_radius.all(15),
            shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.INDIGO_800),
            content=ft.Column(
                controls=[
                    ft.Text(
                        value='Carregar arquivos',
                        size=24,
                        weight=ft.FontWeight.BOLD
                    ),
                    ft.Container(
                        bgcolor=ft.Colors.GREY_50,
                        padding=ft.padding.all(20),
                        border_radius=ft.border_radius.all(10),
                        border=ft.border.all(width=2, color=ft.Colors.GREY_200),
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.CENTER,
                            controls=[
                                ft.Icon(name=ft.Icons.CLOUD_UPLOAD),
                                ft.Text(value='Selecionar arquivos'),
                            ]
                        ),
                        on_click=self.pick_files_dialog.pick_files,
                    ),
                    self.files_progress,
                ]
            )
        )
        self.uploads = {}

    def upload_file_progress(self, e: ft.FilePickerUploadEvent):
        on_upload = self.uploads.get(e.file_name)

        if not on_upload:
            progress_bar = ft.ListTile(
                title=ft.Text(value=e.file_name),
                subtitle=ft.ProgressBar(value=e.progress),
                trailing=ft.Icon(name=ft.Icons.CANCEL)
            )
            self.files_progress.controls.append(progress_bar)
            self.uploads.update({e.file_name: progress_bar})
        else:
            on_upload.subtitle.value = e.progress
            on_upload.trailing.name = ft.Icons.VERIFIED if e.progress == 1 else ft.Icons.CANCEL

        self.files_progress.update()

    def pick_files(self, e: ft.FilePickerResultEvent):
        if not e.files: return

        for file in e.files:
            filename = file.name

            if self.page.web:
                # Faz o upload do arquivo para o diretório definido em "upload_dir"
                self.pick_files_dialog.upload(
                    files=[
                        ft.FilePickerUploadFile(
                            name=filename,
                            upload_url=self.page.get_upload_url(filename, 60),
                            method="PUT"
                        )
                    ]
                )
            else:
                abs_path = Path(__file__).parent
                shutil.copy(file.path, os.path.join(abs_path, 'uploads'))
                self.files_progress.controls.append(
                    ft.ListTile(title=ft.Text(value=file.name), trailing=ft.Icon(name=ft.Icons.VERIFIED))
                )
                self.files_progress.update()



def main(page: ft.Page):
    page.bgcolor  = ft.Colors.INDIGO
    page.theme_mode = ft.ThemeMode.LIGHT
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    uploads = {}

    def upload_file_progress(e: ft.FilePickerUploadEvent):
        on_upload = uploads.get(e.file_name)

        if not on_upload:
            progress_bar = ft.ListTile(
                title=ft.Text(value=e.file_name),
                subtitle=ft.ProgressBar(value=e.progress),
                trailing=ft.Icon(name=ft.Icons.CANCEL)
            )
            files_progress.controls.append(progress_bar)
            uploads.update({e.file_name: progress_bar})
        else:
            on_upload.subtitle.value = e.progress
            on_upload.trailing.name = ft.Icons.VERIFIED if e.progress == 1 else ft.Icons.CANCEL

        files_progress.update()

    def pick_files(e: ft.FilePickerResultEvent):
        if not e.files: return

        for file in e.files:
            filename = file.name

            if page.web or page.platform in (ft.PagePlatform.ANDROID, ft.PagePlatform.IOS):
                # Faz o upload do arquivo para o diretório definido em "upload_dir"
                pick_files_dialog.upload(
                    files=[
                        ft.FilePickerUploadFile(
                            name=filename,
                            upload_url=page.get_upload_url(filename, 60),
                            method="PUT"
                        )
                    ]
                )
            else:
                abs_path = Path(__file__).parent
                shutil.copy(file.path, os.path.join(abs_path, 'uploads'))
                files_progress.controls.append(
                    ft.ListTile(title=ft.Text(value=file.name), trailing=ft.Icon(name=ft.Icons.VERIFIED))
                )
                files_progress.update()

    pick_files_dialog = ft.FilePicker(on_result=pick_files, on_upload=upload_file_progress)
    page.overlay.append(pick_files_dialog)

    files_progress = ft.ListView()

    layout = ft.Container(
        width=400,
        bgcolor=ft.Colors.WHITE,
        padding=ft.padding.all(30),
        border_radius=ft.border_radius.all(15),
        shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.INDIGO_800),
        content=ft.Column(
            controls=[
                ft.Text(
                    value='Carregar arquivos',
                    size=24,
                    weight=ft.FontWeight.BOLD
                ),
                ft.Container(
                    bgcolor=ft.Colors.GREY_50,
                    padding=ft.padding.all(20),
                    border_radius=ft.border_radius.all(10),
                    border=ft.border.all(width=2, color=ft.Colors.GREY_200),
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        controls=[
                            ft.Icon(name=ft.Icons.CLOUD_UPLOAD),
                            ft.Text(value='Selecionar arquivos'),
                        ]
                    ),
                    on_click=pick_files_dialog.pick_files,
                ),
                files_progress,
            ]
        )
    )

    page.add(layout)


if __name__ == '__main__':
    ft.app(target = main, upload_dir = 'uploads')
