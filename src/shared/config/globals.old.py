# globals.py
app_colors = {
    'base_color': 'yellow',
    'primary': '#FFEB3B',  # ft.Colors.YELLOW
    'container': '#FFF59D',  # ft.Colors.YELLOW_200
    'accent': '#FFD740',  # ft.Colors.YELLOW_ACCENT_400
    'appbar': '#FBC02D', # ft.Colors.YELLOW_700
}

"""
# arquivo globals.py
user = None

# Após login
import globals
globals.user = {"uid": "123", "email": "usuario@exemplo.com"}

# Em outra página
import globals
if globals.user:
    print(f"Usuário logado: {globals.user['email']}")
"""