#!/usr/bin/env bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

if [ -f ".venv_bu/bin/python" ]; then
    PYTHON_BIN=".venv_bu/bin/python"
else
    PYTHON_BIN="python3"
fi

echo "=========================================================="
echo "🏛️  Civic Case Engine — Start Cockpit (Linux)"
echo "=========================================================="

$PYTHON_BIN bootstrap.py
