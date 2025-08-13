from enum import Enum


class SessionKeys(str, Enum):
    """Chaves usadas no page.session para um acesso seguro e centralizado."""
    USER_AUTHENTICATED = "user_authenticaded"
    THEME_COLORS = "theme_colors"
    DASHBOARD = "dashboard"


class PubSubTopics(str, Enum):
    """Tópicos usados no sistema Pub/Sub para comunicação entre componentes."""
    USER_UPDATED = "usuario_updated"
    EMPRESA_UPDATED = "empresa_updated"
    DASHBOARD_REFRESHED = "dashboard_refreshed"
