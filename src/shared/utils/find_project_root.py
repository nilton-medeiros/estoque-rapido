from pathlib import Path
import os

def find_project_root(current_path, marker='assets'):
    """Encontra a raiz do projeto subindo os diretórios até encontrar a pasta assets"""
    current = Path(current_path).resolve()

    # Sobe os diretórios até encontrar o marcador ou chegar na raiz do sistema
    while current != current.parent:
        if (current / marker).exists():
            return current
        current = current.parent

    # Se não encontrar, usa o diretório atual como fallback
    return Path(current_path).resolve().parent.parent.parent.parent

"""
# A partir do diretório onde o script está
project_root = find_project_root(__file__)
log_dir = project_root / 'logs'
"""