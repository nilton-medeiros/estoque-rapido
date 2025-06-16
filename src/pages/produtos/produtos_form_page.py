import logging
import os
import base64
import mimetypes

from datetime import datetime, UTC, timedelta
from typing import Any

import flet as ft

import src.shared.config.globals as app_globals

import src.controllers.bucket_controllers as bucket_controllers
import src.domains.categorias.controllers.categorias_controllers as category_controllers
import src.domains.produtos.controllers.produtos_controllers as product_controllers

from src.domains.produtos.models import Produto, ProdutoStatus
from src.pages.partials import build_input_field
from src.services import UploadFile, fetch_product_info_by_ean, ImageDownloader
from src.shared.utils.money_numpy import Money
from src.shared.utils import  show_banner, message_snackbar, MessageType, get_uuid, format_datetime_to_utc_minus_3
from src.shared.utils.find_project_path import find_project_root
from src.shared.config import get_app_colors
from src.pages.partials.monetary_field import MonetaryTextField

logger = logging.getLogger(__name__)


class ProdutoForm:
    def __init__(self, page: ft.Page):
        self.page = page
        self.empresa_logada = page.app_state.empresa  # type: ignore [attr-defined]
        self.data = page.app_state.form_data  # type: ignore [attr-defined]
        # Imagem do produto
        self.image_url: str | None = None
        self.is_image_url_web = False
        self.previous_image_url: str | None = None
        self.local_upload_file: str | None = None
        # Campos de redimencionamento do formulário
        self.font_size = 18
        self.icon_size = 24
        self.padding = 50
        self.app_colors: dict[str, str] = get_app_colors('blue')

        if page.session.get("user_colors"):
            self.app_colors: dict[str, str] = page.session.get(
                "user_colors")  # type: ignore [attr-defined]     ! page.session é um objeto que contém o método .get(), não é um dict

        self.input_width = 400

        # Obtem a lista das categorias de produtos da empresa logada
        self.categories_list = self._get_categories_list(
            self.empresa_logada["id"])
        self.selected_category_name: str | None = None
        # Responsividade
        self._create_form_fields()
        self.form = self.build_form()
        self.page.on_resized = self._page_resize

    def _get_categories_list(self, empresa_id) -> list[dict[str, Any]]:
        result = category_controllers.handle_get_active_categorias_summary(
            empresa_id)

        if result["status"] == "success":
            return result["data"]

        message_snackbar(self.page, result["message"], MessageType.ERROR)
        return []

    def on_change_status(self, e):
        status = e.control
        status.label = "Produto Ativo" if e.data == "true" else "Produto Inativo (Descontinuado)"
        status.update()

    def _update_dropdown_tooltip(self, e: ft.ControlEvent):
        """Atualiza o tooltip do Dropdown com o texto da opção selecionada."""
        dropdown = e.control
        selected_option = next(
            (opt for opt in dropdown.options if opt.key == dropdown.value), None)
        if selected_option:
            dropdown.tooltip = selected_option.text
            self.selected_category_name = selected_option.text
        else:
            dropdown.tooltip = dropdown.data
            self.selected_category_name = None
        dropdown.update()

    def _consult_product(self, e):
        if not self.ean_code.value:
            return

        # Variaveis globais são compartilhadas entre todas sessões de usuários logado
        blocked = app_globals.ean_gtin_api["blocked"]

        if blocked:
            expires_at = app_globals.ean_gtin_api["blocked_until"]
            if datetime.now(UTC) > expires_at:
                # Desbloqueia: Consulta liberada!
                app_globals.ean_gtin_api.update({"blocked_until": None, "blocked": False})
                blocked = False

        if blocked:
            show_banner(
                page=self.page,
                message=f"Limite de consultas excedido! Tente novamente após {format_datetime_to_utc_minus_3(expires_at)}"
            )
            return

        result = fetch_product_info_by_ean(self.ean_code.value)

        if not result:
            show_banner(
                page=self.page,
                message=f"Não foi possível obter dados para o EAN {self.ean_code.value}."
            )
            return
        if result["status_code"] == 429:
            expires_at = datetime.now(UTC) + timedelta(hours=24)
            app_globals.ean_gtin_api.update({"blocked_until": expires_at, "blocked": True})
            show_banner(
                page=self.page,
                message=f"Limite de consultas excedido! Tente novamente após {format_datetime_to_utc_minus_3(expires_at)}"
            )
            return

        product_data = result["data"]
        self.name.value = product_data["description"]
        thumbnail = product_data.get("thumbnail")

        if thumbnail and thumbnail.startswith("http"):
            # Inicializa o downloader de imagens
            image_downloader = ImageDownloader()

            # Faz o download da imagem da URL
            downloaded_file = image_downloader.download_image(
                image_url=thumbnail,
                prefix="cosmos_product"
            )

            if downloaded_file:
                # Sucesso no download - configura para usar o arquivo local
                self.local_upload_file = downloaded_file
                self.is_image_url_web = False  # Marca como arquivo local
                self.image_url = None  # Limpa a URL web

                # Atualiza a interface com a imagem baixada
                # Obtem o diretório raiz do projeto
                project_root = find_project_root(__file__)
                img_file = project_root / downloaded_file

                try:
                    with open(img_file, "rb") as f_img:
                        img_data = f_img.read()

                    base64_data = base64.b64encode(img_data).decode('utf-8')
                    mime_type, _ = mimetypes.guess_type(str(img_file))
                    if not mime_type:
                        # Tenta inferir pela extensão se mimetypes falhar
                        ext = str(img_file).split('.')[-1].lower()
                        if ext == "jpg" or ext == "jpeg":
                            mime_type = "image/jpeg"
                        elif ext == "png":
                            mime_type = "image/png"
                        elif ext == "svg":
                            mime_type = "image/svg+xml"
                        else:
                            mime_type = "application/octet-stream"

                    categoria_img = ft.Image(
                        src_base64=base64_data,
                        error_content=ft.Text("Erro ao carregar (base64)!"),
                        repeat=ft.ImageRepeat.NO_REPEAT,
                        fit=ft.ImageFit.CONTAIN,
                        border_radius=ft.border_radius.all(20),
                    )
                    self.image_frame.content = categoria_img

                except Exception as ex:
                    logger.error(f"Erro ao processar imagem baixada {img_file}: {ex}")
                    # Fallback: tenta usar a URL original diretamente
                    self.image_url = thumbnail
                    self.is_image_url_web = True
                    self.local_upload_file = None

                    categoria_img = ft.Image(
                        src=self.image_url,
                        error_content=ft.Text("Erro!"),
                        repeat=ft.ImageRepeat.NO_REPEAT,
                        fit=ft.ImageFit.CONTAIN,
                        border_radius=ft.border_radius.all(20),
                    )
                    self.image_frame.content = categoria_img

            else:
                # Falha no download - usa a URL original diretamente
                logger.warning(f"Falha ao baixar imagem da URL {thumbnail}, usando URL diretamente")
                self.image_url = thumbnail
                self.is_image_url_web = True
                self.local_upload_file = None

                categoria_img = ft.Image(
                    src=self.image_url,
                    error_content=ft.Text("Erro!"),
                    repeat=ft.ImageRepeat.NO_REPEAT,
                    fit=ft.ImageFit.CONTAIN,
                    border_radius=ft.border_radius.all(20),
                )
                self.image_frame.content = categoria_img


        if product_data.get("brand"):
            self.brand.value = product_data["brand"]["name"]

        if ncm := product_data.get("ncm"):
            self.ncm_code.value = ncm.get("code", "")
            self.ncm_description.value = ncm.get("description", "")
            self.ncm_full_description.value = ncm.get("full_description", "")

        if category := product_data.get("category"):
            id = category_controllers.handle_get_active_id(empresa_id=self.empresa_logada["id"], nome=category["description"])
            if id:
                self.categoria.value = id
            else:
                self.description.value = f"Categoria: {category['description']}"

        if product_data.get("price"):
            if description := self.description.value:
                description = description.strip() + "\n" + f"(Preço: {product_data['price']})"
            else:
                description = f"(Preço: {product_data['price']})"
            self.description.value = description

        if product_data.get("avg_price"):
            self.sale_price.set(product_data["avg_price"])

        if gtins := product_data.get("gtins"):
            if isinstance(gtins, list) and len(gtins) > 0:
                gtin = gtins[0]
                if unit := gtin.get("commercial_unit", {}).get("type_packaging", "UN"):
                    self.unit_of_measure.value = unit.strip().upper()

        self.page.update()


    def _create_form_fields(self):
        """Cria os campos do formulário de Produto"""
        #--------------------------------------------------------------------------------------
        # Código EAN
        self.ean_code = build_input_field(
            page_width=self.page.width,  # type: ignore [attr-defined]
            app_colors=self.app_colors,
            col={'xs': 12, 'md': 6, 'lg': 5},
            label="Código EAN (código de barras)",
            icon=ft.Icons.BARCODE_READER,
        )
        self.consult_product_button = ft.IconButton(
            col={'xs': 12, 'md': 1, 'lg': 2},
            icon=ft.Icons.SEARCH,
            icon_size=self.icon_size,
            tooltip="Consultar Produto",
            on_click=self._consult_product
        )
        # Código interno/SKU
        self.internal_code = build_input_field(
            page_width=self.page.width,  # type: ignore [attr-defined]
            app_colors=self.app_colors,
            col={'xs': 12, 'md': 5, 'lg': 5},
            label="Código interno/SKU",
            icon=ft.Icons.BARCODE_READER,
        )

        #------------------------------------------------------------------------------------------
        # Nome do Produto
        self.name = build_input_field(
            page_width=self.page.width,  # type: ignore [attr-defined]
            app_colors=self.app_colors,
            col={'xs': 12, 'md': 7, 'lg': 7},
            label="Nome do Produto",
            capitalization=ft.TextCapitalization.SENTENCES,
            icon=ft.Icons.ASSIGNMENT_OUTLINED,
        )
        # Dropdown para seleção da Categoria do Produto.
        # As opções são carregadas de self.categories_list, que é uma lista de dicionários.
        # Cada dicionário representa uma categoria de produto ativa e contém chaves como "id" e "name",
        # utilizadas para popular as opções do Dropdown.
        self.categoria = ft.Dropdown(
            col={'xs': 12, 'md': 5, 'lg': 5},
            label="Categoria",
            text_size=16,
            expanded_insets=ft.padding.all(10),
            expand=True,
            expand_loose=True,
            options=[
                ft.dropdown.Option(key=categoria["id"], text=categoria["name"])
                for categoria in self.categories_list
            ],
            enable_filter=True,
            hint_text="Selecione a categoria do produto",
            tooltip='Selecione a categoria do produto',
            data='Selecione a categoria do produto',
            on_change=self._update_dropdown_tooltip,
            filled=True,
            border=ft.InputBorder.OUTLINE,
            border_color=self.app_colors["primary"],
            width=self.input_width,  # type: ignore
        )

        #--------------------------------------------------------------------------------------
        # Marca do produto
        self.brand = build_input_field(
            page_width=self.page.width,  # type: ignore [attr-defined]
            app_colors=self.app_colors,
            col={'xs': 12, 'md': 8, 'lg': 8},
            label="Marca",
            capitalization=ft.TextCapitalization.SENTENCES,
            icon=ft.Icons.ASSIGNMENT_OUTLINED,
        )
        # Switch Ativo/Inativo
        self.status = ft.Switch(
            label="Produto Ativo",
            value=True,
            on_change=self.on_change_status,
            col={'xs': 12, 'md': 4, 'lg': 4})

        #--------------------------------------------------------------------------------------
        # Descrição do produto
        self.description = build_input_field(
            page_width=self.page.width,  # type: ignore
            app_colors=self.app_colors,
            col={'xs': 12, 'md': 12, 'lg': 12},
            label="Descrição (opcional)",
            capitalization=ft.TextCapitalization.SENTENCES,
            icon=ft.Icons.ASSIGNMENT_LATE_OUTLINED,
            multiline=True,
            max_lines=5,
            shift_enter=True,
        )

        #--------------------------------------------------------------------------------------
        # Preço de venda
        self.sale_price = MonetaryTextField(
            label="Preço de Venda",
            col={'xs': 12, 'md': 3, 'lg': 3},
            page_width=self.page.width, # type: ignore
            app_colors=self.app_colors,
        )
        # Preço de custo
        self.cost_price = MonetaryTextField(
            label="Preço de Custo",
            col={'xs': 12, 'md': 3, 'lg': 3},
            page_width=self.page.width, # type: ignore
            app_colors=self.app_colors,
        )
        # Unidade de medida
        self.unit_of_measure = build_input_field(
            page_width=self.page.width,  # type: ignore
            app_colors=self.app_colors,
            col={'xs': 12, 'md': 6, 'lg': 6},
            label='Unidade de medida (ex: "UN", "L", "KG", "PACOTE", etc)',
            capitalization=ft.TextCapitalization.CHARACTERS,
            icon=ft.Icons.ARCHIVE_OUTLINED,
        )

        #--------------------------------------------------------------------------------------
        # Quantidade disponível
        self.quantity_on_hand: ft.TextField = build_input_field(
            page_width=self.page.width,  # type: ignore
            app_colors=self.app_colors,
            col={'xs': 12, 'md': 3, 'lg': 3},
            label="Quantidade disponível",
            keyboard_type=ft.KeyboardType.NUMBER,
            text_align=ft.TextAlign.RIGHT,
            icon=ft.Icons.NUMBERS_OUTLINED,
        )
        # Quantidade mínima
        self.minimum_stock_level = build_input_field(
            page_width=self.page.width,  # type: ignore
            app_colors=self.app_colors,
            col={'xs': 12, 'md': 3, 'lg': 3},
            label='Quantidade mínima para reposição',
            keyboard_type=ft.KeyboardType.NUMBER,
            text_align=ft.TextAlign.RIGHT,
            icon=ft.Icons.NUMBERS_OUTLINED,
        )
        # Quantidade máxima
        self.maximum_stock_level = build_input_field(
            page_width=self.page.width,  # type: ignore
            app_colors=self.app_colors,
            col={'xs': 12, 'md': 6, 'lg': 6},
            label='Quantidade máxima para reposição',
            keyboard_type=ft.KeyboardType.NUMBER,
            text_align=ft.TextAlign.RIGHT,
            icon=ft.Icons.NUMBERS_OUTLINED,
        )

        #--------------------------------------------------------------------------------------
        # Código NCM
        self.ncm_code = build_input_field(
            page_width=self.page.width,  # type: ignore [attr-defined]
            app_colors=self.app_colors,
            col={'xs': 12, 'md': 6, 'lg': 6},
            label="Código da NCM",
            icon=ft.Icons.CODE_OUTLINED,
        )
        # Descrição NCM
        self.ncm_description = build_input_field(
            page_width=self.page.width,  # type: ignore [attr-defined]
            app_colors=self.app_colors,
            col={'xs': 12, 'md': 6, 'lg': 6},
            label="Descrição da NCM",
            icon=ft.Icons.ASSIGNMENT_OUTLINED,
        )
        #--------------------------------------------------------------------------------------
        # Detalhes NCM
        self.ncm_full_description = build_input_field(
            page_width=self.page.width,  # type: ignore [attr-defined]
            app_colors=self.app_colors,
            col={'xs': 12, 'md': 12, 'lg': 12},
            label="Detalhes da NCM",
            icon=ft.Icons.ASSIGNMENT_OUTLINED,
            multiline=True,
            max_lines=5,
        )

        # Imagem do Produto -------------------------------------------------------------------------------
        def on_hover_image(e):
            color: str = self.app_colors["container"] if e.data == "true" else self.app_colors["primary"]
            icon_container = self.camera_icon.content
            image_container = self.image_frame
            icon_container.color = color  # type: ignore
            image_container.border = ft.border.all(color=color, width=1)
            icon_container.update()  # type: ignore
            image_container.update()

        self.image_frame = ft.Container(
            content=ft.Text(
                "Imagem do Produto (opcional, mas desejada)", italic=True),
            bgcolor=ft.Colors.TRANSPARENT,
            padding=10,
            alignment=ft.alignment.center,
            width=350,
            height=250,
            border=ft.border.all(color=ft.Colors.GREY_400, width=1),
            border_radius=ft.border_radius.all(20),
            on_click=self._show_image_dialog,
            on_hover=on_hover_image,
            tooltip="Clique aqui para adicionar uma imagem do produto",
        )
        self.camera_icon = ft.Container(
            content=ft.Icon(
                name=ft.Icons.ADD_A_PHOTO_OUTLINED,
                size=20,
                color=ft.Colors.PRIMARY,
            ),
            margin=ft.margin.only(top=-5),
            ink=True,
            on_hover=on_hover_image,
            border_radius=ft.border_radius.all(100),
            padding=8,
        )

        self.image_section = ft.Column(
            col={'xs': 12, 'md': 4, 'lg': 4},
            controls=[self.image_frame, self.camera_icon],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0,
            width=1400,
        )

    async def _show_image_dialog(self, e) -> None:
        self.image_frame.border = ft.border.all(
            color=self.app_colors["primary"], width=1)
        self.image_frame.update()

        upload_file = UploadFile(
            page=self.page,
            title_dialog="Selecionar imagem do Produto",
            allowed_extensions=["png", "jpg", "jpeg", "svg"],
        )

        local_upload_file = await upload_file.open_dialog()

        # O arquivo ou URL do logo foi obtido. Não há erros.
        self.is_image_url_web = upload_file.is_url_web
        self.image_url = None

        if upload_file.is_url_web:
            # Obtem a url do arquivo para a imagem, atualiza a tela com a imagem do produto e termina
            self.image_url = upload_file.url_file
            self.local_upload_file = None

            categoria_img = ft.Image(
                src=self.image_url,
                error_content=ft.Text("Erro!"),
                repeat=ft.ImageRepeat.NO_REPEAT,
                fit=ft.ImageFit.CONTAIN,
                border_radius=ft.border_radius.all(20),
            )
            self.image_frame.content = categoria_img
            self.image_section.update()
            return

        """
        O arquivo de Imagem do Produto está salvo no diretório local do servidor em "uploads/"
        do projeto e está em self.local_upload_file.
        """
        if local_upload_file:
            self.local_upload_file = local_upload_file
            # Obtem o diretório raiz do projeto
            project_root = find_project_root(__file__)
            # O operador / é usado para concatenar partes de caminhos de forma segura e independente do sistema operacional.
            img_file = project_root / self.local_upload_file

            try:
                with open(img_file, "rb") as f_img:
                    img_data = f_img.read()

                base64_data = base64.b64encode(img_data).decode('utf-8')
                mime_type, _ = mimetypes.guess_type(str(img_file))
                if not mime_type:
                    # Tenta inferir pela extensão se mimetypes falhar
                    ext = str(img_file).split('.')[-1].lower()
                    if ext == "jpg" or ext == "jpeg":
                        mime_type = "image/jpeg"
                    elif ext == "png":
                        mime_type = "image/png"
                    elif ext == "svg":
                        mime_type = "image/svg+xml"
                    else:
                        mime_type = "application/octet-stream"  # Fallback genérico

                categoria_img = ft.Image(
                    src_base64=base64_data,
                    error_content=ft.Text("Erro ao carregar (base64)!"),
                    repeat=ft.ImageRepeat.NO_REPEAT,
                    fit=ft.ImageFit.CONTAIN,
                    border_radius=ft.border_radius.all(20),
                )
            except Exception as ex:
                logger.error(
                    f"Erro ao ler arquivo de imagem {img_file} para base64: {ex}")
                categoria_img = ft.Image(
                    error_content=ft.Text(
                        f"Erro crítico ao carregar imagem: {ex}"),
                )
            self.image_frame.content = categoria_img
            self.image_frame.update()

    def build_form(self) -> ft.Container:
        """Constrói o formulário de Categoria de Produtos"""
        def responsive_row(controls):
            return ft.ResponsiveRow(
                columns=12,
                expand=True,
                # alignment=ft.MainAxisAlignment.START,
                spacing=20,
                run_spacing=20,
                controls=controls,
            )

        build_content = ft.Column(
            controls=[
                ft.Text("Identificação do Produto", size=16),
                ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
                responsive_row(
                    controls=[
                        ft.Column(
                            controls=[
                                ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
                                responsive_row(controls=[self.ean_code, self.consult_product_button, self.internal_code]),
                                ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
                                responsive_row(controls=[self.name, self.categoria]),
                                ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
                                responsive_row(controls=[self.brand, self.status]),
                            ],
                            col={'xs': 12, 'md': 8, 'lg': 8},
                        ),
                        self.image_section,
                    ]
                ),

                # Cria uma linha (espaço vazio) para efeito visual
                ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
                ft.Divider(height=10),
                ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
                ft.Text("Informação do Produto", size=16),
                ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
                responsive_row(controls=[self.description]),
                ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
                responsive_row(controls=[self.sale_price.text_field, self.cost_price.text_field, self.unit_of_measure]),
                ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
                responsive_row(controls=[self.quantity_on_hand, self.minimum_stock_level, self.maximum_stock_level]),
                ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
                ft.Text("NCM - Nomenclatura Comum do Mercosul", size=16),
                ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
                responsive_row(controls=[self.ncm_code, self.ncm_description]),
                ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
                responsive_row(controls=[self.ncm_full_description]),
                ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.START,
            spacing=5,
            alignment=ft.MainAxisAlignment.SPACE_EVENLY,
        )

        return ft.Container(
            content=build_content,
            padding=self.padding,
            bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
            border_radius=ft.border_radius.all(20),
        )

    def did_mount(self):
        if self.data and self.data.get('id'):
            # Preenche os campos com os dados fiscais da empresa
            self.populate_form_fields()
        self.page.update()

    def populate_form_fields(self):
        """Preenche os campos do formulário com os dados do produto"""

        self.ean_code.value = self.data.get("ean_code", "")
        self.internal_code.value = self.data.get("internal_code", "")
        self.name.value = self.data["name"]
        self.categoria.value = self.data["categoria_id"]

        sale_price: Money = self.data['sale_price']
        # MonetaryTextField
        self.sale_price.set(sale_price.get_decimal(), sale_price.currency_symbol)
        cost_price: Money = self.data["cost_price"]
        # MonetaryTextField
        self.cost_price.set(cost_price.get_decimal(), cost_price.currency_symbol)
        self.description.value = self.data.get("description", "")
        self.brand.value = self.data.get("brand", "")
        self.quantity_on_hand.value = self.data.get("quantity_on_hand", 0)
        self.unit_of_measure.value = self.data.get("unit_of_measure", "")
        self.minimum_stock_level.value = self.data.get(
            "minimum_stock_level", 0)
        self.maximum_stock_level.value = self.data.get(
            "maximum_stock_level", 0)

        if ncm := self.data.get("ncm"):
            self.ncm_code.value = ncm.get("code", "")
            self.ncm_description.value = ncm.get("description", "")
            self.ncm_full_description.value = ncm.get("full_description", "")

        status = self.data.get("status", "ACTIVE")

        if status == "ACTIVE":
            self.status.value = True
            self.status.label = "Produto Ativo"
        else:
            self.status.value = False
            self.status.label = "Produto Inativo (Descontinuado)"

        if self.data.get("image_url"):
            # vars, não são fields do formulário
            self.image_url = self.data["image_url"]
            self.previous_image_url = self.data["image_url"]

            # Monta a imagem e associa ao campo do formulário
            categoria_img = ft.Image(
                src=self.image_url,
                error_content=ft.Text("Erro!"),
                repeat=ft.ImageRepeat.NO_REPEAT,
                fit=ft.ImageFit.CONTAIN,
                border_radius=ft.border_radius.all(20),
            )
            self.image_frame.content = categoria_img
        else:
            self.image_url = None
            self.previous_image_url = None

    def validate_form(self) -> str | None:
        """
        Valida os campos do formulário. Retorna uma mensagem de erro se algum campo obrigatório não estiver preenchido.
        """
        if not self.name.value:
            return "Por favor, preencha o nome do produto."
        if not self.categoria.value:
            return "Por favor, selecione a categoria do produto."
        if not self.sale_price.get_numeric_value():
            return "Por favor, preencha o preço de venda do produto."
        if not self.cost_price.get_numeric_value():
            return "Por favor, preencha o preço de custo do produto."
        if not self.quantity_on_hand.value:
            self.quantity_on_hand.value = "0"
        if not self.minimum_stock_level.value:
            self.minimum_stock_level.value = "0"
        if not self.maximum_stock_level.value:
            self.maximum_stock_level.value = "0"

        return None

    def _page_resize(self, e):
        if self.page.width < 600:  # type: ignore
            self.font_size = 14
            self.icon_size = 16
            self.padding = 20
            self.input_width = 280
        elif self.page.width < 1024:  # type: ignore
            self.font_size = 16
            self.icon_size = 20
            self.padding = 40
            self.input_width = 350
        else:
            self.font_size = 18
            self.icon_size = 24
            self.padding = 50
            self.input_width = 400

        # Atualiza os tamanhos dos campos do formulário
        self.name.text_size = self.font_size
        self.description.text_size = self.font_size

        # Atualiza o padding do container
        self.form.padding = self.padding
        self.form.update()

    def get_form_object(self) -> Produto:
        """
        Atualiza self.data com os dados do formulário e o retorna atualizado.
        """
        self.data["ean_code"] = self.ean_code.value
        self.data["internal_code"] = self.internal_code.value
        self.data['name'] = self.name.value
        self.data["categoria_id"] = self.categoria.value
        self.data["categoria_name"] = self.selected_category_name
        self.data["sale_price"] = {"amount_cents": self.sale_price.get_value_as_int(), "currency_symbol": self.sale_price.prefix_text}
        self.data["cost_price"] = {"amount_cents": self.cost_price.get_value_as_int(), "currency_symbol": self.cost_price.prefix_text}
        self.data['description'] = self.description.value
        self.data['ncm'] = {
            "code": self.ncm_code.value,
            "description": self.ncm_description.value,
            "full_description": self.ncm_full_description.value
        }

        if self.image_url:
            self.data['image_url'] = self.image_url

        # Converte os níveis de estoque para int, tratando valores vazios como 0
        try:
            self.data["quantity_on_hand"] = int(self.quantity_on_hand.value) if self.quantity_on_hand.value else 0
        except ValueError:
            self.data["quantity_on_hand"] = 0 # Deve ser numérico devido ao keyboard_type, mas garante
        try:
            self.data["minimum_stock_level"] = int(self.minimum_stock_level.value) if self.minimum_stock_level.value else 0
        except ValueError:
            self.data["minimum_stock_level"] = 0
        try:
            self.data["maximum_stock_level"] = int(self.maximum_stock_level.value) if self.maximum_stock_level.value else 0
        except ValueError:
            self.data["maximum_stock_level"] = 0

        self.data["brand"] = self.brand.value
        self.data["unit_of_measure"] = self.unit_of_measure.value
        self.data['status'] = ProdutoStatus.ACTIVE if self.status.value else ProdutoStatus.INACTIVE

        if not self.data.get('empresa_id'):
            self.data["empresa_id"] = self.empresa_logada["id"]

        return Produto.from_dict(self.data)

    def send_to_bucket(self):
        # Faz o upload do arquivo de imagem do produto para o bucket
        if not self.local_upload_file:
            # Não há arquivo local para enviar
            return False

        prefix = "empresas/" + self.empresa_logada["id"] + "/produtos"

        file_uid = get_uuid()   # Obtem um UUID único para o arquivo

        _, dot_extension = os.path.splitext(self.local_upload_file)
        # Padroniza a extensão para caracteres minúsculos
        dot_extension = dot_extension.lower()

        # A lógica aqui depende do Bucket utilizado, neste caso usamos o S3 da AWS, usamos o CNPJ ou user_id como diretório no bucket.
        file_name_bucket = f"{prefix}/img_{file_uid}{dot_extension}"

        try:
            self.image_url = bucket_controllers.handle_upload_bucket(
                local_path=self.local_upload_file, key=file_name_bucket)

            if self.image_url:
                # Atualiza logo na tela
                produto_img = ft.Image(
                    src=self.image_url,
                    error_content=ft.Text("Erro!"),
                    repeat=ft.ImageRepeat.NO_REPEAT,
                    fit=ft.ImageFit.CONTAIN,
                    border_radius=ft.border_radius.all(20),
                )
                self.image_frame.content = produto_img
                self.image_frame.update()
                return True

            # A Imagem não é válida, URL não foi gerada, mantém a imagem anterior se houver
            if self.previous_image_url:
                self.image_url = self.previous_image_url

            message_snackbar(
                page=self.page, message="Não foi possível carregar imagem do produto de produtos!", message_type=MessageType.ERROR)

            return False
        except ValueError as e:
            msg = f"Erro de validação ao carregar imagem: {str(e)}"
            message_snackbar(page=self.page, message=msg,
                             message_type=MessageType.ERROR)
            logger.error(msg)
        except RuntimeError as e:
            msg = f"Erro ao carregar imagem: {str(e)}"
            message_snackbar(page=self.page, message=msg,
                             message_type=MessageType.ERROR)
            logger.error(msg)
        finally:
            # Independente de sucesso, remove o arquivo de imagem do diretório local uploads/
            try:
                os.remove(self.local_upload_file)
            except:
                pass  # Ignora erros na limpeza do arquivo

    def build(self) -> ft.Container:
        return self.form

    def clear_form(self):
        """Limpa os campos do formulário"""
        for field in self.__dict__.values():
            if isinstance(field, (ft.TextField, ft.Dropdown)):
                field.value = ''
            if isinstance(field, (ft.Switch)):
                field.value = True  # Por default, a categoria sempre é ativa

        # Limpa o buffer com os dados de categorias carregados
        self.data = {}

# Rota: /home/produtos/form


def show_product_form(page: ft.Page):
    """Página de cadastro de produtos."""
    route_title = "home/produtos/form"
    produto_data = page.app_state.form_data  # type: ignore

    if id := produto_data.get("id"):
        route_title += f"/{id}"
    else:
        route_title += "/new"

    def handle_icon_hover(e):
        """Muda o bgcolor do container no hover."""
        e.control.bgcolor = ft.Colors.with_opacity(
            0.1, ft.Colors.WHITE) if e.data == "true" else ft.Colors.TRANSPARENT
        e.control.update()

    appbar = ft.AppBar(
        leading=ft.Container(
            alignment=ft.alignment.center_left,
            padding=ft.padding.only(left=10),
            content=ft.Container(
                width=40,
                height=40,
                border_radius=ft.border_radius.all(100),
                # Aplica ink ao wrapper (ao clicar da um feedback visual para o usuário)
                ink=True,
                bgcolor=ft.Colors.TRANSPARENT,
                alignment=ft.alignment.center,
                on_hover=handle_icon_hover,
                content=ft.Icon(ft.Icons.ARROW_BACK),
                on_click=lambda _: page.go(
                    page.data if page.data else '/home'),
                tooltip="Voltar",
                # Ajuda a garantir que o hover respeite o border_radius
                clip_behavior=ft.ClipBehavior.ANTI_ALIAS
            ),
        ),
        title=ft.Text(route_title, size=18, selectable=True),
        bgcolor=ft.Colors.with_opacity(0.9, ft.Colors.PRIMARY_CONTAINER),
        adaptive=True,
    )

    produtos_view = ProdutoForm(page=page)
    produtos_view.did_mount()
    form_container = produtos_view.build()

    def save_form_produtos(e):
        # Valida os dados do formulário
        if msg := produtos_view.validate_form():
            message_snackbar(
                page=page, message=msg, message_type=MessageType.WARNING)
            return

        # Desabilita o botão de salvar para evitar múltiplos cliques
        save_btn.disabled = True

        # Instância do objeto Produto com os dados do formulário para enviar para o backend
        produto: Produto = produtos_view.get_form_object()

        if not produtos_view.is_image_url_web and produtos_view.local_upload_file:
            # Envia o arquivo de imagem para o bucket
            if produtos_view.send_to_bucket():
                produto.image_url = produtos_view.image_url
            else:
                message_snackbar(
                    page=page, message="Erro ao enviar imagem para o bucket", message_type=MessageType.WARNING)

            # Apaga arquivo do servidor local
            try:
                os.remove(produtos_view.local_upload_file)
            except:
                pass  # Ignora erros na limpeza do arquivo
            produtos_view.local_upload_file = None

        # Envia os dados para o backend, os exceptions foram tratadas no controller e result contém
        # o status da operação.
        result = product_controllers.handle_save(
            produto=produto,
            usuario=page.app_state.usuario  # type: ignore
        )

        if result["status"] == "error":
            message_snackbar(
                page=page, message=result["message"], message_type=MessageType.ERROR)
            return

        # Limpa o formulário salvo e volta para a página anterior que a invocou
        produtos_view.clear_form()
        page.app_state.clear_form_data()  # type: ignore
        page.go(page.data if page.data else '/home')

    def exit_form_produtos(e):
        if not produtos_view.is_image_url_web and produtos_view.local_upload_file:
            try:
                os.remove(produtos_view.local_upload_file)
            except:
                pass  # Ignora erros na limpeza do arquivo
            produtos_view.local_upload_file = None

        # Limpa o formulário sem salvar e volta para à página anterior que a invocou
        produtos_view.clear_form()
        page.app_state.clear_form_data()  # type: ignore
        page.go(page.data if page.data else '/home')

    # Adiciona os botões "Salvar" & "Cancelar"
    save_btn = ft.ElevatedButton(
        text="Salvar", col={'xs': 5, 'md': 5, 'lg': 5}, on_click=save_form_produtos)
    exit_btn = ft.ElevatedButton(
        text="Cancelar", col={'xs': 5, 'md': 5, 'lg': 5}, on_click=exit_form_produtos)
    space_between = ft.Container(col={'xs': 2, 'md': 2, 'lg': 2})
    return ft.Column(
        controls=[
            form_container,
            ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
            ft.Divider(height=10),
            ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
            ft.ResponsiveRow(
                columns=12,
                expand=True,
                spacing=10,
                run_spacing=10,
                controls=[save_btn, space_between, exit_btn],
                alignment=ft.MainAxisAlignment.END,
            ),
        ],
        data=appbar,
    )
