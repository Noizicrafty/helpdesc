from __future__ import annotations

import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, ttk
from typing import Dict, List

from .app_service import MailProcessingService
from .models import AppSettings, CategoryConfig, ProcessedEmail
from .utils import format_datetime, parse_date_input


LIGHT_THEME = {
    "bg": "#f5f5f5",
    "fg": "#1f1f1f",
    "panel": "#ffffff",
}

DARK_THEME = {
    "bg": "#1e1e1e",
    "fg": "#f2f2f2",
    "panel": "#2a2a2a",
}


class SettingsWindow(tk.Toplevel):
    def __init__(self, parent: tk.Tk, service: MailProcessingService, on_saved) -> None:
        super().__init__(parent)
        self.service = service
        self.on_saved = on_saved
        self.title("Настройки")
        self.geometry("720x560")
        self.resizable(True, True)

        self.email_var = tk.StringVar(value=str(service.auth.get("email", "")))
        self.password_var = tk.StringVar(value=str(service.auth.get("password", "")))
        self.host_var = tk.StringVar(value=str(service.auth.get("imap_host", service.settings.imap_host)))
        self.port_var = tk.StringVar(value=str(service.auth.get("imap_port", service.settings.imap_port)))
        self.ssl_var = tk.BooleanVar(value=bool(service.auth.get("use_ssl", service.settings.use_ssl)))

        self.reply_var = tk.BooleanVar(value=service.settings.enable_reply_module)
        self.heatmap_var = tk.BooleanVar(value=service.settings.enable_heatmap_module)
        self.theme_var = tk.StringVar(value=service.settings.theme)
        self.font_var = tk.IntVar(value=service.settings.font_scale)

        self._build()

    def _build(self) -> None:
        container = ttk.Frame(self, padding=16)
        container.pack(fill="both", expand=True)

        auth_frame = ttk.LabelFrame(container, text="Авторизация")
        auth_frame.pack(fill="x", pady=6)
        for row, (label, variable) in enumerate([
            ("Email", self.email_var),
            ("Пароль / app-password", self.password_var),
            ("IMAP host", self.host_var),
            ("IMAP port", self.port_var),
        ]):
            ttk.Label(auth_frame, text=label).grid(row=row, column=0, sticky="w", padx=6, pady=6)
            show = "*" if "Пароль" in label else ""
            ttk.Entry(auth_frame, textvariable=variable, width=48, show=show).grid(row=row, column=1, sticky="ew", padx=6, pady=6)
        ttk.Checkbutton(auth_frame, text="Использовать SSL", variable=self.ssl_var).grid(row=4, column=1, sticky="w", padx=6, pady=6)
        auth_frame.columnconfigure(1, weight=1)

        module_frame = ttk.LabelFrame(container, text="Модули")
        module_frame.pack(fill="x", pady=6)
        ttk.Checkbutton(module_frame, text="Генерировать предлагаемые ответы", variable=self.reply_var).pack(anchor="w", padx=8, pady=6)
        ttk.Checkbutton(module_frame, text="Использовать тепловые карты и семантическую категоризацию", variable=self.heatmap_var).pack(anchor="w", padx=8, pady=6)

        display_frame = ttk.LabelFrame(container, text="Отображение")
        display_frame.pack(fill="x", pady=6)
        ttk.Label(display_frame, text="Тема интерфейса").grid(row=0, column=0, sticky="w", padx=6, pady=6)
        ttk.Combobox(display_frame, textvariable=self.theme_var, values=["light", "dark"], state="readonly", width=16).grid(row=0, column=1, sticky="w", padx=6, pady=6)
        ttk.Label(display_frame, text="Размер шрифта").grid(row=1, column=0, sticky="w", padx=6, pady=6)
        ttk.Spinbox(display_frame, from_=11, to=24, textvariable=self.font_var, width=8).grid(row=1, column=1, sticky="w", padx=6, pady=6)

        categories_frame = ttk.LabelFrame(container, text="Категории")
        categories_frame.pack(fill="both", expand=True, pady=6)
        self.category_list = tk.Listbox(categories_frame, height=10)
        self.category_list.pack(side="left", fill="both", expand=True, padx=(8, 4), pady=8)
        button_column = ttk.Frame(categories_frame)
        button_column.pack(side="right", fill="y", padx=(4, 8), pady=8)
        ttk.Button(button_column, text="Добавить", command=self._add_category).pack(fill="x", pady=4)
        ttk.Button(button_column, text="Удалить", command=self._remove_category).pack(fill="x", pady=4)
        self._refresh_categories()

        action_frame = ttk.Frame(container)
        action_frame.pack(fill="x", pady=10)
        ttk.Button(action_frame, text="Сохранить", command=self._save).pack(side="right", padx=4)
        ttk.Button(action_frame, text="Закрыть", command=self.destroy).pack(side="right", padx=4)

    def _refresh_categories(self) -> None:
        self.category_list.delete(0, tk.END)
        for category in self.service.settings.categories:
            self.category_list.insert(tk.END, f"{category.name} | {', '.join(category.keywords)}")

    def _add_category(self) -> None:
        dialog = tk.Toplevel(self)
        dialog.title("Новая категория")
        dialog.geometry("420x220")
        name_var = tk.StringVar()
        keywords_var = tk.StringVar()
        description_var = tk.StringVar()

        ttk.Label(dialog, text="Название").pack(anchor="w", padx=12, pady=(12, 4))
        ttk.Entry(dialog, textvariable=name_var).pack(fill="x", padx=12)
        ttk.Label(dialog, text="Ключевые слова через запятую").pack(anchor="w", padx=12, pady=(12, 4))
        ttk.Entry(dialog, textvariable=keywords_var).pack(fill="x", padx=12)
        ttk.Label(dialog, text="Описание").pack(anchor="w", padx=12, pady=(12, 4))
        ttk.Entry(dialog, textvariable=description_var).pack(fill="x", padx=12)

        def save_category() -> None:
            name = name_var.get().strip()
            if not name:
                messagebox.showwarning("Категория", "Укажите название категории.")
                return
            keywords = [item.strip() for item in keywords_var.get().split(",") if item.strip()]
            self.service.settings.categories.append(CategoryConfig(name=name, keywords=keywords, description=description_var.get().strip()))
            self._refresh_categories()
            dialog.destroy()

        ttk.Button(dialog, text="Сохранить", command=save_category).pack(pady=12)

    def _remove_category(self) -> None:
        selected = self.category_list.curselection()
        if not selected:
            return
        index = selected[0]
        del self.service.settings.categories[index]
        self._refresh_categories()

    def _save(self) -> None:
        self.service.save_auth_data(
            self.email_var.get().strip(),
            self.password_var.get().strip(),
            self.host_var.get().strip(),
            int(self.port_var.get().strip() or "993"),
            self.ssl_var.get(),
        )
        settings = self.service.settings
        settings.enable_reply_module = self.reply_var.get()
        settings.enable_heatmap_module = self.heatmap_var.get()
        settings.theme = self.theme_var.get()
        settings.font_scale = int(self.font_var.get())
        self.service.save_settings_data(settings)
        self.on_saved()
        messagebox.showinfo("Настройки", "Настройки сохранены.")
        self.destroy()


class MailAppUI(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.service = MailProcessingService()
        self.title("Почтовый помощник")
        self.geometry("1350x820")
        self.minsize(1100, 700)

        self.start_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-01"))
        self.end_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.status_var = tk.StringVar(value="Готово к работе")
        self.current_items: list[ProcessedEmail] = []
        self.current_grouped: Dict[str, List[ProcessedEmail]] = {}

        self._configure_styles()
        self._build_layout()
        self.apply_theme()

    def _configure_styles(self) -> None:
        self.style = ttk.Style(self)
        if "clam" in self.style.theme_names():
            self.style.theme_use("clam")

    def apply_theme(self) -> None:
        theme = DARK_THEME if self.service.settings.theme == "dark" else LIGHT_THEME
        self.configure(bg=theme["bg"])
        self.style.configure("TFrame", background=theme["bg"])
        self.style.configure("TLabel", background=theme["bg"], foreground=theme["fg"], font=("Segoe UI", self.service.settings.font_scale))
        self.style.configure("TButton", font=("Segoe UI", self.service.settings.font_scale))
        self.style.configure("Treeview", rowheight=max(28, self.service.settings.font_scale + 16), font=("Segoe UI", self.service.settings.font_scale))
        self.style.configure("Treeview.Heading", font=("Segoe UI", self.service.settings.font_scale, "bold"))
        self.style.configure("TLabelframe", background=theme["bg"], foreground=theme["fg"])
        self.style.configure("TLabelframe.Label", background=theme["bg"], foreground=theme["fg"], font=("Segoe UI", self.service.settings.font_scale, "bold"))
        self.style.configure("TNotebook", background=theme["bg"])
        self.style.configure("TNotebook.Tab", font=("Segoe UI", self.service.settings.font_scale))
        self.text_bg = theme["panel"]
        self.text_fg = theme["fg"]
        if hasattr(self, "body_text"):
            for widget in [self.body_text, self.reply_text, self.info_text]:
                widget.configure(bg=self.text_bg, fg=self.text_fg, insertbackground=self.text_fg, font=("Segoe UI", self.service.settings.font_scale))

    def _build_layout(self) -> None:
        container = ttk.Frame(self, padding=12)
        container.pack(fill="both", expand=True)

        top = ttk.LabelFrame(container, text="Параметры обработки")
        top.pack(fill="x", pady=(0, 8))

        ttk.Label(top, text="Дата начала (YYYY-MM-DD)").grid(row=0, column=0, sticky="w", padx=8, pady=8)
        ttk.Entry(top, textvariable=self.start_var, width=18).grid(row=0, column=1, sticky="w", padx=8, pady=8)
        ttk.Label(top, text="Дата конца (YYYY-MM-DD)").grid(row=0, column=2, sticky="w", padx=8, pady=8)
        ttk.Entry(top, textvariable=self.end_var, width=18).grid(row=0, column=3, sticky="w", padx=8, pady=8)
        ttk.Button(top, text="Обработать письма", command=self.process_emails).grid(row=0, column=4, padx=8, pady=8)
        ttk.Button(top, text="Настройки", command=self.open_settings).grid(row=0, column=5, padx=8, pady=8)
        ttk.Button(top, text="Экспорт", command=self.export_results).grid(row=0, column=6, padx=8, pady=8)
        ttk.Label(top, textvariable=self.status_var).grid(row=1, column=0, columnspan=7, sticky="w", padx=8, pady=(0, 8))

        center = ttk.Frame(container)
        center.pack(fill="both", expand=True)
        center.columnconfigure(0, weight=1)
        center.columnconfigure(1, weight=2)
        center.rowconfigure(0, weight=1)

        left = ttk.LabelFrame(center, text="Письма по категориям")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        left.rowconfigure(0, weight=1)
        left.columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(left, columns=("from", "date"), show="tree headings")
        self.tree.heading("#0", text="Категория / Тема")
        self.tree.heading("from", text="Отправитель")
        self.tree.heading("date", text="Дата")
        self.tree.column("#0", width=250)
        self.tree.column("from", width=180)
        self.tree.column("date", width=150)
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        scrollbar = ttk.Scrollbar(left, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

        right = ttk.Notebook(center)
        right.grid(row=0, column=1, sticky="nsew")

        info_frame = ttk.Frame(right)
        body_frame = ttk.Frame(right)
        reply_frame = ttk.Frame(right)
        right.add(info_frame, text="Сводка")
        right.add(body_frame, text="Письмо")
        right.add(reply_frame, text="Ответ")

        self.info_text = tk.Text(info_frame, wrap="word", height=14)
        self.info_text.pack(fill="both", expand=True)
        self.body_text = tk.Text(body_frame, wrap="word")
        self.body_text.pack(fill="both", expand=True)
        self.reply_text = tk.Text(reply_frame, wrap="word")
        self.reply_text.pack(fill="both", expand=True)

    def open_settings(self) -> None:
        SettingsWindow(self, self.service, self._settings_saved)

    def _settings_saved(self) -> None:
        self.service.refresh_config()
        self.apply_theme()

    def process_emails(self) -> None:
        try:
            start_date = parse_date_input(self.start_var.get().strip())
            end_date = parse_date_input(self.end_var.get().strip())
            self.status_var.set("Идёт чтение и обработка писем...")
            self.update_idletasks()
            results = self.service.fetch_and_process(start_date, end_date)
            self.current_items = results
            self.current_grouped = self.service.grouped_results()
            self._fill_tree()
            self.status_var.set(f"Готово. Обработано писем: {len(results)}")
        except Exception as exc:
            messagebox.showerror("Ошибка", str(exc))
            self.status_var.set("Ошибка обработки")

    def _fill_tree(self) -> None:
        self.tree.delete(*self.tree.get_children())
        for category, items in self.current_grouped.items():
            parent = self.tree.insert("", "end", text=f"{category} ({len(items)})", values=("", ""), open=True)
            for item in items:
                self.tree.insert(
                    parent,
                    "end",
                    text=item.email.subject or "(без темы)",
                    values=(item.email.sender_name, format_datetime(item.email.received_at)),
                    tags=(item.email.message_id,),
                )
        self.info_text.delete("1.0", tk.END)
        self.info_text.insert(
            tk.END,
            "Письма распределены по категориям.\n\n"
            "Если модуль тепловых карт включён, он используется только во время анализа и не экспортируется отдельными файлами.\n"
            "Если модуль ответов включён, справа доступен предлагаемый ответ.\n"
        )

    def on_tree_select(self, _event=None) -> None:
        selected = self.tree.selection()
        if not selected:
            return
        item_id = selected[0]
        parent = self.tree.parent(item_id)
        if not parent:
            return
        subject = self.tree.item(item_id, "text")
        sender = self.tree.item(item_id, "values")[0]
        processed = next(
            (
                entry
                for entry in self.current_items
                if entry.email.subject == subject and entry.email.sender_name == sender
            ),
            None,
        )
        if processed is None:
            return

        self.body_text.delete("1.0", tk.END)
        self.reply_text.delete("1.0", tk.END)
        self.info_text.delete("1.0", tk.END)

        self.body_text.insert(tk.END, processed.email.normalized_body or processed.email.body)
        if self.service.settings.enable_reply_module and processed.suggested_reply:
            self.reply_text.insert(tk.END, processed.suggested_reply)
        else:
            self.reply_text.insert(tk.END, "Модуль ответов отключён.")

        terms = ", ".join(
            f"{term}:{value}" for term, value in zip(processed.assignment.heatmap_terms, processed.assignment.heatmap_values)
        )
        self.info_text.insert(
            tk.END,
            f"Категория: {processed.assignment.category}\n"
            f"Уверенность: {processed.assignment.confidence}\n"
            f"Причина: {processed.assignment.category_reason}\n"
            f"Отправитель: {processed.email.sender_name} <{processed.email.sender_email}>\n"
            f"Дата: {format_datetime(processed.email.received_at)}\n"
            f"Похоже на спам/рекламу: {'Да' if processed.email.is_spam_like else 'Нет'}\n"
            f"Тепловая карта (ключевые термы): {terms if terms else 'Недостаточно данных'}\n"
        )

    def export_results(self) -> None:
        try:
            directory = filedialog.askdirectory(title="Выберите папку для экспорта")
            if not directory:
                return
            self.service.settings.export_directory = directory
            self.service.save_settings_data(self.service.settings)
            export_path = self.service.export_results()
            messagebox.showinfo("Экспорт", f"CSV экспортирован в файл:\n{export_path}")
        except Exception as exc:
            messagebox.showerror("Ошибка экспорта", str(exc))


def run_ui() -> None:
    app = MailAppUI()
    app.mainloop()
