import flet as ft

def main(page: ft.Page):
    # Configurações iniciais da página
    page.title = "Formulário campos de empresa"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    # Função para abrir a janela flutuante
    def open_popup(e):
        # Cria o conteúdo da janela flutuante
        popup_content = ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        value="Esta é uma janela flutuante!",
                        color=ft.colors.BLACK,
                        weight=ft.FontWeight.BOLD,
                        size=20,
                    ),
                    ft.ElevatedButton("Fechar", on_click=close_popup)
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=20
            ),
            width=300,
            height=200,
            bgcolor=ft.colors.WHITE,
            padding=20,
            border_radius=10,
            shadow=ft.BoxShadow(
                spread_radius=5,
                blur_radius=10,
                color=ft.colors.BLACK38
            )
        )

        # Adiciona o conteúdo ao overlay
        page.overlay.append(popup_content)
        page.update()

    # Função para fechar a janela flutuante
    def close_popup(e):
        # Remove o último widget adicionado ao overlay (a janela flutuante)
        if page.overlay:
            page.overlay.pop()
            page.update()

    # Botão para abrir a janela flutuante
    open_button = ft.ElevatedButton("Abrir Janela Flutuante", on_click=open_popup)

    # Adiciona o botão à página principal
    page.add(ft.Text("Página Principal!!!"), open_button)

# Executa o aplicativo
ft.app(target=main)