import asyncio
import flet as ft
import logging

from src.shared import get_app_colors

import flet as ft

logger = logging.getLogger(__name__)
PREFIX = "estoque.rapido."

"""
Este módulo está desativado, pois o client_storage não funciona direito com views e multiplas páginas,
Vou aguardar os devs do Flet resolver este problema.
https://github.com/flet-dev/flet/issues/3783
Nota: Interessante, funciona perfeitamente em página simples como no exemplo em:
estoquerapido/src/tests/main_client_storage.py
"""

async def prepare_the_user_session(page: ft.Page) -> None:
    """Busca assíncrona do client_storage com timeout"""

    logger.debug("Preparando sessão do usuário...")
    try:
        loop = asyncio.get_running_loop()
        result = await asyncio.wait_for(
            loop.run_in_executor(None, lambda: page.client_storage.get(f"{PREFIX}user-settings")),
            timeout=asyncio.timeout # type: ignore
        )
        logger.debug(f"client_storage.get({f"{PREFIX}user-settings"}) retornou: {result}")
        user_settings = result
        if not user_settings:
            # Define a cor padrão
            colors = get_app_colors('yellow')
            user_settings = {"colors": colors}
            # Armazena no navegador do cliente
            await refresh_the_user_session(page=page, colors=colors)
            logger.debug("Novas configurações de usuário criadas")
            return
        page.session.set("user_colors", user_settings["colors"])
        logger.debug("Sessão do usuário preparada com sucesso")
    except asyncio.TimeoutError:
        logger.error(f"Timeout ao buscar {f"{PREFIX}user-settings"} do client_storage")
        # Assume cor padrão
        page.session.set("user_colors", get_app_colors('yellow'))
    except Exception as e:
        logger.error(f"Erro inesperado ao buscar {f"{PREFIX}user-settings"} do client_storage: {e}")
        print(f"Erro inesperado ao buscar {f"{PREFIX}user-settings"} do client_storage: {e}")
        # Assume cor padrão
        page.session.set("user_colors", get_app_colors('yellow'))


async def refresh_the_user_session(page: ft.Page, colors: dict) -> None:
    """Atualiza a sessão do usuário no navegador e na sessão do usuário do Flet"""

    logger.debug("Atualziando sessão do usuário...")

    try:
        loop = asyncio.get_running_loop()
        user_settings = {"colors": colors}
        await asyncio.wait_for(
            loop.run_in_executor(None, lambda: page.client_storage.set(f"{PREFIX}user-settings", user_settings)),
            timeout=asyncio.timeout # type: ignore
        )
        page.session.set("user_colors", colors)

        logger.debug("Sessão do usuário atualizada com sucesso")
    except asyncio.TimeoutError:
        logger.error(f"Timeout ao atualizar {f"{PREFIX}user-settings"} do client_storage")
        print(f"Timeout ao atualizar {f"{PREFIX}user-settings"} do client_storage")
        # Assume cor padrão
        page.session.set("user_colors", get_app_colors('yellow'))
    except Exception as e:
        logger.error(f"Erro inesperado ao atualizar {f"{PREFIX}user-settings"} do client_storage: {e}")
        print(f"Erro inesperado ao atualizar {f"{PREFIX}user-settings"} do client_storage: {e}")
        # Assume cor padrão
        page.session.set("user_colors", get_app_colors('yellow'))
