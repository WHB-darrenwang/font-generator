#!/usr/bin/env bash
set -euo pipefail

VENV_DIR="venv"

# Check venv exists
if [ ! -d "$VENV_DIR" ]; then
    echo "Error: Virtual environment not found at '$VENV_DIR'."
    echo "Run ./setup.sh first to create it."
    exit 1
fi

source "$VENV_DIR/bin/activate"

# Install pyinstaller if missing
if ! python -c "import PyInstaller" 2>/dev/null; then
    echo "Installing PyInstaller..."
    pip install -r requirements-dev.txt
fi

echo "Building Font Maker..."
pyinstaller font_maker.spec --clean --noconfirm

# Ad-hoc codesign on macOS to reduce Gatekeeper friction
if [ -d "dist/Font Maker.app" ]; then
    echo "Ad-hoc signing the app..."
    codesign --force --deep --sign - "dist/Font Maker.app" 2>/dev/null || true
    echo ""
    echo "Build complete: dist/Font Maker.app"
    echo ""
    echo "Note: Recipients will see an 'unidentified developer' warning."
    echo "They can bypass it by right-clicking the app and choosing Open."
else
    echo "Build complete: dist/font_maker/"
fi
