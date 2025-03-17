import flet as ft


def main(page: ft.Page):
    # Configurações iniciais da página
    page.title = "Exemplo de Janela Flutuante"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    # Variável para armazenar o popup
    popup_content = None

    # Função para atualizar a posição do popup
    def update_popup_position():
        nonlocal popup_content
        if popup_content and page.window.width and page.window.height:
            '''
            A responsividade não está sendo tratada aqui.
            Para tornar o popup responsivo, manipular popup_content.width e popup_content.height
            e cada um dos controles dentro de popup_content.
            '''
            popup_width = popup_content.width
            popup_height = popup_content.height
            popup_content.left = (page.width - popup_width) / 2
            popup_content.top = (page.height - popup_height) / 2
            page.update()

    # Função para abrir a janela flutuante
    def open_popup(e):
        nonlocal popup_content
        # Cria o conteúdo da janela flutuante
        popup_content = ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        value="Esta é uma janela flutuante!",
                        color=ft.Colors.BLACK,
                        weight=ft.FontWeight.BOLD,
                        size=20,
                    ),
                    ft.ElevatedButton("Fechar", on_click=close_popup)
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=20
            ),
            width=600,
            height=200,
            bgcolor=ft.Colors.TEAL_400,
            padding=20,
            border_radius=10,
            shadow=ft.BoxShadow(
                spread_radius=5,
                blur_radius=10,
                color=ft.Colors.BLACK38
            ),
            alignment=ft.alignment.center,
        )

        # Adiciona o conteúdo ao overlay
        page.overlay.append(popup_content)
        update_popup_position()  # Centraliza ao abrir
        page.update()

    # Função para fechar a janela flutuante
    def close_popup(e):
        if page.overlay:
            page.overlay.pop()
            page.update()

    # Listener para redimensionamento da janela
    def on_resize(e):
        update_popup_position()

    page.on_resized = on_resize

    # Botão para abrir a janela flutuante
    open_button = ft.ElevatedButton(
        "Abrir Janela Flutuante", on_click=open_popup)

    # Adiciona o botão à página principal
    page.add(ft.Text("Página Principal!!!"), open_button)


# Executa o aplicativo
ft.app(target=main)
