#!/bin/bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

echo "=========================================================="
echo "    Iniciando FreeLingo con Antigravity CLI (agy)"
echo "=========================================================="

# 1. Asegurar contenedores de PostgreSQL y Redis
echo "[1/3] Verificando contenedores auxiliares (PostgreSQL 16 & Redis 7)..."
echo "docker compose -f docker-compose.infra.yml up -d" | newgrp docker 2>/dev/null || docker compose -f docker-compose.infra.yml up -d

# Esperar a que PostgreSQL esté listo
sleep 2

# 2. Iniciar Backend (FastAPI con soporte para agy)
echo "[2/3] Iniciando Backend en http://127.0.0.1:8000..."
source .venv/bin/activate
(
  cd backend
  PYTHONPATH=. uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
) &
BACKEND_PID=$!

# 3. Iniciar Frontend (Next.js 16)
echo "[3/3] Iniciando Frontend en http://localhost:3000..."
(
  cd frontend
  npm run dev
) &
FRONTEND_PID=$!

cleanup() {
  echo ""
  echo "Deteniendo servidores locales..."
  kill $BACKEND_PID 2>/dev/null || true
  kill $FRONTEND_PID 2>/dev/null || true
  echo "FreeLingo detenido correctamente."
  exit 0
}

trap cleanup INT TERM

echo ""
echo "=========================================================="
echo "  FreeLingo listo:"
echo "  - Frontend: http://localhost:3000"
echo "  - Backend API: http://127.0.0.1:8000"
echo "  - Motor LLM: Antigravity CLI (/home/dan/.local/bin/agy)"
echo "  Presiona Ctrl+C para detener."
echo "=========================================================="

wait
