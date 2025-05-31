import flet as ft

def main(page: ft.Page):
    page.title = "Images Example"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 50
    page.update()

    img = ft.Image(
        src=f"/icons/icon-512.png",
        width=100,
        height=100,
        fit=ft.ImageFit.CONTAIN,
    )
    images = ft.Row(expand=1, wrap=False, scroll="always")

    page.add(img, images)

    image_url = f"https://cdn-cosmos.bluesoft.com.br/products/7500435156547"

    img_contanier = ft.Container(  # Container para a imagem da produto
        width=100,
        height=100,
        border_radius=ft.border_radius.all(
            10),
        border=ft.border.all(
            1, ft.Colors.OUTLINE) if not image_url else None,
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        alignment=ft.alignment.center,
        content=ft.Image(
            src=f"{image_url}",
            fit=ft.ImageFit.COVER,
            width=100,
            height=100,
            border_radius=ft.border_radius.all(
                10),
            error_content=ft.Icon(
                ft.Icons.IMAGE_NOT_SUPPORTED_OUTLINED, size=30, color=ft.Colors.ERROR)
        ) if image_url else ft.Icon(ft.Icons.CATEGORY_OUTLINED, size=40, opacity=0.5)
    )


    images.controls.append(img_contanier)

    images.controls.append(
        ft.Image(
            src=f"https://picsum.photos/200/200?{11}",
            width=200,
            height=200,
            fit=ft.ImageFit.NONE,
            repeat=ft.ImageRepeat.NO_REPEAT,
            border_radius=ft.border_radius.all(10),
            error_content=ft.Text("Image 2"),
        )
    )

    images.controls.append(
        ft.Image(
            src=f"https://<bucket>.s3.<region>.amazonaws.com/estoquerapido/public/bkKAjpVLEdXyqlCrnziCih6H5WJ3/user_img_573fb1fd83694697a597095be2d107ca.jpg",
            width=200,
            height=200,
            fit=ft.ImageFit.CONTAIN,
            repeat=ft.ImageRepeat.NO_REPEAT,
            border_radius=ft.border_radius.all(10),
            error_content=ft.Text("Image 3"),
        )
    )

    images.controls.append(
        ft.Image(
            src=f"https://<bucket>.s3.<region>.amazonaws.com/estoquerapido/public/bkKAjpVLEdXyqlCrnziCih6H5WJ3/user_img_6c7335a1d3604b088b93c12897da19f3.JPG",
            width=200,
            height=200,
            fit=ft.ImageFit.COVER,
            repeat=ft.ImageRepeat.NO_REPEAT,
            border_radius=ft.border_radius.all(10),
            error_content=ft.Text("Image 4"),
        )
    )

    images.controls.append(
        ft.Image(
            src=f"https://<bucket>.s3.<region>.amazonaws.com/estoquerapido/public/bkKAjpVLEdXyqlCrnziCih6H5WJ3/user_img_f31b0323a63c46f389c65547f280161d.jpg",
            width=200,
            height=200,
            fit=ft.ImageFit.FILL,
            repeat=ft.ImageRepeat.NO_REPEAT,
            border_radius=ft.border_radius.all(10),
            error_content=ft.Text("Image 5"),
        )
    )

    images.controls.append(
        ft.Image(
            src=f"https://<bucket>.s3.<region>.amazonaws.com/estoquerapido/public/bkKAjpVLEdXyqlCrnziCih6H5WJ3/user_img_f62e2d06847046f38a98feb653d3317d.jpg",
            width=200,
            height=200,
            fit=ft.ImageFit.CONTAIN,
            repeat=ft.ImageRepeat.NO_REPEAT,
            border_radius=ft.border_radius.all(10),
            error_content=ft.Text("Image 6"),
        )
    )

    page.update()

ft.app(target=main, view=ft.AppView.WEB_BROWSER)
