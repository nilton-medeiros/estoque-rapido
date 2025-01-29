import flet as ft


def sidebar_header(page: ft.Page):
    page.user_name_text.theme_style = ft.TextThemeStyle.BODY_LARGE
    page.company_name_text.theme_style = ft.TextThemeStyle.BODY_MEDIUM
    page.user_name_text.visible = True
    page.company_name_text.visible = True

    current_user = page.app_state.user
    user_photo = current_user['photo']

    print(":")
    print("================================================================================")
    print(f"Debug | photo: {current_user['photo']}")
    print("Debug | page.user_name_text:", page.user_name_text)
    print("Debug | page.company_name_text:", page.company_name_text)
    print("================================================================================")
    print(" ")


    user_avatar = ft.Container(
        image=ft.Image(
            # src="https://sistrom-global-bucket.s3.sa-east-1.amazonaws.com/estoquerapido/public/user_17b8c9059f03419b9e31f8e4d7a40f60-fundo-transp.png",
            src=f"images/avatars/{user_photo}",
            width=100,
            height=100,
            fit=ft.ImageFit.CONTAIN
        ),
        content=ft.Text(current_user['name'].iniciais),
        tooltip="Click para nova foto",
        bgcolor=ft.Colors.PRIMARY,
        alignment=ft.alignment.center,
        width=100,
        height=100,
        border_radius=ft.border_radius.all(100),
    )

    return ft.Container(
        content=ft.Column(
            controls=[
                user_avatar,
                page.user_name_text,
                page.company_name_text,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.padding.symmetric(vertical=20, horizontal=40),
        alignment=ft.alignment.center,
    )


def sidebar_content():
    return ft.Text("Sidebar Content")


def sidebar_footer():
    return ft.Text("Sidebar Footer")


def sidebar_container(page: ft.Page):
    sidebar = ft.Container(
        expand=True,
        bgcolor="#111418",
        border_radius=10,
        content=ft.Column(
            controls=[
                sidebar_header(page),
                sidebar_content(),
                sidebar_footer(),
            ]
        )
    )
    return sidebar
