#!/usr/bin/env python3

import os
import queue
import re
import subprocess
import sys
import threading
from pathlib import Path

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from LLM.zeiss_gateway_client import ZeissLLMGatewayClient


class FrameworkUI(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Selector Framework UI")
        self.geometry("1100x760")
        self.minsize(980, 680)

        self.project_root = Path(__file__).resolve().parents[1]
        self.run_script = self.project_root / "scripts" / "run.py"
        self.default_prompt = self.project_root / "LLM" / "prompts" / "generate_helper_js_prompt.txt"

        self.process = None
        self.output_queue: "queue.Queue[str]" = queue.Queue()
        self.last_helper_file = None
        self.model_choices = ["gpt-4o", "gpt-4o-mini"]

        self._init_style()
        self._init_state()
        self._build_ui()
        self.after(250, self._refresh_models)
        self.after(120, self._drain_log_queue)

    def _init_style(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        bg = "#f7f9fc"
        card = "#ffffff"
        text = "#1f2937"

        self.configure(bg=bg)

        style.configure("Root.TFrame", background=bg)
        style.configure("Card.TLabelframe", background=card, foreground=text)
        style.configure("Card.TLabelframe.Label", background=card, foreground=text, font=("Segoe UI", 10, "bold"))
        style.configure("TLabel", background=bg, foreground=text, font=("Segoe UI", 10))
        style.configure("Field.TLabel", background=card, foreground=text, font=("Segoe UI", 10))
        style.configure("Primary.TButton", font=("Segoe UI", 10, "bold"), padding=(10, 8))
        style.configure("TButton", font=("Segoe UI", 10), padding=(8, 6))
        style.configure("TEntry", padding=4)
        style.configure("TCombobox", padding=3)

    def _init_state(self) -> None:
        self.url_var = tk.StringVar()
        self.mode_var = tk.StringVar(value="all")
        self.workflow_var = tk.StringVar(value="generate-js")
        self.headless_var = tk.BooleanVar(value=True)

        self.llm_api_key_var = tk.StringVar(value=os.getenv("ZEISS_SUB_KEY", ""))
        self.llm_model_var = tk.StringVar(value="gpt-4o")
        self.llm_base_url_var = tk.StringVar(value="https://api.genai.zeiss.com/llm")
        self.llm_temperature_var = tk.StringVar(value="0.2")
        self.llm_max_tokens_var = tk.StringVar(value="2500")
        self.prompt_file_var = tk.StringVar(value=str(self.default_prompt))
        self.show_key_var = tk.BooleanVar(value=False)

        self.status_var = tk.StringVar(value="Ready")

    def _build_ui(self) -> None:
        root = ttk.Frame(self, style="Root.TFrame", padding=14)
        root.pack(fill=tk.BOTH, expand=True)

        header = ttk.Frame(root, style="Root.TFrame")
        header.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(
            header,
            text="Playwright Selector Framework",
            font=("Segoe UI", 16, "bold"),
        ).pack(anchor=tk.W)
        ttk.Label(
            header,
            text="URL scrape -> selector prediction -> optional LLM helper generation",
            font=("Segoe UI", 10),
        ).pack(anchor=tk.W, pady=(2, 0))

        config_card = ttk.LabelFrame(root, text="Configuration", style="Card.TLabelframe", padding=12)
        config_card.pack(fill=tk.X)

        config_card.columnconfigure(1, weight=1)
        config_card.columnconfigure(3, weight=1)

        self._row_entry(config_card, 0, "Target URL", self.url_var)
        self._row_combobox(config_card, 1, "Scrape Mode", self.mode_var, ["all", "interactive", "text"])
        self._row_combobox(
            config_card,
            1,
            "Workflow",
            self.workflow_var,
            ["generate-js", "predict"],
            col=2,
        )

        headless_frame = ttk.Frame(config_card)
        headless_frame.grid(row=2, column=0, columnspan=2, sticky="w", pady=(6, 2))
        ttk.Checkbutton(headless_frame, text="Headless Browser", variable=self.headless_var).pack(side=tk.LEFT)

        llm_card = ttk.LabelFrame(root, text="LLM Settings", style="Card.TLabelframe", padding=12)
        llm_card.pack(fill=tk.X, pady=(10, 0))

        llm_card.columnconfigure(1, weight=1)
        llm_card.columnconfigure(3, weight=1)

        self._row_entry(llm_card, 0, "Subscription Key", self.llm_api_key_var, show="*")
        show_key_chk = ttk.Checkbutton(
            llm_card,
            text="Show key",
            variable=self.show_key_var,
            command=self._toggle_key_visibility,
        )
        show_key_chk.grid(row=0, column=2, sticky="w", padx=(10, 6))

        ttk.Label(llm_card, text="Base URL", style="Field.TLabel").grid(row=1, column=0, sticky="w", pady=(6, 2), padx=(0, 8))
        ttk.Entry(llm_card, textvariable=self.llm_base_url_var).grid(row=1, column=1, columnspan=3, sticky="ew", pady=(6, 2), padx=(0, 10))

        ttk.Label(llm_card, text="Model", style="Field.TLabel").grid(row=2, column=0, sticky="w", pady=(6, 2), padx=(0, 8))
        self.model_cb = ttk.Combobox(
            llm_card,
            textvariable=self.llm_model_var,
            values=self.model_choices,
            state="readonly",
        )
        self.model_cb.grid(row=2, column=1, sticky="ew", pady=(6, 2), padx=(0, 10))

        ttk.Button(llm_card, text="Refresh Models", command=self._refresh_models).grid(
            row=2,
            column=2,
            columnspan=2,
            sticky="w",
            pady=(6, 2),
        )

        self._row_entry(llm_card, 3, "Temperature", self.llm_temperature_var)
        self._row_entry(llm_card, 3, "Max Tokens", self.llm_max_tokens_var, col=2)

        ttk.Label(llm_card, text="Prompt Template", style="Field.TLabel").grid(row=4, column=0, sticky="w", pady=(8, 2))
        prompt_row = ttk.Frame(llm_card)
        prompt_row.grid(row=4, column=1, columnspan=3, sticky="ew", pady=(8, 2))
        prompt_row.columnconfigure(0, weight=1)
        ttk.Entry(prompt_row, textvariable=self.prompt_file_var).grid(row=0, column=0, sticky="ew")
        ttk.Button(prompt_row, text="Browse", command=self._browse_prompt_file).grid(row=0, column=1, padx=(8, 0))

        controls = ttk.Frame(root, style="Root.TFrame")
        controls.pack(fill=tk.X, pady=(12, 8))

        self.run_btn = ttk.Button(controls, text="Run Workflow", style="Primary.TButton", command=self._start_run)
        self.run_btn.pack(side=tk.LEFT)

        self.stop_btn = ttk.Button(controls, text="Stop", command=self._stop_run, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=(8, 0))

        self.open_helper_btn = ttk.Button(
            controls,
            text="Open Generated Helper JS",
            command=self._open_helper_file,
            state=tk.DISABLED,
        )
        self.open_helper_btn.pack(side=tk.LEFT, padx=(8, 0))

        ttk.Label(controls, textvariable=self.status_var).pack(side=tk.RIGHT)

        log_card = ttk.LabelFrame(root, text="Live Processing Log", style="Card.TLabelframe", padding=8)
        log_card.pack(fill=tk.BOTH, expand=True)

        log_frame = ttk.Frame(log_card)
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = tk.Text(
            log_frame,
            wrap=tk.WORD,
            bg="#0f172a",
            fg="#e5e7eb",
            insertbackground="#e5e7eb",
            font=("Consolas", 10),
            relief=tk.FLAT,
            padx=10,
            pady=10,
        )
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        log_scroll = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.configure(yscrollcommand=log_scroll.set)

    def _row_entry(self, parent, row, label, variable, col=0, show=None):
        ttk.Label(parent, text=label, style="Field.TLabel").grid(row=row, column=col, sticky="w", pady=(6, 2), padx=(0, 8))
        entry = ttk.Entry(parent, textvariable=variable, show=show)
        entry.grid(row=row, column=col + 1, sticky="ew", pady=(6, 2), padx=(0, 10))
        if label == "Subscription Key":
            self.key_entry = entry

    def _row_combobox(self, parent, row, label, variable, values, col=0):
        ttk.Label(parent, text=label, style="Field.TLabel").grid(row=row, column=col, sticky="w", pady=(6, 2), padx=(0, 8))
        cb = ttk.Combobox(parent, textvariable=variable, values=values, state="readonly")
        cb.grid(row=row, column=col + 1, sticky="ew", pady=(6, 2), padx=(0, 10))

    def _toggle_key_visibility(self) -> None:
        self.key_entry.configure(show="" if self.show_key_var.get() else "*")

    def _fetch_models_worker(self, api_key: str, base_url: str) -> None:
        try:
            client = ZeissLLMGatewayClient(base_url=base_url, api_key=api_key, timeout=45)
            data = client.list_models(version="v1")

            models = []
            if isinstance(data, dict):
                payload = data.get("data", [])
                if isinstance(payload, list):
                    for item in payload:
                        if isinstance(item, dict):
                            model_name = item.get("id") or item.get("model") or item.get("name")
                            if model_name:
                                models.append(str(model_name))

            models = sorted(list(set(models)))
            if not models:
                self.output_queue.put("[WARN] No models returned from API. Keeping existing model list.\n")
                self.after(0, lambda: self.status_var.set("Ready"))
                return

            def apply_models() -> None:
                self.model_choices = models
                self.model_cb.configure(values=self.model_choices)
                if self.llm_model_var.get() not in self.model_choices:
                    self.llm_model_var.set(self.model_choices[0])
                self.status_var.set("Ready")

            self.after(0, apply_models)
            self.output_queue.put(f"[INFO] Loaded {len(models)} models from ZEISS gateway.\n")
        except Exception as exc:
            self.output_queue.put(f"[WARN] Could not fetch models from API: {exc}\n")
            self.after(0, lambda: self.status_var.set("Ready"))

    def _refresh_models(self) -> None:
        api_key = self.llm_api_key_var.get().strip() or os.getenv("ZEISS_SUB_KEY", "")
        base_url = self.llm_base_url_var.get().strip()

        if not api_key:
            self.output_queue.put("[WARN] Subscription key missing. Cannot fetch model list.\n")
            return
        if not base_url:
            self.output_queue.put("[WARN] Base URL missing. Cannot fetch model list.\n")
            return

        self.status_var.set("Loading models...")
        threading.Thread(
            target=self._fetch_models_worker,
            args=(api_key, base_url),
            daemon=True,
        ).start()

    def _browse_prompt_file(self) -> None:
        path = filedialog.askopenfilename(
            title="Select Prompt Template",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
            initialdir=str(self.project_root),
        )
        if path:
            self.prompt_file_var.set(path)

    def _append_log(self, text: str) -> None:
        self.log_text.insert(tk.END, text)
        self.log_text.see(tk.END)

    def _drain_log_queue(self) -> None:
        while True:
            try:
                line = self.output_queue.get_nowait()
            except queue.Empty:
                break

            self._append_log(line)

            match = re.search(r"Helper JavaScript saved:\s*(.+)", line)
            if match:
                helper_path = match.group(1).strip()
                self.last_helper_file = (self.project_root / helper_path).resolve() if not Path(helper_path).is_absolute() else Path(helper_path)
                self.open_helper_btn.configure(state=tk.NORMAL)

        self.after(120, self._drain_log_queue)

    def _validate_inputs(self) -> bool:
        if not self.url_var.get().strip():
            messagebox.showerror("Missing URL", "Please provide a target URL.")
            return False

        if self.workflow_var.get() == "generate-js":
            if not self.llm_model_var.get().strip():
                messagebox.showerror("Missing Model", "Please provide an LLM model name.")
                return False

            try:
                float(self.llm_temperature_var.get().strip())
            except ValueError:
                messagebox.showerror("Invalid Temperature", "Temperature must be a numeric value.")
                return False

            try:
                int(self.llm_max_tokens_var.get().strip())
            except ValueError:
                messagebox.showerror("Invalid Max Tokens", "Max tokens must be an integer.")
                return False

            if not Path(self.prompt_file_var.get().strip()).exists():
                messagebox.showerror("Prompt File Missing", "Prompt template file does not exist.")
                return False

        return True

    def _build_command(self):
        url = self.url_var.get().strip()
        mode = self.mode_var.get().strip()
        workflow = self.workflow_var.get().strip()

        cmd = [
            sys.executable,
            str(self.run_script),
            url,
            mode,
            workflow,
        ]

        cmd.append("--headless" if self.headless_var.get() else "--no-headless")

        if workflow == "generate-js":
            if self.llm_api_key_var.get().strip():
                cmd.append(f"--llm-api-key={self.llm_api_key_var.get().strip()}")
            if self.llm_base_url_var.get().strip():
                cmd.append(f"--llm-base-url={self.llm_base_url_var.get().strip()}")
            cmd.append(f"--llm-model={self.llm_model_var.get().strip()}")
            cmd.append(f"--llm-temperature={self.llm_temperature_var.get().strip()}")
            cmd.append(f"--llm-max-tokens={self.llm_max_tokens_var.get().strip()}")
            cmd.append(f"--prompt-file={self.prompt_file_var.get().strip()}")

        return cmd

    def _start_run(self) -> None:
        if self.process is not None:
            messagebox.showinfo("In Progress", "A workflow is already running.")
            return

        if not self._validate_inputs():
            return

        self.last_helper_file = None
        self.open_helper_btn.configure(state=tk.DISABLED)

        cmd = self._build_command()

        self.log_text.delete("1.0", tk.END)
        self._append_log(f"[COMMAND] {' '.join(cmd)}\n\n")

        self.status_var.set("Running...")
        self.run_btn.configure(state=tk.DISABLED)
        self.stop_btn.configure(state=tk.NORMAL)

        def runner():
            try:
                self.process = subprocess.Popen(
                    cmd,
                    cwd=str(self.project_root),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                )

                assert self.process.stdout is not None
                for line in self.process.stdout:
                    self.output_queue.put(line)

                code = self.process.wait()
                self.output_queue.put(f"\n[EXIT] Process finished with code {code}\n")

            except Exception as exc:
                self.output_queue.put(f"\n[ERROR] Failed to run process: {exc}\n")
            finally:
                self.process = None
                self.after(0, self._mark_completed)

        threading.Thread(target=runner, daemon=True).start()

    def _mark_completed(self) -> None:
        self.run_btn.configure(state=tk.NORMAL)
        self.stop_btn.configure(state=tk.DISABLED)
        self.status_var.set("Ready")

    def _stop_run(self) -> None:
        if self.process is None:
            return

        try:
            self.process.terminate()
            self.output_queue.put("\n[STOP] Termination requested by user.\n")
            self.status_var.set("Stopping...")
        except Exception as exc:
            self.output_queue.put(f"\n[ERROR] Unable to stop process: {exc}\n")

    def _open_helper_file(self) -> None:
        if not self.last_helper_file:
            messagebox.showinfo("No File", "No generated helper file path is available yet.")
            return

        if not self.last_helper_file.exists():
            messagebox.showerror("File Missing", f"File not found:\n{self.last_helper_file}")
            return

        try:
            if sys.platform.startswith("win"):
                os.startfile(str(self.last_helper_file))
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(self.last_helper_file)])
            else:
                subprocess.Popen(["xdg-open", str(self.last_helper_file)])
        except Exception as exc:
            messagebox.showerror("Open Failed", f"Could not open file:\n{exc}")


def main() -> int:
    app = FrameworkUI()
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
