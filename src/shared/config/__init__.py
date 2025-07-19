from .get_app_colors import get_theme_colors
# A configuração de logging agora acontece quando logging_config.py é importado,
# que é acionado pela linha abaixo.
# Não há mais uma classe LogConfig para exportar diretamente daqui.
import src.shared.config.logging_config
