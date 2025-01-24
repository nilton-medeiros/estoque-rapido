import os
import firebase_admin
from firebase_admin import credentials

# Obtém o caminho absoluto para o arquivo de credenciais
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_PATH = os.path.join(BASE_DIR, '..', '..', '..', 'src', 'services', 'serviceAccountKey.json')
CREDENTIALS_PATH = os.path.normpath(CREDENTIALS_PATH)

# print("CREDENTIALS_PATH:", CREDENTIALS_PATH)


# Singleton para inicialização do Firebase
def get_firebase_app():
    # Inicializa o aplicativo Firebase apenas se ainda não estiver inicializado
    if not firebase_admin._apps:
        try:
            cred = credentials.Certificate(CREDENTIALS_PATH)
            firebase_admin.initialize_app(cred)
            print("INTERFACE: Firebase inicializado com sucesso!")
        except FileNotFoundError:
            print(
                f"INTERFACE: Erro: Arquivo de credenciais não encontrado em {CREDENTIALS_PATH}")
    return firebase_admin.get_app()
