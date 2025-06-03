import logging
import os
import firebase_admin
from firebase_admin import credentials

from src.shared.utils.find_project_path import find_project_root

# Obtém o caminho absoluto para o arquivo de credenciais
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# CREDENTIALS_PATH = os.path.join(BASE_DIR, '..', '..', '..', 'src', 'services', '.keys', 'serviceAccountKey.json')
CREDENTIALS_PATH = find_project_root(__file__) / 'serviceAccountKey.json'
CREDENTIALS_PATH = os.path.normpath(CREDENTIALS_PATH)

print(f"Debug  -> {CREDENTIALS_PATH}")

logger = logging.getLogger(__name__)


# Singleton para inicialização do Firebase
def get_firebase_app():
    # Inicializa o aplicativo Firebase apenas se ainda não estiver inicializado
    if not firebase_admin._apps:
        try:
            cred = credentials.Certificate(CREDENTIALS_PATH)
            firebase_admin.initialize_app(cred)
            # print("INTERFACE: Firebase inicializado com sucesso!")
        except FileNotFoundError:
            logger.error(f"INTERFACE: Erro: Arquivo de credenciais não encontrado em {CREDENTIALS_PATH}")
    return firebase_admin.get_app()
