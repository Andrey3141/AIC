import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from typing import Callable
import os
from datetime import datetime


class SettingsDialog:
    """Диалоговое окно настроек формата запроса"""
    
    def __init__(self, parent, current_params: dict, on_save: Callable):
        self.parent = parent
        self.current_params = current_params
        self.on_save = on_save
        self.result = None
        
        self._create_dialog()
    
    def _create_dialog(self):
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Настройка формата запроса")
        self.dialog.geometry("400x350")
        self.dialog.configure(bg="#2d2d3d")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        tk.Label(self.dialog, text="⚙️ НАСТРОЙКА ФОРМАТА ЗАПРОСА", 
                font=("Arial", 12, "bold"), bg="#2d2d3d", fg="#00d4ff").pack(pady=15)
        
        # Язык
        lang_frame = tk.Frame(self.dialog, bg="#2d2d3d")
        lang_frame.pack(fill=tk.X, padx=20, pady=8)
        tk.Label(lang_frame, text="Язык программирования:", font=("Arial", 10),
                bg="#2d2d3d", fg="#ffffff", width=20, anchor="w").pack(side=tk.LEFT)
        
        self.language_var = tk.StringVar(value=self.current_params.get("language", "Python"))
        languages = ["Python", "Java", "JavaScript", "C++", "C#", "Go", "Rust", "TypeScript", "PHP", "Ruby", "Swift", "Kotlin"]
        lang_menu = ttk.Combobox(lang_frame, textvariable=self.language_var, values=languages, state="readonly", width=15)
        lang_menu.pack(side=tk.LEFT, padx=10)
        
        # Платформа
        plat_frame = tk.Frame(self.dialog, bg="#2d2d3d")
        plat_frame.pack(fill=tk.X, padx=20, pady=8)
        tk.Label(plat_frame, text="Платформа:", font=("Arial", 10),
                bg="#2d2d3d", fg="#ffffff", width=20, anchor="w").pack(side=tk.LEFT)
        
        self.platform_var = tk.StringVar(value=self.current_params.get("platform", "Desktop"))
        platforms = ["Desktop", "Web", "Mobile", "Embedded", "Cloud", "CLI"]
        plat_menu = ttk.Combobox(plat_frame, textvariable=self.platform_var, values=platforms, state="readonly", width=15)
        plat_menu.pack(side=tk.LEFT, padx=10)
        
        # IDE
        ide_frame = tk.Frame(self.dialog, bg="#2d2d3d")
        ide_frame.pack(fill=tk.X, padx=20, pady=8)
        tk.Label(ide_frame, text="IDE:", font=("Arial", 10),
                bg="#2d2d3d", fg="#ffffff", width=20, anchor="w").pack(side=tk.LEFT)
        
        self.ide_var = tk.StringVar(value=self.current_params.get("ide", "VS Code"))
        ides = ["VS Code", "PyCharm", "IntelliJ IDEA", "Eclipse", "Android Studio", "Xcode", "NetBeans", "Sublime Text", "Vim", "Emacs"]
        ide_menu = ttk.Combobox(ide_frame, textvariable=self.ide_var, values=ides, state="readonly", width=15)
        ide_menu.pack(side=tk.LEFT, padx=10)
        
        # Кнопки
        btn_frame = tk.Frame(self.dialog, bg="#2d2d3d")
        btn_frame.pack(fill=tk.X, padx=20, pady=20)
        
        tk.Button(btn_frame, text="✅ СОХРАНИТЬ", font=("Arial", 10, "bold"),
                 bg="#00ff9d", fg="#1e1e2e", relief=tk.FLAT, cursor="hand2",
                 command=self._save).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        
        tk.Button(btn_frame, text="❌ ОТМЕНА", font=("Arial", 10, "bold"),
                 bg="#ff4444", fg="#ffffff", relief=tk.FLAT, cursor="hand2",
                 command=self._cancel).pack(side=tk.RIGHT, padx=5, expand=True, fill=tk.X)
        
        self.dialog.protocol("WM_DELETE_WINDOW", self._cancel)
        
        self.dialog.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (self.dialog.winfo_width() // 2)
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
    
    def _save(self):
        self.result = {
            "language": self.language_var.get(),
            "platform": self.platform_var.get(),
            "ide": self.ide_var.get()
        }
        self.on_save(self.result)
        self.dialog.destroy()
    
    def _cancel(self):
        self.dialog.destroy()


class ControlPanel(tk.Frame):
    """Левая панель управления"""
    
    def __init__(self, parent, log_callback: Callable, colors=None, **kwargs):
        super().__init__(parent, bg="#2d2d3d", width=380, **kwargs)
        self.log_callback = log_callback
        self.pack_propagate(False)
        
        self.url_var = tk.StringVar(value="http://localhost:1234/v1/chat/completions")
        self.model_var = tk.StringVar(value="qwen/qwen2.5-coder-14b")
        self.temp_var = tk.StringVar(value="0.1")
        self.max_tokens_var = tk.StringVar(value="4096")
        self.custom_colors = colors or {}
        
        self._create_widgets()
    
    def _create_widgets(self):
        tk.Label(self, text="AIC CONTROL PANEL", font=("Arial", 14, "bold"),
                bg="#2d2d3d", fg="#00d4ff").pack(pady=15)
        
        self._create_status_frame()
        self._create_lm_studio_frame()
        self._create_model_frame()
    
    def _create_status_frame(self):
        status_frame = tk.Frame(self, bg="#3d3d4d", relief=tk.FLAT, bd=2)
        status_frame.pack(fill=tk.X, padx=15, pady=10)
        
        self.status_canvas = tk.Canvas(status_frame, width=12, height=12, bg="#3d3d4d", highlightthickness=0)
        self.status_canvas.pack(side=tk.LEFT, padx=10, pady=10)
        self.status_dot = self.status_canvas.create_oval(2, 2, 10, 10, fill="#ff4444")
        
        self.status_label = tk.Label(status_frame, text="OFFLINE", font=("Arial", 10, "bold"),
                                     bg="#3d3d4d", fg="#ff4444")
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        self.fullscreen_btn = tk.Button(status_frame, text="F11", font=("Arial", 9, "bold"),
                                        bg="#3d3d4d", fg="#00d4ff", relief=tk.FLAT, cursor="hand2", width=3)
        self.fullscreen_btn.pack(side=tk.RIGHT, padx=5)
        
        self.connect_btn = tk.Button(status_frame, text="ПОДКЛЮЧИТЬСЯ", font=("Arial", 11, "bold"),
                                     bg="#00d4ff", fg="#1e1e2e", relief=tk.FLAT, cursor="hand2")
        self.connect_btn.pack(side=tk.RIGHT, padx=5)
    
    def _create_lm_studio_frame(self):
        frame = tk.LabelFrame(self, text="LM STUDIO НАСТРОЙКИ", 
                              font=("Arial", 10, "bold"),
                              bg="#2d2d3d", fg="#00d4ff", relief=tk.GROOVE)
        frame.pack(fill=tk.X, padx=15, pady=10)
        
        tk.Label(frame, text="API URL:", font=("Arial", 9),
                bg="#2d2d3d", fg="#ffffff").pack(anchor=tk.W, padx=10, pady=(5,0))
        tk.Entry(frame, textvariable=self.url_var, bg="#3d3d4d", fg="#ffffff", font=("Arial", 9)).pack(fill=tk.X, padx=10, pady=2)
        
        tk.Label(frame, text="Модель:", font=("Arial", 9),
                bg="#2d2d3d", fg="#ffffff").pack(anchor=tk.W, padx=10, pady=(5,0))
        tk.Entry(frame, textvariable=self.model_var, bg="#3d3d4d", fg="#ffffff", font=("Arial", 9)).pack(fill=tk.X, padx=10, pady=2)
    
    def _create_model_frame(self):
        frame = tk.LabelFrame(self, text="ПАРАМЕТРЫ МОДЕЛИ", 
                              font=("Arial", 10, "bold"),
                              bg="#2d2d3d", fg="#00d4ff", relief=tk.GROOVE)
        frame.pack(fill=tk.X, padx=15, pady=10)
        
        temp_frame = tk.Frame(frame, bg="#2d2d3d")
        temp_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(temp_frame, text="Температура (0-1):", font=("Arial", 9),
                bg="#2d2d3d", fg="#ffffff").pack(side=tk.LEFT)
        tk.Entry(temp_frame, textvariable=self.temp_var, width=10, bg="#3d3d4d", fg="#ffffff").pack(side=tk.RIGHT)
        
        tokens_frame = tk.Frame(frame, bg="#2d2d3d")
        tokens_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(tokens_frame, text="Max tokens:", font=("Arial", 9),
                bg="#2d2d3d", fg="#ffffff").pack(side=tk.LEFT)
        tk.Entry(tokens_frame, textvariable=self.max_tokens_var, width=10, bg="#3d3d4d", fg="#ffffff").pack(side=tk.RIGHT)
        
        self.save_settings_btn = tk.Button(frame, text="СОХРАНИТЬ НАСТРОЙКИ", font=("Arial", 9, "bold"),
                                          bg="#ffaa00", fg="#1e1e2e", relief=tk.FLAT, cursor="hand2")
        self.save_settings_btn.pack(fill=tk.X, padx=10, pady=10)
        
        self.settings_info = tk.Label(frame, text="URL: localhost:1234 | Модель: Qwen2.5-Coder-7B",
                                      font=("Arial", 8), bg="#2d2d3d", fg="#888888")
        self.settings_info.pack(pady=(0, 10))
    
    def update_status(self, is_connected: bool):
        if is_connected:
            self.status_canvas.itemconfig(self.status_dot, fill="#00ff9d")
            self.status_label.config(text="ONLINE", fg="#00ff9d")
            self.connect_btn.config(text="ОТКЛЮЧИТЬСЯ", bg="#ff4444", fg="#ffffff")
        else:
            self.status_canvas.itemconfig(self.status_dot, fill="#ff4444")
            self.status_label.config(text="OFFLINE", fg="#ff4444")
            self.connect_btn.config(text="ПОДКЛЮЧИТЬСЯ", bg="#00d4ff", fg="#1e1e2e")
    
    def update_settings_info(self, url: str, model: str, temp: float, max_tokens: int):
        short_url = url.replace("http://", "").replace("/v1/chat/completions", "")[:30]
        self.settings_info.config(text=f"URL: {short_url} | {model[:15]}")
    
    def update_stage(self, stage: str, color: str = "#ffaa00"):
        if hasattr(self, 'stage_label'):
            self.stage_label.config(text=stage, fg=color)
        else:
            self.stage_label = tk.Label(self, text=stage, font=("Arial", 10, "bold"),
                                        bg="#2d2d3d", fg=color)
            self.stage_label.pack(pady=5)


class ChatMessage(tk.Frame):
    """Виджет сообщения с закруглёнными краями"""
    
    COLORS = {
        "USER": {"bg": "#00aa00", "fg": "#ffffff", "align": "right"},
        "Аналитик": {"bg": "#cc0000", "fg": "#ffffff", "align": "left"},
        "Начальник": {"bg": "#ffaa00", "fg": "#000000", "align": "left"},
        "Главный разработчик": {"bg": "#0066cc", "fg": "#ffffff", "align": "left"},
        "Главный тестировщик": {"bg": "#cc00cc", "fg": "#ffffff", "align": "left"},
        "Рядовой разработчик": {"bg": "#0099cc", "fg": "#ffffff", "align": "left"},
        "Рядовой тестировщик": {"bg": "#00cc99", "fg": "#ffffff", "align": "left"},
    }
    
    def __init__(self, parent, sender: str, message: str, timestamp: str = None, colors=None, **kwargs):
        self.custom_colors = colors or {}
        
        super().__init__(parent, bg="#1e1e2e", **kwargs)
        self.sender = sender
        self.message = message
        self.timestamp = timestamp or datetime.now().strftime("%H:%M")
        
        self._create_widgets()
        self.pack(fill=tk.X, pady=5, padx=10)
    
    def _create_widgets(self):
        colors = self.custom_colors.get(self.sender, {"bg": "#3d3d4d", "fg": "#ffffff", "align": "left"})
        align = colors["align"]
        
        # Контейнер для сообщения
        msg_container = tk.Frame(self, bg="#1e1e2e")
        msg_container.pack(fill=tk.X, anchor="e" if align == "right" else "w")
        
        # Имя отправителя
        name_label = tk.Label(msg_container, text=self.sender, font=("Arial", 8, "bold"),
                              bg="#1e1e2e", fg=colors["bg"])
        name_label.pack(anchor="e" if align == "right" else "w", padx=5)
        
        # Блок сообщения (закруглённый прямоугольник)
        text_frame = tk.Frame(msg_container, bg=colors["bg"], bd=0)
        text_frame.pack(anchor="e" if align == "right" else "w", padx=5)
        
        # Текст сообщения
        message_label = tk.Label(
            text_frame,
            text=self.message,
            font=("Segoe UI Emoji", 10),
            bg=colors["bg"],
            fg=colors["fg"],
            wraplength=400,
            justify=tk.LEFT
        )
        message_label.pack(padx=12, pady=8)
        
        # Кнопка копирования
        copy_btn = tk.Button(
            text_frame,
            text="📋",
            font=("Arial", 8),
            bg=colors["bg"],
            fg=colors["fg"],
            relief=tk.FLAT,
            cursor="hand2",
            command=self._copy_message
        )

        # позиционирование справа снизу
        copy_btn.pack(anchor="e", padx=5, pady=(0, 5))
        
        # Время
        time_label = tk.Label(msg_container, text=self.timestamp, font=("Arial", 7),
                              bg="#1e1e2e", fg="#888888")
        time_label.pack(anchor="e" if align == "right" else "w", padx=8)
        
    def _copy_message(self):
        self.clipboard_clear()
        self.clipboard_append(self.message)
        self.update()  # важно для буфера

class ChatPanel(tk.Frame):
    """Центральная панель чата с мессенджер-стилем"""
    
    def __init__(self, parent, employees, **kwargs):
        super().__init__(parent, bg="#1e1e2e", **kwargs)
        self.employees = employees
        self.format_params = {"language": "Python", "platform": "Desktop", "ide": "VS Code"}
        self.is_format_set = False
        self.role_colors = {
            "Пользователь": {"bg": "#00aa00", "fg": "#ffffff", "align": "right"},
            "Аналитик": {"bg": "#cc0000", "fg": "#ffffff", "align": "left"},
            "Начальник": {"bg": "#ffaa00", "fg": "#000000", "align": "left"},
            "Главный разработчик": {"bg": "#0066cc", "fg": "#ffffff", "align": "left"},
            "Главный тестировщик": {"bg": "#cc00cc", "fg": "#ffffff", "align": "left"},
            "Рядовой разработчик": {"bg": "#0099cc", "fg": "#ffffff", "align": "left"},
            "Рядовой тестировщик": {"bg": "#00cc99", "fg": "#ffffff", "align": "left"},
        }
        self._create_widgets()
    
    def _create_widgets(self):
        # Основной контейнер
        main_container = tk.Frame(self, bg="#1e1e2e")
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Верхняя панель: заголовок
        header_frame = tk.Frame(main_container, bg="#2d2d3d", height=50)
        header_frame.pack(fill=tk.X, side=tk.TOP)
        header_frame.pack_propagate(False)
        tk.Label(header_frame, text="ОБЩИЙ ЧАТ", font=("Arial", 12, "bold"),
                bg="#2d2d3d", fg="#00d4ff").pack(pady=12)
        
        # Средняя часть: область сообщений (слева) + список сотрудников (справа)
        middle_frame = tk.Frame(main_container, bg="#1e1e2e")
        middle_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Область сообщений (слева)
        chat_frame = tk.Frame(middle_frame, bg="#1e1e2e")
        chat_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Канвас с прокруткой для сообщений
        self.messages_container = tk.Frame(chat_frame, bg="#1e1e2e")
        self.messages_container.pack(fill=tk.BOTH, expand=True)
        
        self.messages_canvas = tk.Canvas(self.messages_container, bg="#1e1e2e", highlightthickness=0)
        self.messages_scrollbar = tk.Scrollbar(self.messages_container, orient=tk.VERTICAL, command=self.messages_canvas.yview)
        self.messages_scrollable = tk.Frame(self.messages_canvas, bg="#1e1e2e")
        
        self.messages_scrollable.bind("<Configure>", lambda e: self.messages_canvas.configure(scrollregion=self.messages_canvas.bbox("all")))
        self.messages_canvas.create_window((0, 0), window=self.messages_scrollable, anchor="nw")
        self.messages_canvas.configure(yscrollcommand=self.messages_scrollbar.set)
        
        self.messages_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.messages_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Список сотрудников (справа)
        employees_frame = tk.LabelFrame(middle_frame, text="КОМАНДА", font=("Arial", 10, "bold"),
                                        bg="#1e1e2e", fg="#00d4ff", relief=tk.GROOVE)
        employees_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        
        # Сотрудники
        for emp in self.employees:
            emp_frame = tk.Frame(employees_frame, bg="#2d2d3d", relief=tk.FLAT, bd=1)
            emp_frame.pack(fill=tk.X, padx=10, pady=5)

            tk.Label(
                emp_frame,
                text=f"{emp['icon']} {emp['name']}",
                font=("Arial", 10),
                bg="#2d2d3d",
                fg="#ffffff",
                padx=10,
                pady=8
            ).pack()
        
        # Область ввода (увеличена по вертикали)
        input_frame = tk.Frame(main_container, bg="#2d2d3d")
        input_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=5)
        
        # Кнопки
        button_frame = tk.Frame(input_frame, bg="#2d2d3d")
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.format_btn = tk.Button(button_frame, text="⚙️ ФОРМАТ ЗАПРОСА", font=("Arial", 9, "bold"),
                                    bg="#ffaa00", fg="#1e1e2e", relief=tk.FLAT, cursor="hand2")
        self.format_btn.pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)
        
        self.attach_btn = tk.Button(button_frame, text="📎 ПРИКРЕПИТЬ", font=("Arial", 9, "bold"),
                                    bg="#3d3d4d", fg="#ffffff", relief=tk.FLAT, cursor="hand2")
        self.attach_btn.pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)
        
        self.clear_btn = tk.Button(button_frame, text="🗑️ ОЧИСТИТЬ", font=("Arial", 9, "bold"),
                                   bg="#ff4444", fg="#ffffff", relief=tk.FLAT, cursor="hand2")
        self.clear_btn.pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)
        
        self.send_btn = tk.Button(button_frame, text="📤 ОТПРАВИТЬ", font=("Arial", 9, "bold"),
                                  bg="#00d4ff", fg="#1e1e2e", relief=tk.FLAT, cursor="hand2")
        self.send_btn.pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)
        
        # Поле ввода - увеличено (height=8 вместо 4)
        self.message_input = tk.Text(input_frame, height=8, bg="#3d3d4d", fg="#ffffff",
                                     font=("Arial", 10), wrap=tk.WORD, relief=tk.FLAT)
        self.message_input.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        self._create_files_frame(input_frame)
        
        self.message_input.config(state=tk.DISABLED)
        self.send_btn.config(state=tk.DISABLED)
        self.attach_btn.config(state=tk.DISABLED)
        
        def _on_mousewheel(event):
            self.messages_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        self.messages_canvas.bind("<MouseWheel>", _on_mousewheel)
        
        self.messages_canvas.bind("<Button-4>", lambda e: self.messages_canvas.yview_scroll(-1, "units"))
        self.messages_canvas.bind("<Button-5>", lambda e: self.messages_canvas.yview_scroll(1, "units"))
    
    def _create_files_frame(self, parent):
        self.files_frame = tk.LabelFrame(parent, text="ПРИКРЕПЛЁННЫЕ ФАЙЛЫ", 
                                         font=("Arial", 8, "bold"),
                                         bg="#2d2d3d", fg="#00ff9d", relief=tk.GROOVE)
        self.files_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.files_listbox = tk.Listbox(self.files_frame, bg="#3d3d4d", fg="#00ff9d",
                                        font=("Arial", 8), height=3, relief=tk.FLAT)
        self.files_listbox.pack(fill=tk.X, padx=5, pady=5)
        
        btn_frame = tk.Frame(self.files_frame, bg="#2d2d3d")
        btn_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        self.remove_file_btn = tk.Button(btn_frame, text="Удалить", font=("Arial", 7),
                                         bg="#ff4444", fg="#ffffff", relief=tk.FLAT, cursor="hand2")
        self.remove_file_btn.pack(side=tk.LEFT, padx=2)
        
        self.clear_files_btn = tk.Button(btn_frame, text="Очистить всё", font=("Arial", 7),
                                         bg="#ffaa00", fg="#1e1e2e", relief=tk.FLAT, cursor="hand2")
        self.clear_files_btn.pack(side=tk.RIGHT, padx=2)
        
        self.files_frame.pack_forget()
    
    def set_format_params(self, params: dict):
        self.format_params = params
        self.is_format_set = True
        
        template = f"""Язык: {params['language']}
Платформа: {params['platform']}
IDE: {params['ide']}
Задача: """
        
        self.message_input.config(state=tk.NORMAL)
        self.message_input.delete("1.0", tk.END)
        self.message_input.insert("1.0", template)
        self.send_btn.config(state=tk.NORMAL)
        self.attach_btn.config(state=tk.NORMAL)
        
        self.message_input.mark_set("insert", "end-1c")
        self.message_input.focus()
    
    def add_message(self, sender: str, message: str, distribution=None):
        """Добавляет сообщение в чат"""

        # общий контейнер сообщения
        message_frame = tk.Frame(self.messages_scrollable, bg="#1e1e2e")
        message_frame.pack(fill=tk.X, pady=5, padx=10)

        # === ИКОНКИ РАСПРЕДЕЛЕНИЯ ===
        if distribution:
            icons_frame = tk.Frame(message_frame, bg="#1e1e2e")
            icons_frame.pack(anchor="w", pady=(0, 3))
            
            ROLE_ICONS = {e["token"]: e["icon"] for e in self.employees}

            for role, action in distribution.items():
                if action == "ignore":
                    continue

                icon = ROLE_ICONS.get(role, "❓")

                color = "#888888"  # save
                if action == "send":
                    color = "#00ff88"

                tk.Label(
                    icons_frame,
                    text=icon,
                    fg=color,
                    bg="#1e1e2e",
                    font=("Arial", 12)
                ).pack(side=tk.LEFT, padx=2)

        # === САМО СООБЩЕНИЕ ===
        ChatMessage(message_frame, sender, message, colors=self.role_colors)

        # скролл вниз
        self.messages_scrollable.update_idletasks()
        self.messages_canvas.yview_moveto(1.0)
    
    def get_user_message(self) -> str:
        return self.message_input.get("1.0", tk.END).strip()
    
    def clear_input(self):
        if self.is_format_set:
            template = f"""Язык: {self.format_params['language']}
Платформа: {self.format_params['platform']}
IDE: {self.format_params['ide']}
Задача: """
            self.message_input.delete("1.0", tk.END)
            self.message_input.insert("1.0", template)
            self.message_input.mark_set("insert", "end-1c")
        else:
            self.message_input.delete("1.0", tk.END)
    
    def clear_chat(self):
        for widget in self.messages_scrollable.winfo_children():
            widget.destroy()
        self.add_message("Система", "Чат очищен")
    
    def update_files_list(self, files: list):
        if files:
            self.files_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
            self.files_listbox.delete(0, tk.END)
            for file_path in files:
                file_name = os.path.basename(file_path)
                file_size = os.path.getsize(file_path)
                size_str = f"{file_size / 1024:.1f} KB" if file_size < 1024*1024 else f"{file_size / (1024*1024):.1f} MB"
                self.files_listbox.insert(tk.END, f"📄 {file_name} ({size_str})")
        else:
            self.files_frame.pack_forget()
    
    def get_selected_file_index(self) -> int:
        selection = self.files_listbox.curselection()
        return selection[0] if selection else -1
    
    def enable_send_button(self, enabled: bool):
        if enabled:
            self.send_btn.config(state=tk.NORMAL, text="📤 ОТПРАВИТЬ")
        else:
            self.send_btn.config(state=tk.DISABLED, text="⏳ ОТПРАВКА...")


class LogPanel(tk.Frame):
    """Правая панель логов"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg="#1e1e2e", width=150, **kwargs)
        self.pack_propagate(False)
        self._create_widgets()
    
    def _create_widgets(self):
        log_frame = tk.LabelFrame(self, text="СИСТЕМНЫЙ ЛОГ", font=("Arial", 11, "bold"),
                                  bg="#1e1e2e", fg="#00d4ff", relief=tk.GROOVE)
        log_frame.pack(fill=tk.BOTH, expand=True, ipadx=5, ipady=5)
        
        self.log_text = tk.Text(log_frame, bg="#2d2d3d", fg="#00ff9d", font=("Consolas", 8),
                                wrap=tk.WORD, relief=tk.FLAT)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        scrollbar = tk.Scrollbar(self.log_text, command=self.log_text.yview)
        self.log_text.config(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def add_log(self, message: str, msg_type: str = "info"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        colors = {"info": "#00d4ff", "error": "#ff4444", "success": "#00ff9d", "warning": "#ffaa00"}
        
        self.log_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
        self.log_text.insert(tk.END, f"{message}\n", msg_type)
        self.log_text.tag_config("timestamp", foreground="#888888")
        self.log_text.tag_config("info", foreground="#00d4ff")
        self.log_text.tag_config("error", foreground="#ff4444")
        self.log_text.tag_config("success", foreground="#00ff9d")
        self.log_text.tag_config("warning", foreground="#ffaa00")
        self.log_text.see(tk.END)
    
    def clear(self):
        self.log_text.delete("1.0", tk.END)
        super().__init__(parent, bg="#1e1e2e", **kwargs)
        self.format_params = {"language": "Python", "platform": "Desktop", "ide": "VS Code"}
        self.is_format_set = False
        self._create_widgets()

