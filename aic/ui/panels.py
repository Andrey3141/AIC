# файл: aic/ui/panels.py
import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable
import os

class ControlPanel(tk.Frame):
    """Левая панель управления"""
    
    def __init__(self, parent, log_callback: Callable, **kwargs):
        super().__init__(parent, bg="#2d2d3d", width=380, **kwargs)
        self.log_callback = log_callback
        self.pack_propagate(False)
        self._create_widgets()
    
    def _create_widgets(self):
        tk.Label(self, text="AIC CONTROL PANEL", font=("Arial", 14, "bold"),
                bg="#2d2d3d", fg="#00d4ff").pack(pady=15)
        
        # Статус
        self._create_status_frame()
        
        # Проект
        self._create_project_frame()
        
        # Настройки времени
        self._create_settings_frame()
        
        # Управление окнами
        self._create_windows_frame()
    
    def _create_status_frame(self):
        status_frame = tk.Frame(self, bg="#3d3d4d", relief=tk.FLAT, bd=2)
        status_frame.pack(fill=tk.X, padx=15, pady=10)
        
        self.status_canvas = tk.Canvas(status_frame, width=12, height=12, bg="#3d3d4d", highlightthickness=0)
        self.status_canvas.pack(side=tk.LEFT, padx=10, pady=10)
        self.status_dot = self.status_canvas.create_oval(2, 2, 10, 10, fill="#ff4444")
        
        self.status_label = tk.Label(status_frame, text="OFFLINE", font=("Arial", 10, "bold"),
                                     bg="#3d3d4d", fg="#ff4444")
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        # Кнопка F11 для полноэкранного режима
        self.fullscreen_btn = tk.Button(status_frame, text="F11", font=("Arial", 9, "bold"),
                                        bg="#3d3d4d", fg="#00d4ff", relief=tk.FLAT, cursor="hand2",
                                        width=3)
        self.fullscreen_btn.pack(side=tk.RIGHT, padx=5)
        
        self.connect_btn = tk.Button(status_frame, text="ПОДКЛЮЧИТЬСЯ", font=("Arial", 11, "bold"),
                                     bg="#00d4ff", fg="#1e1e2e", relief=tk.FLAT, cursor="hand2")
        self.connect_btn.pack(side=tk.RIGHT, padx=5)
    
    def _create_project_frame(self):
        project_frame = tk.LabelFrame(self, text="НАСТРОЙКИ ПРОЕКТА", 
                                      font=("Arial", 10, "bold"),
                                      bg="#2d2d3d", fg="#00d4ff", relief=tk.GROOVE)
        project_frame.pack(fill=tk.X, padx=15, pady=10)
        
        project_path_frame = tk.Frame(project_frame, bg="#2d2d3d")
        project_path_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(project_path_frame, text="Папка проекта:", font=("Arial", 9),
                bg="#2d2d3d", fg="#ffffff").pack(anchor=tk.W)
        
        self.project_path_var = tk.StringVar()
        self.project_path_entry = tk.Entry(project_path_frame, textvariable=self.project_path_var,
                                           bg="#3d3d4d", fg="#ffffff", font=("Arial", 9))
        self.project_path_entry.pack(fill=tk.X, pady=5)
        
        btn_frame = tk.Frame(project_path_frame, bg="#2d2d3d")
        btn_frame.pack(fill=tk.X, pady=5)
        
        self.select_btn = tk.Button(btn_frame, text="ВЫБРАТЬ ПАПКУ", font=("Arial", 9, "bold"),
                                    bg="#3d3d4d", fg="#ffffff", relief=tk.FLAT, cursor="hand2")
        self.select_btn.pack(side=tk.LEFT, padx=(0,5))
        
        self.save_btn = tk.Button(btn_frame, text="СОХРАНИТЬ ПУТЬ", font=("Arial", 9, "bold"),
                                  bg="#ffaa00", fg="#1e1e2e", relief=tk.FLAT, cursor="hand2")
        self.save_btn.pack(side=tk.LEFT)
        
        self.project_files_info = tk.Label(project_frame, text="Файлы проекта: не выбрано",
                                           font=("Arial", 8), bg="#2d2d3d", fg="#888888")
        self.project_files_info.pack(fill=tk.X, padx=10, pady=5)
    
    def _create_settings_frame(self):
        settings_frame = tk.LabelFrame(self, text="НАСТРОЙКИ ОЖИДАНИЯ", 
                                       font=("Arial", 10, "bold"),
                                       bg="#2d2d3d", fg="#00d4ff", relief=tk.GROOVE)
        settings_frame.pack(fill=tk.X, padx=15, pady=10)
        
        min_frame = tk.Frame(settings_frame, bg="#2d2d3d")
        min_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(min_frame, text="Мин. время (сек):", font=("Arial", 9),
                bg="#2d2d3d", fg="#ffffff").pack(side=tk.LEFT)
        self.min_time_var = tk.StringVar(value="60")
        self.min_spinbox = tk.Spinbox(min_frame, from_=60, to=600, textvariable=self.min_time_var,
                                      width=10, bg="#3d3d4d", fg="#ffffff", font=("Arial", 9))
        self.min_spinbox.pack(side=tk.RIGHT)
        
        max_frame = tk.Frame(settings_frame, bg="#2d2d3d")
        max_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(max_frame, text="Макс. время (сек):", font=("Arial", 9),
                bg="#2d2d3d", fg="#ffffff").pack(side=tk.LEFT)
        self.max_time_var = tk.StringVar(value="600")
        self.max_spinbox = tk.Spinbox(max_frame, from_=60, to=600, textvariable=self.max_time_var,
                                      width=10, bg="#3d3d4d", fg="#ffffff", font=("Arial", 9))
        self.max_spinbox.pack(side=tk.RIGHT)
        
        self.save_settings_btn = tk.Button(settings_frame, text="СОХРАНИТЬ НАСТРОЙКИ", font=("Arial", 9, "bold"),
                                          bg="#ffaa00", fg="#1e1e2e", relief=tk.FLAT, cursor="hand2")
        self.save_settings_btn.pack(fill=tk.X, padx=10, pady=10)
        
        self.settings_info = tk.Label(settings_frame, text="Текущий диапазон: 1мин00с - 10мин00с",
                                      font=("Arial", 8), bg="#2d2d3d", fg="#888888")
        self.settings_info.pack(pady=(0, 10))
    
    def _create_windows_frame(self):
        tk.Label(self, text="УПРАВЛЕНИЕ ОКНАМИ", font=("Arial", 11, "bold"),
                bg="#2d2d3d", fg="#00d4ff").pack(pady=(10,5))
        
        self.windows_listbox = tk.Listbox(self, bg="#3d3d4d", fg="#ffffff",
                                          selectbackground="#00d4ff", selectforeground="#1e1e2e",
                                          font=("Arial", 9), height=5, relief=tk.FLAT)
        self.windows_listbox.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
        
        btn_frame = tk.Frame(self, bg="#2d2d3d")
        btn_frame.pack(fill=tk.X, padx=15, pady=5)
        
        self.refresh_btn = tk.Button(btn_frame, text="REFRESH", font=("Arial", 9), 
                                     bg="#3d3d4d", fg="#ffffff", relief=tk.FLAT, cursor="hand2")
        self.refresh_btn.pack(side=tk.LEFT, padx=2)
        
        self.switch_btn = tk.Button(btn_frame, text="ПЕРЕКЛЮЧИТЬ", font=("Arial", 9), 
                                    bg="#00d4ff", fg="#1e1e2e", relief=tk.FLAT, cursor="hand2")
        self.switch_btn.pack(side=tk.RIGHT, padx=2)
        
        self.current_label = tk.Label(self, text="Активное окно: ---", font=("Arial", 9),
                                      bg="#2d2d3d", fg="#888888", wraplength=350)
        self.current_label.pack(pady=10)
        
        self.stage_label = tk.Label(self, text="Этап: ожидание", font=("Arial", 10, "bold"),
                                    bg="#2d2d3d", fg="#ffaa00")
        self.stage_label.pack(pady=5)
        
        self.load_history_btn = tk.Button(self, text="ЗАГРУЗИТЬ ИСТОРИЮ", font=("Arial", 9, "bold"),
                                          bg="#ffaa00", fg="#1e1e2e", relief=tk.FLAT, cursor="hand2")
        self.load_history_btn.pack(fill=tk.X, padx=15, pady=5)
    
    def update_status(self, is_connected: bool):
        """Обновление статуса подключения"""
        if is_connected:
            self.status_canvas.itemconfig(self.status_dot, fill="#00ff9d")
            self.status_label.config(text="ONLINE", fg="#00ff9d")
            self.connect_btn.config(text="ОТКЛЮЧИТЬСЯ", bg="#ff4444", fg="#ffffff")
        else:
            self.status_canvas.itemconfig(self.status_dot, fill="#ff4444")
            self.status_label.config(text="OFFLINE", fg="#ff4444")
            self.connect_btn.config(text="ПОДКЛЮЧИТЬСЯ", bg="#00d4ff", fg="#1e1e2e")
    
    def update_project_info(self, folder: str, files: list):
        """Обновление информации о проекте"""
        self.project_path_var.set(folder)
        if files:
            self.project_files_info.config(text=f"Найдено: {', '.join(files)}", fg="#00ff9d")
        else:
            self.project_files_info.config(text="Файлы проекта: не найдены", fg="#ff4444")
    
    def update_settings_info(self, min_time: int, max_time: int):
        """Обновление информации о настройках"""
        minutes_min = min_time // 60
        seconds_min = min_time % 60
        minutes_max = max_time // 60
        seconds_max = max_time % 60
        self.settings_info.config(text=f"Текущий диапазон: {minutes_min}мин{seconds_min:02d}с - {minutes_max}мин{seconds_max:02d}с")
        self.min_time_var.set(str(min_time))
        self.max_time_var.set(str(max_time))
    
    def update_windows_list(self, windows_info: list, current_index: int):
        """Обновление списка окон"""
        self.windows_listbox.delete(0, tk.END)
        for info in windows_info:
            self.windows_listbox.insert(tk.END, info)
        self.current_label.config(text=f"Активное окно: Окно {current_index + 1}" if windows_info else "Активное окно: ---")
    
    def update_stage(self, stage: str, color: str = "#ffaa00"):
        """Обновление этапа"""
        self.stage_label.config(text=stage, fg=color)
    
    def get_selected_window_index(self) -> int:
        """Получение выбранного окна"""
        selection = self.windows_listbox.curselection()
        return selection[0] if selection else -1


class ChatPanel(tk.Frame):
    """Центральная панель чата - диалог с DeepSeek"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg="#1e1e2e", **kwargs)
        self._create_widgets()
    
    def _create_widgets(self):
        chat_frame = tk.LabelFrame(self, text="ДИАЛОГ С DEEPSEEK", font=("Arial", 11, "bold"),
                                   bg="#1e1e2e", fg="#00d4ff", relief=tk.GROOVE)
        chat_frame.pack(fill=tk.BOTH, expand=True, ipadx=5, ipady=5)
        
        # Создаем фрейм для чата с прокруткой
        chat_container = tk.Frame(chat_frame, bg="#1e1e2e")
        chat_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.chat_text = tk.Text(chat_container, bg="#2d2d3d", fg="#ffffff", font=("Arial", 10),
                                 wrap=tk.WORD, relief=tk.FLAT)
        self.chat_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(chat_container, command=self.chat_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.chat_text.config(yscrollcommand=scrollbar.set)
        
        # Поле ввода
        input_frame = tk.Frame(chat_frame, bg="#1e1e2e")
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.message_input = tk.Text(input_frame, height=5, bg="#3d3d4d", fg="#ffffff",
                                     font=("Arial", 10), wrap=tk.WORD, relief=tk.FLAT)
        self.message_input.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0,5))
        
        button_frame = tk.Frame(input_frame, bg="#1e1e2e")
        button_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.send_btn = tk.Button(button_frame, text="ОТПРАВИТЬ\nCtrl+Enter", font=("Arial", 9, "bold"),
                                  bg="#00d4ff", fg="#1e1e2e", relief=tk.FLAT, cursor="hand2",
                                  width=10, height=2)
        self.send_btn.pack(pady=(0,5))
        
        self.attach_btn = tk.Button(button_frame, text="ПРИКРЕПИТЬ\nФАЙЛЫ", font=("Arial", 9, "bold"),
                                    bg="#3d3d4d", fg="#ffffff", relief=tk.FLAT, cursor="hand2",
                                    width=10, height=2)
        self.attach_btn.pack(pady=(0,5))
        
        self.get_response_btn = tk.Button(button_frame, text="ПОЛУЧИТЬ\nОТВЕТ", font=("Arial", 9, "bold"),
                                          bg="#3d3d4d", fg="#ffffff", relief=tk.FLAT, cursor="hand2",
                                          width=10, height=2)
        self.get_response_btn.pack(pady=(0,5))
        
        self.clear_btn = tk.Button(button_frame, text="ОЧИСТИТЬ\nЧАТ", font=("Arial", 9, "bold"),
                                   bg="#ff4444", fg="#ffffff", relief=tk.FLAT, cursor="hand2",
                                   width=10, height=2)
        self.clear_btn.pack()
        
        # Файлы
        self._create_files_frame(chat_frame)
    
    def _create_files_frame(self, parent):
        self.files_frame = tk.LabelFrame(parent, text="ПРИКРЕПЛЁННЫЕ ФАЙЛЫ", 
                                         font=("Arial", 9, "bold"),
                                         bg="#1e1e2e", fg="#00ff9d", relief=tk.GROOVE)
        self.files_frame.pack(fill=tk.X, padx=5, pady=(0,5))
        
        self.files_listbox = tk.Listbox(self.files_frame, bg="#2d2d3d", fg="#00ff9d",
                                        font=("Arial", 8), height=4, relief=tk.FLAT)
        self.files_listbox.pack(fill=tk.X, padx=5, pady=5)
        
        btn_frame = tk.Frame(self.files_frame, bg="#1e1e2e")
        btn_frame.pack(fill=tk.X, padx=5, pady=(0,5))
        
        self.remove_file_btn = tk.Button(btn_frame, text="Удалить выбранный", font=("Arial", 8),
                                         bg="#ff4444", fg="#ffffff", relief=tk.FLAT, cursor="hand2")
        self.remove_file_btn.pack(side=tk.LEFT, padx=2)
        
        self.clear_files_btn = tk.Button(btn_frame, text="Очистить все", font=("Arial", 8),
                                         bg="#ffaa00", fg="#1e1e2e", relief=tk.FLAT, cursor="hand2")
        self.clear_files_btn.pack(side=tk.RIGHT, padx=2)
    
    def add_message(self, sender: str, message: str, is_user: bool = True):
        """Добавление сообщения в чат (отображается полный ответ DeepSeek)"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        self.chat_text.insert(tk.END, f"\n{'-'*50}\n", "separator")
        
        if is_user:
            self.chat_text.insert(tk.END, f"ПОЛЬЗОВАТЕЛЬ [{timestamp}]:\n", "user_header")
            self.chat_text.insert(tk.END, f"{message}\n", "user_msg")
        else:
            self.chat_text.insert(tk.END, f"DEEPSEEK AI [{timestamp}]:\n", "ai_header")
            self.chat_text.insert(tk.END, f"{message}\n", "ai_msg")
        
        self.chat_text.tag_config("separator", foreground="#444444")
        self.chat_text.tag_config("user_header", foreground="#00d4ff", font=("Arial", 10, "bold"))
        self.chat_text.tag_config("user_msg", foreground="#ffffff", font=("Arial", 10))
        self.chat_text.tag_config("ai_header", foreground="#00ff9d", font=("Arial", 10, "bold"))
        self.chat_text.tag_config("ai_msg", foreground="#dddddd", font=("Arial", 10))
        self.chat_text.see(tk.END)
    
    def get_user_message(self) -> str:
        """Получение сообщения пользователя"""
        return self.message_input.get("1.0", tk.END).strip()
    
    def clear_input(self):
        """Очистка поля ввода"""
        self.message_input.delete("1.0", tk.END)
    
    def clear_chat(self):
        """Очистка чата"""
        self.chat_text.delete("1.0", tk.END)
        self.add_message("AIC Assistant", "Чат очищен", is_user=False)
    
    def update_files_list(self, files: list):
        """Обновление списка прикреплённых файлов"""
        self.files_listbox.delete(0, tk.END)
        for file_path in files:
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            size_str = f"{file_size / 1024:.1f} KB" if file_size < 1024*1024 else f"{file_size / (1024*1024):.1f} MB"
            self.files_listbox.insert(tk.END, f"[Файл] {file_name} ({size_str})")
    
    def get_selected_file_index(self) -> int:
        """Получение индекса выбранного файла"""
        selection = self.files_listbox.curselection()
        return selection[0] if selection else -1
    
    def enable_send_button(self, enabled: bool):
        """Включение/отключение кнопки отправки"""
        if enabled:
            self.send_btn.config(state=tk.NORMAL, text="ОТПРАВИТЬ\nCtrl+Enter")
        else:
            self.send_btn.config(state=tk.DISABLED, text="ОТПРАВКА...")


class LogPanel(tk.Frame):
    """Правая панель логов"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg="#1e1e2e", width=280, **kwargs)
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
        """Добавление сообщения в лог"""
        from datetime import datetime
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
        """Очистка лога"""
        self.log_text.delete("1.0", tk.END)
