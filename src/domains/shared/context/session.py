from flet import Page
from get_app_colors import get_theme_colors
from src.domains.usuarios.models import Usuario

def get_current_user(page: Page):
    return page.app_state.usuario # type: ignore [attr-defined]

def get_session_colors(page: Page) -> dict:
    # Garante que há sempre uma cor padrão
    theme_colors = get_theme_colors()
    if not page.session.contains_key("theme_colors"):
        page.session.set("theme_colors", theme_colors) # Atualiza a sessão do usuário
        return theme_colors # # Improvável, só para o Pylance não acusar erro. Retorna o tema de cores padrão

    # Obtem o tema de cores da sessão do usuário
    session_colors = page.session.get("theme_colors")
    if not isinstance(session_colors, dict):
        page.session.set("theme_colors", theme_colors) # Atualiza a sessão do usuário
        return theme_colors # Improvável, só para o Pylance não acusar erro. Retorna o tema de cores padrão
    return session_colors # Retorna o tema de cores da sessão do usuário
