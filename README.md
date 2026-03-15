# Font Maker

A desktop application for creating handwritten fonts. Draw glyphs on a canvas and export them as TTF or OTF font files.

## Features

- Pen and eraser tools with adjustable thickness
- Support for uppercase, lowercase, digits, punctuation, and Chinese (GB2312) characters
- Undo support (Cmd/Ctrl+Z)
- Project save/load with per-glyph PNG storage
- Export to TTF (TrueType) or OTF (OpenType)
- Bitmap-to-vector tracing for clean font outlines

## Requirements

- Python 3.10+
- Tkinter (usually included with Python; on some Linux distros install `python3-tk`)

## Quick Start

```bash
./setup.sh   # creates venv and installs dependencies
./run.sh     # launches Font Maker
```

## Manual Setup

```bash
git clone <repo-url>
cd fonts
python3 -m venv venv
source venv/bin/activate      # macOS/Linux
# venv\Scripts\activate       # Windows
pip install -r requirements.txt
python font_maker.py
```

## Usage

1. **Create a project** — On first draw or via File > New Project, choose a name and directory. Glyphs are saved automatically as PNGs.
2. **Draw glyphs** — Use the pen tool to draw each character. Switch between characters with the left/right arrow keys, the glyph list, or the "Jump to" field.
3. **Tools** — Toggle between Pen and Eraser in the toolbar. Adjust thickness with the slider.
4. **Export** — Click TTF or OTF (or use File > Export) to generate a font file. You'll be prompted for a font name and save location.
5. **Reopen a project** — Use File > Open Project to continue where you left off.
