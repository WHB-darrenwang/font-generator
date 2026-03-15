"""Project save/load: PNG per glyph + manifest.json."""

import json
import os
from datetime import date
from PIL import Image

CANVAS_SIZE = 512


class Project:
    def __init__(self):
        self.project_dir = None
        self.font_name = "MyFont"
        self.style_name = "Regular"
        self.glyphs_done = set()
        self.current_index = 0
        self.settings = {
            "pen_thickness": 8,
            "export_tolerance": 2.0,
        }

    def _glyph_filename(self, char):
        return f"U+{ord(char):04X}.png"

    def _glyphs_dir(self):
        return os.path.join(self.project_dir, "glyphs")

    def _manifest_path(self):
        return os.path.join(self.project_dir, "manifest.json")

    def create_new(self, project_dir, font_name="MyFont"):
        """Create a new project at the given directory."""
        self.project_dir = project_dir
        self.font_name = font_name
        self.glyphs_done = set()
        self.current_index = 0

        os.makedirs(self._glyphs_dir(), exist_ok=True)
        self.save_manifest()

    def open_project(self, project_dir):
        """Open an existing project."""
        self.project_dir = project_dir
        manifest_path = self._manifest_path()
        if not os.path.exists(manifest_path):
            raise FileNotFoundError("No manifest.json found in project directory")

        with open(manifest_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.font_name = data.get("font_name", "MyFont")
        self.style_name = data.get("style_name", "Regular")
        self.current_index = data.get("current_glyph_index", 0)
        self.glyphs_done = set(data.get("glyphs_done", []))
        self.settings.update(data.get("settings", {}))

    def save_manifest(self):
        """Save the project manifest."""
        if not self.project_dir:
            return
        data = {
            "font_name": self.font_name,
            "style_name": self.style_name,
            "canvas_size": CANVAS_SIZE,
            "created": str(date.today()),
            "last_modified": str(date.today()),
            "current_glyph_index": self.current_index,
            "glyphs_done": sorted(self.glyphs_done),
            "settings": self.settings,
        }
        with open(self._manifest_path(), 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def save_glyph(self, char, pil_image):
        """Save a glyph image as PNG."""
        if not self.project_dir:
            return
        filepath = os.path.join(self._glyphs_dir(), self._glyph_filename(char))
        pil_image.save(filepath)
        codepoint = f"U+{ord(char):04X}"
        self.glyphs_done.add(codepoint)
        self.save_manifest()

    def load_glyph(self, char):
        """Load a glyph image. Returns PIL Image or None."""
        if not self.project_dir:
            return None
        filepath = os.path.join(self._glyphs_dir(), self._glyph_filename(char))
        if os.path.exists(filepath):
            return Image.open(filepath).convert('L')
        return None

    def delete_glyph(self, char):
        """Delete a glyph's saved image."""
        if not self.project_dir:
            return
        filepath = os.path.join(self._glyphs_dir(), self._glyph_filename(char))
        if os.path.exists(filepath):
            os.remove(filepath)
        codepoint = f"U+{ord(char):04X}"
        self.glyphs_done.discard(codepoint)
        self.save_manifest()

    def is_glyph_done(self, char):
        codepoint = f"U+{ord(char):04X}"
        return codepoint in self.glyphs_done

    def get_all_glyph_paths(self):
        """Return dict of char -> PNG path for all saved glyphs."""
        if not self.project_dir:
            return {}
        result = {}
        glyphs_dir = self._glyphs_dir()
        if not os.path.exists(glyphs_dir):
            return {}
        for fname in os.listdir(glyphs_dir):
            if fname.startswith("U+") and fname.endswith(".png"):
                codepoint_str = fname.replace(".png", "")
                try:
                    codepoint = int(codepoint_str[2:], 16)
                    char = chr(codepoint)
                    result[char] = os.path.join(glyphs_dir, fname)
                except ValueError:
                    pass
        return result
