#!/bin/bash
set -e

echo "=== Sincronizando con el repositorio oficial (upstream: artcc/freelingo) ==="
git fetch upstream

CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "Rama actual: $CURRENT_BRANCH"

echo "Fusionando cambios de upstream/main en $CURRENT_BRANCH..."
git merge upstream/main --no-edit

echo "Sincronización completada exitosamente."
echo "Para subir a tu repositorio en GitHub ejecuta: git push origin $CURRENT_BRANCH"
