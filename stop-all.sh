#!/bin/bash
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

echo "Deteniendo contenedores de PostgreSQL y Redis..."
echo "docker compose -f docker-compose.infra.yml down" | newgrp docker 2>/dev/null || docker compose -f docker-compose.infra.yml down
echo "Contenedores detenidos."
