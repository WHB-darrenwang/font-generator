"""Scrollable glyph list panel with category headers and done/pending indicators."""

import tkinter as tk
from char_sets import get_all_chars


class GlyphListPanel:
    def __init__(self, parent, on_select):
        self.parent = parent
        self.on_select = on_select
        self.done_set = set()  # Set of characters that have been drawn

        self.frame = tk.Frame(parent, width=180)
        self.frame.pack_propagate(False)

        # Header
        tk.Label(self.frame, text="Glyphs", font=('Helvetica', 12, 'bold')).pack(pady=(5, 2))

        # Category filter
        self.categories = get_all_chars()
        self.flat_chars = []
        for _, chars in self.categories:
            self.flat_chars.extend(chars)

        # Category selector
        cat_frame = tk.Frame(self.frame)
        cat_frame.pack(fill=tk.X, padx=5, pady=2)
        self.cat_var = tk.StringVar(value="All")
        cat_names = ["All"] + [name for name, _ in self.categories]
        self.cat_menu = tk.OptionMenu(cat_frame, self.cat_var, *cat_names, command=self._filter_category)
        self.cat_menu.config(width=14)
        self.cat_menu.pack(fill=tk.X)

        # Listbox with scrollbar
        list_frame = tk.Frame(self.frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=2)

        self.scrollbar = tk.Scrollbar(list_frame)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.listbox = tk.Listbox(
            list_frame,
            yscrollcommand=self.scrollbar.set,
            font=('Helvetica', 14),
            selectmode=tk.SINGLE,
            activestyle='none',
        )
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.config(command=self.listbox.yview)

        self.listbox.bind('<<ListboxSelect>>', self._on_listbox_select)

        # Track which chars are shown in the listbox
        self.displayed_chars = []
        self._populate_all()

    def _populate_all(self):
        self.listbox.delete(0, tk.END)
        self.displayed_chars = []
        for name, chars in self.categories:
            # Category header
            self.listbox.insert(tk.END, f"── {name} ──")
            self.displayed_chars.append(None)  # None = header
            self.listbox.itemconfig(tk.END, fg='#888', selectbackground='#333')
            for c in chars:
                prefix = "● " if c in self.done_set else "○ "
                display = f"{prefix}{c}  (U+{ord(c):04X})"
                self.listbox.insert(tk.END, display)
                self.displayed_chars.append(c)
                if c in self.done_set:
                    self.listbox.itemconfig(tk.END, fg='#4CAF50')

    def _filter_category(self, selection):
        self.listbox.delete(0, tk.END)
        self.displayed_chars = []
        if selection == "All":
            self._populate_all()
            return
        for name, chars in self.categories:
            if name == selection:
                for c in chars:
                    prefix = "● " if c in self.done_set else "○ "
                    display = f"{prefix}{c}  (U+{ord(c):04X})"
                    self.listbox.insert(tk.END, display)
                    self.displayed_chars.append(c)
                    if c in self.done_set:
                        self.listbox.itemconfig(tk.END, fg='#4CAF50')
                break

    def _on_listbox_select(self, event):
        sel = self.listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        if idx < len(self.displayed_chars):
            char = self.displayed_chars[idx]
            if char is not None:  # Skip headers
                self.on_select(char)

    def mark_done(self, char):
        self.done_set.add(char)
        self._refresh_display()

    def mark_undone(self, char):
        self.done_set.discard(char)
        self._refresh_display()

    def _refresh_display(self):
        """Refresh the listbox colors without rebuilding."""
        for i, c in enumerate(self.displayed_chars):
            if c is None:
                continue
            if c in self.done_set:
                self.listbox.itemconfig(i, fg='#4CAF50')
            else:
                self.listbox.itemconfig(i, fg='white')

    def select_char(self, char):
        """Highlight and scroll to a character in the list."""
        for i, c in enumerate(self.displayed_chars):
            if c == char:
                self.listbox.selection_clear(0, tk.END)
                self.listbox.selection_set(i)
                self.listbox.see(i)
                return True
        return False

    def get_char_index(self, char):
        """Get the index of a character in the flat list."""
        try:
            return self.flat_chars.index(char)
        except ValueError:
            return -1

    def get_total_count(self):
        return len(self.flat_chars)

    def get_done_count(self):
        return len(self.done_set)
