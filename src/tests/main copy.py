import flet as ft


class SaveSelectFile2(ft.Row):
    def __init__(self, tipo, nome=None, tamanho=None):
        '''
        tipo  == path: seleciona uma pasta (retorna o caminho completo da pasta selecionada)
        tipo  == file: seleciona um arquivo (retorna o caminho completo do arquivo selecionado)
        tipo  == save: salva um arquivo (retorna o caminho completo do arquivo, junto com seu nome)

        '''
        super().__init__()
        self.nome = nome
        self.pick_files_dialog = ft.FilePicker(on_result=self.pick_files_result)
        self.tamanho_Texto = 500
        self.selected_files = ft.Text('', selectable=True, color='white')
        self._value = self.selected_files.value
        self.tipo = tipo
        self.visible = True
        self.wrap = True
        self.width = tamanho
        self.alignment = 'start'

        if tipo == 'file':
            if self.nome is None:
                self.nome = 'Selecione o arquivo'
            self.controls = [
                ft.TextButton(
                    self.nome,
                    icon=ft.Icons.UPLOAD_FILE,
                    on_click=self.Selecionar_arquivo,
                    # bgcolor = 'white,0.0',
                    # expand=True
                ),
                self.selected_files,
            ]
        elif tipo == 'path':
            if self.nome is None:
                self.nome = 'Selecione a pasta'
            self.controls = [
                ft.TextButton(
                    self.nome,
                    icon=ft.Icons.FOLDER,
                    on_click=self.Selecionar_pasta,
                    # bgcolor = 'white,0.0',
                    # expand=True
                ),
                self.selected_files,
            ]
        elif tipo == 'save':
            if self.nome is None:
                self.nome = 'Digite o nome do arquivo'
            self.controls = [
                ft.TextButton(
                    self.nome,
                    icon=ft.Icons.SAVE,
                    on_click=self.Save1,
                    # bgcolor = 'white,0.0',
                    # expand=True
                ),
                self.selected_files,

            ]
        self.controls.append(self.pick_files_dialog)

    def pick_files_result(self, e: ft.FilePickerResultEvent):
        print(f"e.files: {e.files}")  # Adicionando print para verificar e.files
        if e.files:
            print(f"e.files[0]: {e.files[0]}")  # Adicionando print para verificar e.files[0]

        if self.tipo == 'file':
            self.selected_files.value = e.files[0].path if e.files else "Cancelled!"
        elif self.tipo == 'path':
            self.selected_files.value = e.path if e.path else "Cancelled!"

        elif self.tipo == 'save':
            self.selected_files.value = e.path if e.path else "Cancelled!"

        self.selected_files.update()
        self._value = self.selected_files.value
        self.update()
        print(f"Selected file path: {self._value}")  # Adicionando print para verificar o valor final

    def Selecionar_arquivo(self, _):
        self.pick_files_dialog.pick_files(allow_multiple=True)

    def Selecionar_pasta(self, _):
        self.pick_files_dialog.get_directory_path_async(dialog_title='askdjahs', initial_directory=r'D:\baixados\programas_python\TabelaMandado\baixaryoutube\baixar_do_youtube\build\web')

    def Save1(self, _):
        self.pick_files_dialog.save_file()

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, valor):
        self._value = valor
        self.selected_files.value = valor
        self.selected_files.update()


def main(page: ft.Page):
    upload = SaveSelectFile2(tipo="file")
    page.add(upload)  # Adicione o SaveSelectFile2 à página
    page.add(upload.pick_files_dialog)  # Adicione o FilePicker à página

    def on_click(_):
        upload.Selecionar_arquivo(_)
        page.update()
        print(f"Value: {upload.value}")

    page.add(ft.ElevatedButton("Selecionar Arquivo", on_click=on_click))

if __name__ == '__main__':
    ft.app(target=main)
