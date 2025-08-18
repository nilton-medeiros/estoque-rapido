# src/routes.py
from src.pages.external_pages import show_signup_page, show_landing_page, show_login_page
from src.pages.clientes.clientes_form_page import show_client_form
from src.pages.clientes.clientes_grid_page import show_clients_grid
from src.pages.clientes.clientes_grid_recycle_page import show_clients_grid_trash
from src.pages.empresas import show_companies_grid, show_company_main_form, show_company_tax_form, show_companies_grid_trash
from src.pages.external_pages.forgot_password_page import show_forgot_pswd_page
from src.pages.formas_pagamento.formas_pagamento_form_page import show_formas_pagamento_form
from src.pages.formas_pagamento.formas_pagamento_grid_page import show_formas_pagamento_grid
from src.pages.formas_pagamento.formas_pagamento_grid_recycle_page import show_formas_pagamento_grid_trash
from src.pages.home import show_home_page
from src.pages.pedidos.pedidos_form_page import show_pedido_form
from src.pages.pedidos.pedidos_grid_page import show_orders_grid
from src.pages.pedidos.pedidos_grid_recycle_page import show_orders_grid_trash
from src.pages.produtos import show_products_grid, show_products_grid_trash, show_product_form
from src.pages.categorias import show_categories_grid, show_categories_grid_trash, show_category_form
from src.pages.usuarios.usuarios_form_page import show_user_form
from src.pages.usuarios.usuarios_grid_page import show_users_grid
from src.pages.usuarios.usuarios_grid_recycle_page import show_users_grid_trash

# Mapeamento de rotas para as funções que geram suas views/conteúdos.
# Esta centralização simplifica o main.py e facilita a manutenção.
ROUTE_HANDLERS = {
    # Rotas públicas
    '/': show_landing_page,
    '/login': show_login_page,
    '/signup': show_signup_page,
    '/forgot-password': show_forgot_pswd_page,


    # Rotas protegidas (requerem login)
    '/home': show_home_page,

    # Empresas
    '/home/empresas/grid': show_companies_grid,
    '/home/empresas/grid/lixeira': show_companies_grid_trash,
    '/home/empresas/form/principal': show_company_main_form,
    '/home/empresas/form/dados-fiscais': show_company_tax_form,

    # Usuários
    '/home/usuarios/grid': show_users_grid,
    '/home/usuarios/grid/lixeira': show_users_grid_trash,
    '/home/usuarios/form': show_user_form,

    # Clientes
    '/home/clientes/grid': show_clients_grid,
    '/home/clientes/grid/lixeira': show_clients_grid_trash,
    '/home/clientes/form': show_client_form,

    # Produtos e Categorias
    '/home/produtos/grid': show_products_grid,
    '/home/produtos/grid/lixeira': show_products_grid_trash,
    '/home/produtos/form': show_product_form,
    '/home/produtos/categorias/grid': show_categories_grid,
    '/home/produtos/categorias/grid/lixeira': show_categories_grid_trash,
    '/home/produtos/categorias/form': show_category_form,

    # Pedidos
    '/home/pedidos/grid': show_orders_grid,
    '/home/pedidos/grid/lixeira': show_orders_grid_trash,
    '/home/pedidos/form': show_pedido_form,

    # Formas de Pagamento
    '/home/formasdepagamento/grid': show_formas_pagamento_grid,
    '/home/formasdepagamento/grid/lixeira': show_formas_pagamento_grid_trash,
    '/home/formasdepagamento/form': show_formas_pagamento_form,
}
