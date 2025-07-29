from flet import Page
from src.shared.config import get_theme_colors
from src.domains.usuarios.models import Usuario

def get_current_user(page: Page) -> Usuario:
    """Retorna o usuário atual (Usuario)."""
    return page.app_state.usuario # type: ignore [attr-defined]

def get_current_company(page: Page) -> dict:
    """Retorna a empresa atual (dict)."""
    return page.app_state.empresa # type: ignore [attr=defined]

def get_session_colors(page: Page) -> dict[str, str]:
    """Retorna o tema de cores da sessão do usuário (dict)."""
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

def get_current_data_form(page: Page) -> dict:
    """Retorna os dados do formulário atual (dict)."""
    return page.app_state.form_data or {} # type: ignore [attr-defined]

def get_current_page_width(page: Page) -> int:
    """Retorna a largura atual da página (int)."""
    width = 600
    if page.width:
        width: int = int(page.width)
    return width
