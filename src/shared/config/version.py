# version.py

"""
Este arquivo centraliza as informações de versão da aplicação.

IDEALMENTE, este arquivo não deve ser editado manualmente.
Ele deve ser gerado automaticamente durante o processo de build/deploy.

Exemplo de comando no script de deploy (shell):

VERSION=$(git describe --tags --abbrev=0)
COMMIT=$(git rev-parse --short HEAD)
BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')

echo "APP_VERSION = '$VERSION'" > src/shared/config/version.py
echo "COMMIT_HASH = '$COMMIT'" >> src/shared/config/version.py
echo "BUILD_DATE = '$BUILD_DATE'" >> src/shared/config/version.py
"""

APP_VERSION = "1.00.21"