import flet as ft

# ToDo: Este componente está sem uso, por enquanto!

class Carousel(ft.Column):
    def __init__(self, controls: list[ft.Control], height: int = 250, **kwargs):
        super().__init__(**kwargs)
        # Componente principal do Carousel
        self.carousel = ft.Row(
            height=height,
            scroll=ft.ScrollMode.HIDDEN,
            controls=controls
        )

        # Adiciona os controles principais ao layout da coluna
        self.controls.append(self.carousel)
        self.controls.append(
            ft.Row(
                alignment=ft.MainAxisAlignment.END,
                controls=[
                    ft.IconButton(
                        icon=ft.Icons.KEYBOARD_ARROW_LEFT,
                        on_click=self.move_backward
                    ),
                    ft.IconButton(
                        icon=ft.Icons.KEYBOARD_ARROW_RIGHT,
                        on_click=self.move_forward
                    ),
                ]
            )
        )

    def move_backward(self, e):
        self.carousel.scroll_to(delta=-500, duration=200, curve=ft.AnimationCurve.DECELERATE)
        self.update()

    def move_forward(self, e):
        self.carousel.scroll_to(delta=500, duration=200, curve=ft.AnimationCurve.DECELERATE)
        self.update()
