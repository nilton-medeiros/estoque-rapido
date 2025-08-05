import logging

import flet as ft

from src.domains.empresas.controllers.grid_controller import GridController
from src.domains.empresas.views.empresas_grid_ui import EmpresasGridUI

logger = logging.getLogger(__name__)


# Rota: /home/empresas/grid
def show_companies_grid(page: ft.Page):
    """
    Página de exibição das empresas do usuário logado em formato Cards.
    Orquestra a criação do Controller e da UI para a grade de empresas.
    """
    page.theme_mode = ft.ThemeMode.DARK
    page.data = page.route

    # 1. Inicializa o Controller com a lógica de negócio
    controller = GridController(page)

    # 2. Inicializa a UI com os componentes visuais, passando o controller
    ui = EmpresasGridUI(page, controller)

    # 3. Injeta a instância da UI no controller para que ele possa atualizá-la
    controller.ui = ui

    # 4. Dispara o carregamento inicial dos dados em uma tarefa de fundo
    page.run_task(controller.load_data_and_update_ui)

    # 5. Retorna a View construída pela classe de UI.
    # A UI é responsável por exibir o spinner de carregamento inicial.
    return ui.build()
