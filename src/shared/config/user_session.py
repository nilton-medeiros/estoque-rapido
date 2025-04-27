import flet as ft
import logging

from src.shared.config import get_app_colors

import flet as ft

logger = logging.getLogger(__name__)
PREFIX = "estoque.rapido."


def prepare_the_user_session(page: ft.Page) -> None:
    """Obtem a sessão do usuário do navegador do cliente"""

    logger.debug("Preparando sessão do usuário...")
    try:
        user_settings = page.client_storage.get(f"{PREFIX}user-settings")
        print(f"Debug  -> prepare_the_user_session: {user_settings}")
        # user_settings = page._invoke_method_async(# noqa: WPS437
        #     method_name="clientStorage:get",
        #     arguments={"key": f"{PREFIX}user-settings"},
        #     wait_timeout=10,
        #     wait_for_result=True,
        # )

        logger.debug(f"Configurações do usuário recuperadas: {user_settings}")

        if not user_settings:
            # Define a cor padrão
            print(f"Debug  -> prepare_the_user_session: user_settings não encontrada no client session")
            user_settings = {"colors": get_app_colors('yellow')}
            # Armazena no navegador do cliente
            page.client_storage.set(f"{PREFIX}user-settings", user_settings)
            # await page._invoke_method_async( # noqa: WPS437
            #     "clientStorage:set",
            #     {"key": f"{PREFIX}user-settings", "value": user_settings},
            #     wait_timeout=10,
            # )

            logger.debug("Novas configurações de usuário criadas")

        # Armazena no servidor na sessão do usuário
        page.session.set("user_colors", user_settings["colors"])
        logger.debug("Sessão do usuário preparada com sucesso")
        print(f"Debug  -> prepare_the_user_session: Setado page.session.user_colors: {user_settings['colors']}")
    except Exception as e:
        error_msg = f"Erro ao preparar sessão do usuário: {str(e)}"
        logger.error(error_msg)
        # Fallback para cores padrão se client_storage falhar
        page.session.set("user_colors", get_app_colors('yellow'))
        print(error_msg)
        print("Assumindo cores padrão...")


def refresh_the_user_session(page: ft.Page, colors: dict) -> None:
    """Atualiza a sessão do usuário no navegador e na sessão do usuário do Flet"""

    logger.debug("Atualziando sessão do usuário...")

    try:
        # Obtem as cores pela cor base
        user_settings = {"colors": colors}
        logger.debug(f"Atualizando sessão com cores: {colors}")
        print(f"Debug  -> refresh_the_user_session: color: {colors}")
        print(f"Debug  -> refresh_the_user_session: user_settings: {user_settings}")

        # Armazena no navegador do cliente
        page.client_storage.set(f"{PREFIX}user-settings", user_settings)
        # page._invoke_method_async( # noqa: WPS437
        #     "clientStorage:set",
        #     {"key": f"{PREFIX}user-settings", "value": user_settings},
        #     wait_timeout=10,
        # )

        # Armazena no servidor na sessão do usuário
        page.session.set("user_colors", colors)
        logger.debug("Sessão do usuário atualizada com sucesso")
    except Exception as e:
        error_msg = f"Erro ao atualizar sessão do usuário: {str(e)}"
        logger.error(error_msg)
        # Ainda atualizamos a sessão local mesmo se o client_storage falhar
        page.session.set("user_colors", colors)
        print(error_msg)
        print("Mesmo assim a sessão local foi atualizada...")
