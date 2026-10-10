#!/usr/bin/env bash
set -e

echo "=========================================================="
echo "🏛️  Civic Case Engine — Linux Setup (Linux Mint / Ubuntu)"
echo "=========================================================="

# Controleer python3 en git
if ! command -v python3 &> /dev/null; then
    echo "[!] python3 is niet gevonden. Installeer met: sudo apt install python3 python3-venv python3-pip"
    exit 1
fi

if ! command -v git &> /dev/null; then
    echo "[!] git is niet gevonden. Installeer met: sudo apt install git"
    exit 1
fi

# Draai de autonome environment provisioner
python3 setup_environment.py

chmod +x start_linux.sh 2>/dev/null || true
echo ""
echo "✅ Setup voltooid! Je kunt de engine nu starten met: ./start_linux.sh"
