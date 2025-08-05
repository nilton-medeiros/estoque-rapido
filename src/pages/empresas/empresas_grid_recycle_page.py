import logging

import flet as ft

from src.domains.empresas.controllers.recycle_controller import RecycleController
from src.domains.empresas.views.empresas_recycle_ui import EmpresasRecycleUI

logger = logging.getLogger(__name__)


# Rota: /home/empresas/grid/lixeira
def show_companies_grid_trash(page: ft.Page):
    """
    Página de exibição das empresas inativas ('DELETED' e 'ARCHIVED').
    Orquestra a criação do Controller e da UI para a lixeira de empresas.
    """
    page.theme_mode = ft.ThemeMode.DARK

    # 1. Inicializa o Controller com a lógica de negócio
    controller = RecycleController(page)

    # 2. Inicializa a UI com os componentes visuais, passando o controller
    ui = EmpresasRecycleUI(page, controller)

    # 3. Injeta a instância da UI no controller para que ele possa atualizá-la
    controller.ui = ui

    # 4. Dispara o carregamento inicial dos dados em uma tarefa de fundo
    page.run_task(controller.load_data_and_update_ui)

    # 5. Retorna a View construída pela classe de UI.
    # A UI é responsável por exibir o spinner de carregamento inicial.
    return ui.build()
