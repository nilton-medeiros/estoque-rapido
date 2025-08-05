#!/bin/bash

# Extrai informações de versão direto do Git
VERSION=$(git describe --tags --abbrev=0)
COMMIT=$(git rev-parse --short HEAD)
BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')

# Atualiza o arquivo version.py
echo "APP_VERSION = '$VERSION'" > src/shared/config/version.py
echo "COMMIT_HASH = '$COMMIT'" >> src/shared/config/version.py
echo "BUILD_DATE = '$BUILD_DATE'" >> src/shared/config/version.py

echo "✔ Versão atualizada: $VERSION ($COMMIT - $BUILD_DATE)"