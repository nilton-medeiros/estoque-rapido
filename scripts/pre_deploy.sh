#!/bin/bash
set -e

echo "⏳ Iniciando Pre-Deploy..."

# Verifica se o Git está instalado
if ! command -v git &> /dev/null; then
    echo "❌ Git não está instalado. Abortando deploy."
    exit 1
fi

# Verifica se há pelo menos uma tag
if ! git describe --tags --abbrev=0 &> /dev/null; then
    echo "⚠️ Nenhuma tag encontrada. Usando versão default."
    VERSION="0.0.0"
else
    VERSION=$(git describe --tags --abbrev=0)
fi

COMMIT=$(git rev-parse --short HEAD)
BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')

# Atualiza o version.py
echo "APP_VERSION = '$VERSION'" > src/shared/config/version.py
echo "COMMIT_HASH = '$COMMIT'" >> src/shared/config/version.py
echo "BUILD_DATE = '$BUILD_DATE'" >> src/shared/config/version.py

echo "✅ Version.py atualizado com sucesso!"
echo "📦 Versão: $VERSION | Commit: $COMMIT | Build: $BUILD_DATE"