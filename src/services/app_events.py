class AppEvents:
    """
    Centraliza as constantes de eventos da aplicação.
    Evita erros de digitação e facilita a manutenção.
    """
    USER_UPDATED = "user_updated"
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"

    COMPANY_UPDATED = "company_updated"
    COMPANY_CREATED = "company_created"
    COMPANY_DELETED = "company_deleted"

    ERROR_OCCURRED = "error_occurred"
    AUTH_STATE_CHANGED = "auth_state_changed"
