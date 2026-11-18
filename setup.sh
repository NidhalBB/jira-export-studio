#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Installing Jira Export Studio..."

if [ ! -d "$SCRIPT_DIR/.venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv "$SCRIPT_DIR/.venv"
fi

echo "Activating virtual environment and installing dependencies..."
source "$SCRIPT_DIR/.venv/bin/activate"
pip install -q -r "$SCRIPT_DIR/requirements.txt"

echo ""
echo "✓ Setup complete!"
echo ""
echo "To start the app:"
echo "  source .venv/bin/activate"
echo "  python app.py"
echo ""
