from __future__ import annotations

import os
import threading
from pathlib import Path
from tkinter import (
    BOTH,
    END,
    HORIZONTAL,
    LEFT,
    RIGHT,
    TOP,
    Button,
    Checkbutton,
    Entry,
    Frame,
    Label,
    LabelFrame,
    Listbox,
    Menu,
    PanedWindow,
    Scrollbar,
    StringVar,
    Text,
    Tk,
    filedialog,
    messagebox,
    ttk,
)

from .advice import build_advice_prompt
from .analyzer import build_report, render_markdown
from .detail_level import DetailLevel
from .display_names import set_localization_catalog
from .knowledge import build_knowledge_query, load_knowledge_records, retrieve_knowledge
from .localization import load_localization_catalog
from .report_language import ReportLanguage
from .save_reader import read_save
from .strategic_focus import StrategicFocus, focus_description
from .visibility import VisibilityMode


DEFAULT_SAVE_ROOT = Path.home() / "Documents" / "Paradox Interactive" / "Stellaris" / "save games"


class AdvisorApp:
    def __init__(self, root: Tk) -> None:
        self.root = root
        self.root.title("Stellaris Advisor")
        self.root.geometry("1180x760")
        self.root.minsize(980, 620)

        self.save_root_var = StringVar(value=str(DEFAULT_SAVE_ROOT))
        self.save_file_var = StringVar()
        self.localization_dir_var = StringVar(value=os.environ.get("STELLARIS_ADVISOR_LOCALIZATION_DIR", ""))
        self.knowledge_dir_var = StringVar()
        self.advice_focus_var = StringVar()
        self.language_var = StringVar(value=ReportLanguage.ZH.value)
        self.detail_level_var = StringVar(value=DetailLevel.STANDARD.value)
        self.visibility_var = StringVar(value=VisibilityMode.PLAYER_VISIBLE.value)
        self.strategic_focus_var = StringVar(value=StrategicFocus.BALANCED.value)
        self.output_mode_var = StringVar(value="report")
        self.rag_top_k_var = StringVar(value="0")
        self.status_var = StringVar(value="Ready")

        self._save_files: list[Path] = []
        self._build_menu()
        self._build_layout()
        self.refresh_saves()

    def _build_menu(self) -> None:
        menu = Menu(self.root)
        file_menu = Menu(menu, tearoff=False)
        file_menu.add_command(label="Open Save...", command=self.browse_save)
        file_menu.add_command(label="Save Output...", command=self.save_output)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.destroy)
        menu.add_cascade(label="File", menu=file_menu)
        self.root.config(menu=menu)

    def _build_layout(self) -> None:
        container = PanedWindow(self.root, orient=HORIZONTAL, sashwidth=6)
        container.pack(fill=BOTH, expand=True)

        left = Frame(container, padx=10, pady=10)
        right = Frame(container, padx=10, pady=10)
        container.add(left, minsize=360)
        container.add(right, minsize=540)

        self._build_save_panel(left)
        self._build_options_panel(left)
        self._build_output_panel(right)

    def _build_save_panel(self, parent: Frame) -> None:
        panel = LabelFrame(parent, text="Save File", padx=8, pady=8)
        panel.pack(fill=BOTH, expand=True)

        Label(panel, text="Save folder").pack(anchor="w")
        folder_row = Frame(panel)
        folder_row.pack(fill="x", pady=(2, 8))
        Entry(folder_row, textvariable=self.save_root_var).pack(side=LEFT, fill="x", expand=True)
        Button(folder_row, text="Browse", command=self.browse_save_root).pack(side=RIGHT, padx=(6, 0))

        button_row = Frame(panel)
        button_row.pack(fill="x", pady=(0, 8))
        Button(button_row, text="Refresh", command=self.refresh_saves).pack(side=LEFT)
        Button(button_row, text="Open .sav", command=self.browse_save).pack(side=LEFT, padx=(6, 0))

        list_frame = Frame(panel)
        list_frame.pack(fill=BOTH, expand=True)
        scrollbar = Scrollbar(list_frame)
        scrollbar.pack(side=RIGHT, fill="y")
        self.save_listbox = Listbox(list_frame, yscrollcommand=scrollbar.set, exportselection=False)
        self.save_listbox.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.config(command=self.save_listbox.yview)
        self.save_listbox.bind("<<ListboxSelect>>", self._select_listed_save)

        Label(panel, text="Selected save").pack(anchor="w", pady=(8, 0))
        Entry(panel, textvariable=self.save_file_var).pack(fill="x", pady=(2, 0))

    def _build_options_panel(self, parent: Frame) -> None:
        panel = LabelFrame(parent, text="Options", padx=8, pady=8)
        panel.pack(fill="x", pady=(10, 0))

        grid = Frame(panel)
        grid.pack(fill="x")

        self._option_row(grid, 0, "Language", self.language_var, [item.value for item in ReportLanguage])
        self._option_row(grid, 1, "Detail", self.detail_level_var, [item.value for item in DetailLevel])
        self._option_row(grid, 2, "Visibility", self.visibility_var, [item.value for item in VisibilityMode])
        self._option_row(grid, 3, "Focus", self.strategic_focus_var, [item.value for item in StrategicFocus])
        self._option_row(grid, 4, "Output", self.output_mode_var, ["report", "prompt"])

        Label(panel, text="Player question / advice focus").pack(anchor="w", pady=(8, 0))
        Entry(panel, textvariable=self.advice_focus_var).pack(fill="x", pady=(2, 6))

        Label(panel, text="Localization folder or .yml").pack(anchor="w")
        localization_row = Frame(panel)
        localization_row.pack(fill="x", pady=(2, 6))
        Entry(localization_row, textvariable=self.localization_dir_var).pack(side=LEFT, fill="x", expand=True)
        Button(localization_row, text="Browse", command=self.browse_localization).pack(side=RIGHT, padx=(6, 0))

        Label(panel, text="Knowledge folder/file").pack(anchor="w")
        knowledge_row = Frame(panel)
        knowledge_row.pack(fill="x", pady=(2, 6))
        Entry(knowledge_row, textvariable=self.knowledge_dir_var).pack(side=LEFT, fill="x", expand=True)
        Button(knowledge_row, text="Browse", command=self.browse_knowledge).pack(side=RIGHT, padx=(6, 0))

        rag_row = Frame(panel)
        rag_row.pack(fill="x", pady=(0, 8))
        Label(rag_row, text="RAG top K").pack(side=LEFT)
        ttk.Spinbox(rag_row, from_=0, to=20, textvariable=self.rag_top_k_var, width=6).pack(
            side=LEFT, padx=(8, 0)
        )

        Button(panel, text="Generate", command=self.generate).pack(fill="x")

    def _option_row(self, parent: Frame, row: int, label: str, variable: StringVar, values: list[str]) -> None:
        Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=2)
        combo = ttk.Combobox(parent, textvariable=variable, values=values, state="readonly", width=22)
        combo.grid(row=row, column=1, sticky="ew", padx=(10, 0), pady=2)
        parent.columnconfigure(1, weight=1)

    def _build_output_panel(self, parent: Frame) -> None:
        toolbar = Frame(parent)
        toolbar.pack(side=TOP, fill="x")
        Button(toolbar, text="Copy", command=self.copy_output).pack(side=LEFT)
        Button(toolbar, text="Save", command=self.save_output).pack(side=LEFT, padx=(6, 0))
        Label(toolbar, textvariable=self.status_var).pack(side=RIGHT)

        text_frame = Frame(parent)
        text_frame.pack(fill=BOTH, expand=True, pady=(8, 0))
        scrollbar = Scrollbar(text_frame)
        scrollbar.pack(side=RIGHT, fill="y")
        self.output = Text(text_frame, wrap="word", undo=False, yscrollcommand=scrollbar.set)
        self.output.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.config(command=self.output.yview)

    def browse_save_root(self) -> None:
        selected = filedialog.askdirectory(initialdir=self.save_root_var.get() or str(DEFAULT_SAVE_ROOT))
        if selected:
            self.save_root_var.set(selected)
            self.refresh_saves()

    def browse_save(self) -> None:
        selected = filedialog.askopenfilename(
            title="Select Stellaris save",
            initialdir=self.save_root_var.get() or str(DEFAULT_SAVE_ROOT),
            filetypes=[("Stellaris saves", "*.sav"), ("All files", "*.*")],
        )
        if selected:
            self.save_file_var.set(selected)

    def browse_localization(self) -> None:
        selected = filedialog.askdirectory(title="Select Stellaris install or localization folder")
        if selected:
            self.localization_dir_var.set(selected)

    def browse_knowledge(self) -> None:
        selected = filedialog.askdirectory(title="Select knowledge folder")
        if selected:
            self.knowledge_dir_var.set(selected)

    def refresh_saves(self) -> None:
        root = Path(self.save_root_var.get()).expanduser()
        self.save_listbox.delete(0, END)
        self._save_files = []
        if not root.exists():
            self.status_var.set("Save folder not found")
            return
        self._save_files = sorted(root.rglob("*.sav"), key=lambda path: path.stat().st_mtime, reverse=True)
        for path in self._save_files[:500]:
            try:
                label = str(path.relative_to(root))
            except ValueError:
                label = str(path)
            self.save_listbox.insert(END, label)
        self.status_var.set(f"Found {len(self._save_files)} saves")

    def _select_listed_save(self, _event: object) -> None:
        selection = self.save_listbox.curselection()
        if not selection:
            return
        index = selection[0]
        if index < len(self._save_files):
            self.save_file_var.set(str(self._save_files[index]))

    def generate(self) -> None:
        save_file = self.save_file_var.get().strip()
        if not save_file:
            messagebox.showwarning("Missing save", "Select a .sav file first.")
            return
        self.status_var.set("Working...")
        self.output.delete("1.0", END)
        thread = threading.Thread(target=self._generate_worker, args=(save_file,), daemon=True)
        thread.start()

    def _generate_worker(self, save_file: str) -> None:
        try:
            result = self._generate_output(save_file)
        except Exception as exc:  # noqa: BLE001 - GUI should show unexpected parser errors.
            self.root.after(0, self._show_error, exc)
            return
        self.root.after(0, self._show_output, result)

    def _generate_output(self, save_file: str) -> str:
        language = ReportLanguage(self.language_var.get())
        localization_dir = self.localization_dir_var.get().strip()
        if localization_dir:
            set_localization_catalog(load_localization_catalog(localization_dir, language))
        else:
            set_localization_catalog(None)

        save = read_save(save_file)
        report = build_report(
            save,
            VisibilityMode(self.visibility_var.get()),
            language,
            DetailLevel(self.detail_level_var.get()),
        )
        if self.output_mode_var.get() == "report":
            return render_markdown(report)

        strategic_focus = StrategicFocus(self.strategic_focus_var.get())
        knowledge_hits = []
        rag_top_k = int(self.rag_top_k_var.get() or "0")
        knowledge_dir = self.knowledge_dir_var.get().strip()
        if rag_top_k > 0:
            if not knowledge_dir:
                raise ValueError("RAG top K requires a knowledge folder/file.")
            records = load_knowledge_records(knowledge_dir)
            query = build_knowledge_query(
                report.summary,
                " ".join(
                    item
                    for item in [
                        self.advice_focus_var.get().strip(),
                        focus_description(strategic_focus, zh=(language is ReportLanguage.ZH)),
                    ]
                    if item
                ),
            )
            knowledge_hits = retrieve_knowledge(
                records,
                query,
                version=save.metadata.version,
                top_k=rag_top_k,
            )
        prompt = build_advice_prompt(
            report,
            self.advice_focus_var.get().strip(),
            knowledge_hits,
            strategic_focus,
        )
        return prompt.render()

    def _show_output(self, text: str) -> None:
        self.output.delete("1.0", END)
        self.output.insert("1.0", text)
        self.status_var.set("Done")

    def _show_error(self, exc: Exception) -> None:
        self.status_var.set("Error")
        messagebox.showerror("Stellaris Advisor", str(exc))

    def copy_output(self) -> None:
        text = self.output.get("1.0", END).strip()
        if not text:
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.status_var.set("Copied")

    def save_output(self) -> None:
        text = self.output.get("1.0", END).strip()
        if not text:
            return
        selected = filedialog.asksaveasfilename(
            title="Save output",
            defaultextension=".md",
            filetypes=[("Markdown", "*.md"), ("Text", "*.txt"), ("All files", "*.*")],
        )
        if selected:
            Path(selected).write_text(text + "\n", encoding="utf-8")
            self.status_var.set("Saved")


def main() -> int:
    root = Tk()
    AdvisorApp(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
