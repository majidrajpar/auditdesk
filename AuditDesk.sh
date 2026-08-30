#!/usr/bin/env bash
# AuditDesk Universal 1-Click Launcher (macOS & Linux)

echo "========================================================"
echo "  Starting AuditDesk Internal Audit Workbench..."
echo "========================================================"
echo ""

# 1. Detect Python
PY_CMD=""
if command -v python3 &>/dev/null; then
    PY_CMD="python3"
elif command -v python &>/dev/null; then
    PY_CMD="python"
fi

if [ -z "$PY_CMD" ]; then
    echo "========================================================"
    echo "  [NOTICE] Python 3 was not detected on this system."
    echo "========================================================"
    echo "Please install Python 3 (e.g. brew install python3 or sudo apt install python3)"
    echo "Opening https://www.python.org/downloads/ ..."
    if command -v open &>/dev/null; then
        open "https://www.python.org/downloads/"
    elif command -v xdg-open &>/dev/null; then
        xdg-open "https://www.python.org/downloads/"
    fi
    exit 1
fi

# 2. Check and auto-install python-docx
if ! $PY_CMD -c "import docx" &>/dev/null; then
    echo "Installing required reporting engine (python-docx)..."
    $PY_CMD -m pip install python-docx --quiet
fi

# 3. Locate script directory and launch
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "[OK] Python detected: $($PY_CMD --version)"
echo "Launching AuditDesk application..."
$PY_CMD server.py
