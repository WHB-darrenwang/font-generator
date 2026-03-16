#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

echo "=== Font Maker DMG Builder ==="

# Ensure venv exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Run ./setup.sh first."
    exit 1
fi

PIP="./venv/bin/pip"
PYTHON="./venv/bin/python"

# Install build dependencies
echo "Installing build dependencies..."
$PIP install -q py2app dmgbuild

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build dist

# Build the .app bundle with py2app
echo "Building Font Maker.app..."
$PYTHON setup.py py2app

# Verify the .app was created
APP_PATH="dist/Font Maker.app"
if [ ! -d "$APP_PATH" ]; then
    echo "ERROR: Font Maker.app was not created."
    exit 1
fi
echo "Font Maker.app built successfully."

# Copy missing dylibs into the app bundle
# py2app doesn't always bundle dylibs that .so extensions link to via @rpath
echo "Fixing dynamic library references..."
FRAMEWORKS_DIR="$APP_PATH/Contents/Frameworks"
mkdir -p "$FRAMEWORKS_DIR"

PYTHON_LIB_DIR=$($PYTHON -c "import sys; print(getattr(sys, 'real_prefix', getattr(sys, 'base_prefix', sys.prefix)) + '/lib')")
echo "Python lib dir: $PYTHON_LIB_DIR"

# Find all @rpath dylibs needed by bundled .so files and copy them
for dylib in $(find "$APP_PATH/Contents/Resources/lib" -name "*.so" -exec otool -L {} \; 2>/dev/null | grep "@rpath" | awk '{print $1}' | sed 's|@rpath/||' | sort -u); do
    if [ ! -f "$FRAMEWORKS_DIR/$dylib" ]; then
        src="$PYTHON_LIB_DIR/$dylib"
        if [ -f "$src" ]; then
            cp "$src" "$FRAMEWORKS_DIR/"
            echo "  Copied $dylib"
        else
            echo "  WARNING: $dylib not found in $PYTHON_LIB_DIR"
        fi
    fi
done

# Build the DMG
DMG_PATH="dist/FontMaker.dmg"
echo "Building DMG..."
$PYTHON -m dmgbuild -s dmg_settings.py "Font Maker" "$DMG_PATH"

if [ -f "$DMG_PATH" ]; then
    echo ""
    echo "=== Build complete ==="
    echo "DMG: $DMG_PATH"
    echo "Size: $(du -h "$DMG_PATH" | cut -f1)"
else
    echo "ERROR: DMG was not created."
    exit 1
fi
