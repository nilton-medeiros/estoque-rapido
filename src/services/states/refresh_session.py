import flet as ft
import logging
import asyncio

from src.domains.produtos.controllers.produtos_controllers import handle_get_low_stock_count
from src.shared.utils import MessageType, message_snackbar

logger = logging.getLogger(__name__)

async def refresh_dashboard_session(page: ft.Page):
    """
    Atualiza os dados da sessão do dashboard com base no estado atual da empresa.
    """
    try:
        current_company = page.app_state.empresa # type: ignore [attr-defined]

        dashboard_data = {
            "repor_produtos": 0, # Buscar contagem real
            "encomendas": 0,     # Buscar contagem real
            "pagamentos": 0,     # Buscar contagem real
            "recebimentos": 0,   # Buscar contagem real
        }

        # Se houver uma empresa selecionada, buscar dados reais (exemplo)
        if not current_company.get('id'):
            logger.warning("Nenhuma empresa selecionada para atualizar dashboard session")
            return

        # Busca todos os produtos ativos que precisam de reposição
        # Envolve a chamada síncrona em asyncio.to_thread para não bloquear
        result = await asyncio.to_thread(
            handle_get_low_stock_count, empresa_id=current_company['id']
        )

        if result["status"] == "error":
            logger.warning(f"Erro ao buscar dados do dashboard: {result['message']}")
            message_snackbar(
                page=page, message=result["message"], message_type=MessageType.ERROR)
            return

        dashboard_data["repor_produtos"] = result["data"]["products_low_stock"]

        # TODO: Implementar as demais lógicas real para buscar dados do dashboard
        # dashboard_data["encomendas"] = some_service.get_pending_orders_count(company_id=current_company['id'])
        # ... etc.

        page.session.set("dashboard", dashboard_data)
        logger.info(f"Dashboard session updated for company: {current_company.get('id', 'None')}")
        # Notifica que o dashboard foi atualizado
        page.pubsub.send_all("dashboard_refreshed")

    except Exception as e:
        logger.error(f"Erro ao atualizar dashboard session: {str(e)}")
        # Opcional: Limpar a sessão do dashboard em caso de erro
        page.session.set("dashboard", {
            "repor_produtos": 0,
            "encomendas": 0,
            "pagamentos": 0,
            "recebimentos": 0,
        })
        # Opcional: notificar sobre o erro também, se a UI precisar reagir
        # page.pubsub.send_all("dashboard_refresh_error")