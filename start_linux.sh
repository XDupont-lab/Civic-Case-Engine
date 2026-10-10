#!/usr/bin/env bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

if [ -f ".venv_bu/bin/python" ]; then
    PYTHON_BIN=".venv_bu/bin/python"
else
    PYTHON_BIN="python3"
fi

while true; do
    clear
    echo "======================================================================="
    echo "        🏛️  CIVIC CASE ENGINE — CIVIC EXOSKELETON HUB (LINUX)          "
    echo "======================================================================="
    echo ""
    echo " [0] Inrichtings- & Onboarding Wizard (bootstrap.py)"
    echo " [1] Multi-Model Dialectic Audit (_engine/audit_engine.py)"
    echo " [2] Forensische Tijdlijn & Hashes (_engine/timeline_weaver.py)"
    echo " [3] Termijnen & Dwangsommen Tracker (_engine/statutory_clock.py)"
    echo " [4] Bank CSV Auditen op bronheffingen & huur (_engine/bank_audit.py)"
    echo " [5] Procesbundel Exporteren met SHA-256 (_engine/case_bundler.py)"
    echo " [6] Chunk-Audit v0.3 — Cognitieve Werkgeheugentoets (_engine/chunk_audit.py)"
    echo " [7] Afsluiten"
    echo ""
    read -p "Kies een optie (0-7): " opt

    case "$opt" in
        0)
            $PYTHON_BIN bootstrap.py
            ;;
        1)
            $PYTHON_BIN _engine/audit_engine.py
            ;;
        2)
            $PYTHON_BIN _engine/timeline_weaver.py
            ;;
        3)
            $PYTHON_BIN _engine/statutory_clock.py
            ;;
        4)
            $PYTHON_BIN _engine/bank_audit.py
            ;;
        5)
            $PYTHON_BIN _engine/case_bundler.py
            ;;
        6)
            echo ""
            read -p "Voer pad in naar concept (Enter voor nieuwste in Outgoing_Drafts/): " doc_path
            if [ -z "$doc_path" ]; then
                doc_path=$(ls -t Outgoing_Drafts/*.md 2>/dev/null | head -n 1)
            fi
            if [ -n "$doc_path" ] && [ -f "$doc_path" ]; then
                $PYTHON_BIN _engine/chunk_audit.py "$doc_path"
            else
                echo "[!] Geen geldig markdown document gevonden in Outgoing_Drafts/."
            fi
            ;;
        7)
            echo "Tot ziens!"
            exit 0
            ;;
        *)
            echo "Ongeldige keuze."
            ;;
    esac

    echo ""
    read -p "Druk op Enter om terug te keren naar het hoofdmenu..." dummy
done
