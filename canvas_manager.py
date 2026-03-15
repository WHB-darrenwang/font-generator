"""Drawing canvas with pen/eraser tools and undo support."""

import tkinter as tk
from PIL import Image, ImageDraw, ImageTk

INTERNAL_SIZE = 512   # Full-res PIL image for export
DISPLAY_SIZE = 256    # Smaller canvas the user draws on
SCALE = INTERNAL_SIZE / DISPLAY_SIZE  # 2x
MAX_UNDO = 20


class CanvasManager:
    def __init__(self, parent, on_modified=None):
        self.parent = parent
        self.on_modified = on_modified

        # Tool state
        self.tool = "pen"  # "pen" or "eraser"
        self.thickness = 8  # thickness in display pixels
        self.drawing = False

        # Undo stack
        self.undo_stack = []

        # PIL image at full resolution (grayscale: black bg, white strokes)
        self.pil_image = Image.new('L', (INTERNAL_SIZE, INTERNAL_SIZE), 0)
        self.draw = ImageDraw.Draw(self.pil_image)

        # Tkinter canvas at display size
        self.frame = tk.Frame(parent)
        self.canvas = tk.Canvas(
            self.frame,
            width=DISPLAY_SIZE,
            height=DISPLAY_SIZE,
            bg='black',
            cursor='crosshair',
            highlightthickness=1,
            highlightbackground='#555',
        )
        self.canvas.pack(padx=5, pady=5)

        # Draw guide lines
        self._draw_guides()

        # Mouse bindings
        self.canvas.bind('<ButtonPress-1>', self._on_press)
        self.canvas.bind('<B1-Motion>', self._on_drag)
        self.canvas.bind('<ButtonRelease-1>', self._on_release)

        # Keyboard undo
        self.canvas.bind_all('<Command-z>', self._undo)
        self.canvas.bind_all('<Control-z>', self._undo)

        # Track last position for smooth lines (display coords)
        self.last_x = None
        self.last_y = None

    def _draw_guides(self):
        """Draw baseline/ascender guide lines on the display canvas."""
        self.canvas.delete('guide')
        guides = [
            (int(DISPLAY_SIZE * 0.10), '#333', 'ascender'),
            (int(DISPLAY_SIZE * 0.80), '#333', 'baseline'),
            (int(DISPLAY_SIZE * 0.95), '#222', 'descender'),
        ]
        for y, color, tag in guides:
            self.canvas.create_line(
                0, y, DISPLAY_SIZE, y,
                fill=color, dash=(4, 4), tags=('guide', tag)
            )

    def _on_press(self, event):
        self.drawing = True
        self._save_undo_snapshot()
        self.last_x = event.x
        self.last_y = event.y
        self._draw_point(event.x, event.y)

    def _on_drag(self, event):
        if not self.drawing:
            return
        if self.last_x is not None:
            self._draw_line(self.last_x, self.last_y, event.x, event.y)
        self.last_x = event.x
        self.last_y = event.y

    def _on_release(self, event):
        self.drawing = False
        self.last_x = None
        self.last_y = None
        if self.on_modified:
            self.on_modified()

    def _draw_point(self, x, y):
        """Draw a point at display coords (x, y), and scaled on the PIL image."""
        r = self.thickness // 2
        color = 255 if self.tool == "pen" else 0
        tk_color = 'white' if self.tool == "pen" else 'black'

        # Draw on display canvas
        self.canvas.create_oval(
            x - r, y - r, x + r, y + r,
            fill=tk_color, outline=tk_color, tags='stroke'
        )

        # Draw on internal PIL image (scaled up)
        ix, iy = x * SCALE, y * SCALE
        ir = r * SCALE
        self.draw.ellipse([ix - ir, iy - ir, ix + ir, iy + ir], fill=color)

    def _draw_line(self, x1, y1, x2, y2):
        """Draw a line segment at display coords, and scaled on the PIL image."""
        color = 255 if self.tool == "pen" else 0
        tk_color = 'white' if self.tool == "pen" else 'black'
        w = self.thickness

        # Draw on display canvas
        self.canvas.create_line(
            x1, y1, x2, y2,
            fill=tk_color, width=w, capstyle=tk.ROUND, tags='stroke'
        )
        r = w // 2
        self.canvas.create_oval(
            x2 - r, y2 - r, x2 + r, y2 + r,
            fill=tk_color, outline=tk_color, tags='stroke'
        )

        # Draw on internal PIL image (scaled up)
        iw = int(w * SCALE)
        ix1, iy1 = x1 * SCALE, y1 * SCALE
        ix2, iy2 = x2 * SCALE, y2 * SCALE
        self.draw.line([ix1, iy1, ix2, iy2], fill=color, width=iw)
        ir = iw // 2
        self.draw.ellipse([ix2 - ir, iy2 - ir, ix2 + ir, iy2 + ir], fill=color)

    def _save_undo_snapshot(self):
        self.undo_stack.append(self.pil_image.copy())
        if len(self.undo_stack) > MAX_UNDO:
            self.undo_stack.pop(0)

    def _undo(self, event=None):
        if not self.undo_stack:
            return
        self.pil_image = self.undo_stack.pop()
        self.draw = ImageDraw.Draw(self.pil_image)
        self._refresh_canvas_from_pil()

    def _refresh_canvas_from_pil(self):
        """Redraw the tkinter canvas from the PIL image (downscaled for display)."""
        self.canvas.delete('stroke')
        display_img = self.pil_image.resize((DISPLAY_SIZE, DISPLAY_SIZE), Image.LANCZOS)
        self._tk_photo = ImageTk.PhotoImage(display_img)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self._tk_photo, tags='stroke')
        self._draw_guides()

    def clear(self):
        """Clear the canvas."""
        self._save_undo_snapshot()
        self.pil_image = Image.new('L', (INTERNAL_SIZE, INTERNAL_SIZE), 0)
        self.draw = ImageDraw.Draw(self.pil_image)
        self.canvas.delete('stroke')
        self._draw_guides()
        if self.on_modified:
            self.on_modified()

    def get_image(self):
        """Return a copy of the full-resolution PIL image."""
        return self.pil_image.copy()

    def load_image(self, img):
        """Load a PIL image onto the canvas."""
        self.undo_stack.clear()
        self.pil_image = img.copy().convert('L').resize((INTERNAL_SIZE, INTERNAL_SIZE))
        self.draw = ImageDraw.Draw(self.pil_image)
        self._refresh_canvas_from_pil()

    def is_blank(self):
        """Check if the canvas is empty."""
        return self.pil_image.getbbox() is None

    def set_tool(self, tool):
        self.tool = tool

    def set_thickness(self, thickness):
        self.thickness = int(thickness)
