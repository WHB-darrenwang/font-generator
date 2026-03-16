"""Font Maker - A desktop app for creating handwritten fonts."""

import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
import os
import shutil

from canvas_manager import CanvasManager
from glyph_list import GlyphListPanel
from char_sets import get_flat_char_list
from project import Project
from exporter import build_font


class FontMaker:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.root.title("Font Maker")
        self.root.configure(bg='#2b2b2b')
        w, h = 1050, 680
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

        # State
        self.project = Project()
        self.char_list = get_flat_char_list()
        self.current_char_index = 0
        self.current_char = self.char_list[0] if self.char_list else None

        self._setup_styles()
        self._setup_menu()
        self._setup_ui()
        self._update_status()

        self.root.bind('<Left>', self._on_left_key)
        self.root.bind('<Right>', self._on_right_key)

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Dark.TButton',
                        background='#444', foreground='white',
                        borderwidth=0, padding=(10, 5))
        style.map('Dark.TButton',
                  background=[('active', '#555'), ('pressed', '#333')],
                  foreground=[('active', 'white'), ('pressed', 'white')])

    def _setup_menu(self):
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="New Project...", command=self._new_project)
        file_menu.add_command(label="Open Project...", command=self._open_project)
        file_menu.add_separator()
        file_menu.add_command(label="Export as TTF...", command=lambda: self._export_font("ttf"))
        file_menu.add_command(label="Export as OTF...", command=lambda: self._export_font("otf"))
        file_menu.add_separator()
        file_menu.add_command(label="Quit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Clear Canvas", command=self._clear_canvas)
        edit_menu.add_command(label="Undo", command=lambda: self.canvas_mgr._undo())
        menubar.add_cascade(label="Edit", menu=edit_menu)

        self.root.config(menu=menubar)

    def _setup_ui(self):
        # Main container
        main = tk.Frame(self.root, bg='#2b2b2b')
        main.pack(fill=tk.BOTH, expand=True)

        # Left panel: glyph list
        self.glyph_panel = GlyphListPanel(main, on_select=self._on_glyph_select)
        self.glyph_panel.frame.pack(side=tk.LEFT, fill=tk.Y, padx=(5, 0), pady=5)

        # Center: canvas
        self.canvas_mgr = CanvasManager(main, on_modified=self._on_canvas_modified)
        self.canvas_mgr.frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Right panel: toolbar
        toolbar = tk.Frame(main, bg='#2b2b2b')
        toolbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 5), pady=5)

        # Current character display
        self.char_display = tk.Label(
            toolbar, text="A", font=('Helvetica', 36),
            bg='#2b2b2b', fg='white',
        )
        self.char_display.pack(pady=(5, 2))

        self.char_code_label = tk.Label(
            toolbar, text="U+0041", font=('Helvetica', 10),
            bg='#2b2b2b', fg='#888',
        )
        self.char_code_label.pack()

        # Tools
        tk.Label(toolbar, text="Tool", font=('Helvetica', 10, 'bold'),
                 bg='#2b2b2b', fg='#aaa').pack(pady=(10, 3))

        self.tool_var = tk.StringVar(value="pen")
        tool_frame = tk.Frame(toolbar, bg='#2b2b2b')
        tool_frame.pack()
        tk.Radiobutton(
            tool_frame, text="Pen", variable=self.tool_var, value="pen",
            command=self._on_tool_change, bg='#2b2b2b', fg='white',
            selectcolor='#444', activebackground='#2b2b2b',
        ).pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(
            tool_frame, text="Eraser", variable=self.tool_var, value="eraser",
            command=self._on_tool_change, bg='#2b2b2b', fg='white',
            selectcolor='#444', activebackground='#2b2b2b',
        ).pack(side=tk.LEFT, padx=5)

        # Thickness
        tk.Label(toolbar, text="Thickness", font=('Helvetica', 10, 'bold'),
                 bg='#2b2b2b', fg='#aaa').pack(pady=(10, 3))

        self.thickness_var = tk.IntVar(value=8)
        self.thickness_slider = tk.Scale(
            toolbar, from_=1, to=30, orient=tk.HORIZONTAL,
            variable=self.thickness_var, command=self._on_thickness_change,
            bg='#2b2b2b', fg='white', troughcolor='#444',
            highlightthickness=0, length=130,
        )
        self.thickness_slider.pack()

        # Clear button
        ttk.Button(
            toolbar, text="Clear Canvas", command=self._clear_canvas,
            style='Dark.TButton',
        ).pack(pady=(10, 3))

        # Navigation
        tk.Label(toolbar, text="Navigate", font=('Helvetica', 10, 'bold'),
                 bg='#2b2b2b', fg='#aaa').pack(pady=(10, 3))

        nav_frame = tk.Frame(toolbar, bg='#2b2b2b')
        nav_frame.pack()
        ttk.Button(
            nav_frame, text="< Prev", command=self._prev_glyph,
            style='Dark.TButton',
        ).pack(side=tk.LEFT, padx=3)
        ttk.Button(
            nav_frame, text="Next >", command=self._next_glyph,
            style='Dark.TButton',
        ).pack(side=tk.LEFT, padx=3)

        # Jump to character
        tk.Label(toolbar, text="Jump to", font=('Helvetica', 10, 'bold'),
                 bg='#2b2b2b', fg='#aaa').pack(pady=(10, 3))

        jump_frame = tk.Frame(toolbar, bg='#2b2b2b')
        jump_frame.pack()
        self.jump_entry = tk.Entry(jump_frame, width=5, font=('Helvetica', 16), justify='center')
        self.jump_entry.pack(side=tk.LEFT, padx=3)
        ttk.Button(
            jump_frame, text="Go", command=self._jump_to_char,
            style='Dark.TButton',
        ).pack(side=tk.LEFT, padx=3)
        self.jump_entry.bind('<Return>', lambda e: self._jump_to_char())

        # Export buttons
        tk.Label(toolbar, text="Export", font=('Helvetica', 10, 'bold'),
                 bg='#2b2b2b', fg='#aaa').pack(pady=(10, 3))

        export_frame = tk.Frame(toolbar, bg='#2b2b2b')
        export_frame.pack()
        ttk.Button(
            export_frame, text="TTF", command=lambda: self._export_font("ttf"),
            style='Dark.TButton',
        ).pack(side=tk.LEFT, padx=3)
        ttk.Button(
            export_frame, text="OTF", command=lambda: self._export_font("otf"),
            style='Dark.TButton',
        ).pack(side=tk.LEFT, padx=3)

        # Progress
        self.progress_label = tk.Label(
            toolbar, text="0 / 0 done", font=('Helvetica', 10),
            bg='#2b2b2b', fg='#aaa',
        )
        self.progress_label.pack(pady=(10, 3))

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = tk.Label(
            self.root, textvariable=self.status_var,
            bg='#333', fg='#aaa', anchor=tk.W, padx=10,
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _on_left_key(self, event):
        if event.widget != self.jump_entry:
            self._prev_glyph()

    def _on_right_key(self, event):
        if event.widget != self.jump_entry:
            self._next_glyph()

    def _on_tool_change(self):
        self.canvas_mgr.set_tool(self.tool_var.get())

    def _on_thickness_change(self, val):
        self.canvas_mgr.set_thickness(int(val))

    def _on_canvas_modified(self):
        """Called when canvas content changes. Auto-creates project if needed."""
        if self.project.project_dir is None:
            self._auto_create_project()

    def _on_glyph_select(self, char):
        """Called when user clicks a glyph in the list."""
        self._save_current_glyph()
        idx = self.glyph_panel.get_char_index(char)
        if idx >= 0:
            self.current_char_index = idx
            self.current_char = char
            self._load_current_glyph()
            self._update_status()

    def _save_current_glyph(self):
        """Save the current canvas to the project."""
        if self.current_char is None:
            return
        if self.project.project_dir is None:
            return
        if not self.canvas_mgr.is_blank():
            self.project.save_glyph(self.current_char, self.canvas_mgr.get_image())
            self.glyph_panel.mark_done(self.current_char)
        else:
            # If canvas is blank, remove the glyph
            self.project.delete_glyph(self.current_char)
            self.glyph_panel.mark_undone(self.current_char)

    def _load_current_glyph(self):
        """Load the current glyph from project onto canvas."""
        if self.current_char is None:
            return
        img = self.project.load_glyph(self.current_char)
        if img:
            self.canvas_mgr.load_image(img)
        else:
            self.canvas_mgr.clear()
        self.glyph_panel.select_char(self.current_char)

    def _prev_glyph(self):
        self._save_current_glyph()
        if self.current_char_index > 0:
            self.current_char_index -= 1
            self.current_char = self.char_list[self.current_char_index]
            self._load_current_glyph()
            self._update_status()

    def _next_glyph(self):
        self._save_current_glyph()
        if self.current_char_index < len(self.char_list) - 1:
            self.current_char_index += 1
            self.current_char = self.char_list[self.current_char_index]
            self._load_current_glyph()
            self._update_status()

    def _jump_to_char(self):
        text = self.jump_entry.get().strip()
        if not text:
            return
        # Take the first character
        char = text[0]
        if char in self.char_list:
            self._save_current_glyph()
            idx = self.char_list.index(char)
            self.current_char_index = idx
            self.current_char = char
            self._load_current_glyph()
            self._update_status()
            self.jump_entry.delete(0, tk.END)
        else:
            messagebox.showinfo("Not Found", f"Character '{char}' is not in the character set.")

    def _clear_canvas(self):
        self.canvas_mgr.clear()

    def _update_status(self):
        if self.current_char:
            self.char_display.config(text=self.current_char)
            self.char_code_label.config(text=f"U+{ord(self.current_char):04X}")
            idx = self.current_char_index + 1
            total = len(self.char_list)
            self.status_var.set(f"Drawing: {self.current_char} ({idx}/{total})")
        done = self.glyph_panel.get_done_count()
        total = self.glyph_panel.get_total_count()
        self.progress_label.config(text=f"{done} / {total} done")

    def _auto_create_project(self):
        """Auto-create a project in a temp-like location so drawing just works."""
        result = messagebox.askyesno(
            "Create Project",
            "You need a project to save your work.\nCreate one now?"
        )
        if result:
            self._new_project()

    def _new_project(self):
        name = simpledialog.askstring("New Project", "Font name:", initialvalue="MyFont")
        if not name:
            return
        dir_path = filedialog.askdirectory(title="Choose project directory")
        if not dir_path:
            return
        project_dir = os.path.join(dir_path, name)
        self.project.create_new(project_dir, font_name=name)
        self.root.title(f"Font Maker - {name}")
        self._load_current_glyph()
        self._update_status()

    def _open_project(self):
        dir_path = filedialog.askdirectory(title="Select project directory")
        if not dir_path:
            return
        try:
            self.project.open_project(dir_path)
        except FileNotFoundError:
            messagebox.showerror("Error", "No manifest.json found in the selected directory.")
            return

        self.root.title(f"Font Maker - {self.project.font_name}")

        # Mark done glyphs in the list
        for codepoint_str in self.project.glyphs_done:
            try:
                cp = int(codepoint_str[2:], 16)
                char = chr(cp)
                self.glyph_panel.mark_done(char)
            except (ValueError, IndexError):
                pass

        # Restore position
        self.current_char_index = min(self.project.current_index, len(self.char_list) - 1)
        self.current_char = self.char_list[self.current_char_index]
        self.thickness_var.set(self.project.settings.get("pen_thickness", 8))
        self._load_current_glyph()
        self._update_status()

    def _export_font(self, fmt="ttf"):
        if not self.project.project_dir:
            messagebox.showwarning("No Project", "Please create or open a project first.")
            return

        self._save_current_glyph()

        glyph_paths = self.project.get_all_glyph_paths()
        if not glyph_paths:
            messagebox.showwarning("No Glyphs", "No glyphs have been drawn yet.")
            return

        # Ask for font name before exporting
        font_name = simpledialog.askstring(
            "Font Name",
            "Name for your font:",
            initialvalue=self.project.font_name,
        )
        if not font_name:
            return
        self.project.font_name = font_name
        self.project.save_manifest()
        self.root.title(f"Font Maker - {font_name}")

        ext = f".{fmt}"
        type_label = "TrueType Font" if fmt == "ttf" else "OpenType Font"
        output_path = filedialog.asksaveasfilename(
            title=f"Export {fmt.upper()}",
            defaultextension=ext,
            filetypes=[(type_label, f"*{ext}")],
            initialfile=f"{font_name}{ext}",
        )
        if not output_path:
            return

        # Show progress
        progress_win = tk.Toplevel(self.root)
        progress_win.title("Exporting...")
        progress_win.geometry("300x80")
        progress_win.transient(self.root)
        progress_label = tk.Label(progress_win, text="Tracing glyphs...")
        progress_label.pack(pady=10)
        progress_bar = ttk.Progressbar(progress_win, length=250, mode='determinate')
        progress_bar.pack(pady=5)

        def update_progress(current, total):
            progress_bar['value'] = (current / total) * 100
            progress_label.config(text=f"Tracing glyph {current}/{total}...")
            progress_win.update()

        try:
            tolerance = self.project.settings.get("export_tolerance", 2.0)
            is_ttf = (fmt == "ttf")
            build_font(
                glyph_paths,
                font_name=self.project.font_name,
                style=self.project.style_name,
                output_path=output_path,
                tolerance=tolerance,
                progress_callback=update_progress,
                is_ttf=is_ttf,
            )
            progress_win.destroy()

            # Auto-install to macOS Font Book
            install_msg = ""
            fonts_dir = os.path.expanduser("~/Library/Fonts")
            if os.path.isdir(fonts_dir):
                font_filename = os.path.basename(output_path)
                install_path = os.path.join(fonts_dir, font_filename)
                try:
                    shutil.copy2(output_path, install_path)
                    install_msg = "\n\nInstalled to Font Book automatically."
                except Exception:
                    install_msg = "\n\nFailed to install to Font Book."

            messagebox.showinfo("Export Complete",
                                f"Font saved to:\n{output_path}\n\n"
                                f"Glyphs exported: {len(glyph_paths)}"
                                f"{install_msg}")
        except Exception as e:
            progress_win.destroy()
            messagebox.showerror("Export Error", str(e))

    def run(self):
        self.root.deiconify()
        self.root.lift()
        self.root.attributes('-topmost', True)
        self.root.after(100, lambda: self.root.attributes('-topmost', False))
        self.root.mainloop()


if __name__ == '__main__':
    app = FontMaker()
    app.run()
