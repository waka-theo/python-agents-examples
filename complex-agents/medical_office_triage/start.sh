#!/bin/bash

# Medical Office Triage - Start Script
# Lance le frontend et le backend simultanément

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_PATH="/Users/theo/python-agents-examples/venv"

# Couleurs pour les logs
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Medical Office Triage ===${NC}"
echo ""

# Fonction de nettoyage à la fermeture
cleanup() {
    echo ""
    echo -e "${RED}Arrêt des services...${NC}"
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Lancer le backend (Python agent)
echo -e "${GREEN}[Backend]${NC} Démarrage de l'agent Python..."
source "$VENV_PATH/bin/activate"
cd "$SCRIPT_DIR"
python triage.py dev &
BACKEND_PID=$!

# Attendre que le backend soit prêt
sleep 3

# Lancer le frontend (Next.js)
echo -e "${GREEN}[Frontend]${NC} Démarrage du serveur Next.js..."
cd "$SCRIPT_DIR/frontend"
pnpm dev &
FRONTEND_PID=$!

echo ""
echo -e "${BLUE}=== Services démarrés ===${NC}"
echo -e "${GREEN}Frontend:${NC} http://localhost:3000"
echo -e "${GREEN}Backend:${NC}  Agent connecté à LiveKit Cloud"
echo ""
echo -e "Appuie sur ${RED}Ctrl+C${NC} pour arrêter les deux services."
echo ""

# Attendre que les deux processus se terminent
wait $BACKEND_PID $FRONTEND_PID
