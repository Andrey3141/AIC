# файл: aic/ui/main_window.py
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import time
import os

from aic.models.config import Config
from aic.utils.file_utils import FileUtils
from aic.core.browser_manager import BrowserManager
from aic.core.message_handler import MessageHandler
from aic.core.timer import Timer
from aic.handlers.stage_handler import StageHandler
from aic.handlers.token_parser import TokenParser
from aic.ui.panels import ControlPanel, ChatPanel, LogPanel

class AICApp:
    """Главное окно приложения"""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("AIC - Artificial Intelligence Company v10.3")
        self.root.geometry("1400x900")
        self.root.configure(bg="#1e1e2e")
        
        self.config = Config.load()
        
        self.browser_manager = None
        self.message_handler = None
        self.timer = None
        self.stage_handler = None
        
        self.attached_files = []
        self.fullscreen = False
        self.user_message = None
        
        self._create_ui()
        self._bind_events()
        
        FileUtils.ensure_folder(self.config.prompts_folder)
        
        self._log_startup()
    
    def _create_ui(self):
        main_paned = tk.PanedWindow(self.root, bg="#1e1e2e", sashwidth=5, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.control_panel = ControlPanel(main_paned, self.log)
        main_paned.add(self.control_panel, width=380)
        
        self.chat_panel = ChatPanel(main_paned)
        main_paned.add(self.chat_panel, width=680)
        
        self.log_panel = LogPanel(main_paned)
        main_paned.add(self.log_panel, width=280)
    
    def _bind_events(self):
        self.control_panel.connect_btn.config(command=self.toggle_connection)
        self.control_panel.select_btn.config(command=self.select_project_folder)
        self.control_panel.save_btn.config(command=self.save_project_path)
        self.control_panel.save_settings_btn.config(command=self.save_settings)
        self.control_panel.refresh_btn.config(command=self.refresh_windows)
        self.control_panel.switch_btn.config(command=self.switch_to_selected_window)
        self.control_panel.load_history_btn.config(command=self.load_history_from_browser)
        self.control_panel.fullscreen_btn.config(command=self.toggle_fullscreen)
        
        self.chat_panel.send_btn.config(command=self.send_message)
        self.chat_panel.attach_btn.config(command=self.attach_files)
        self.chat_panel.get_response_btn.config(command=self.get_response)
        self.chat_panel.clear_btn.config(command=self.clear_chat)
        self.chat_panel.remove_file_btn.config(command=self.remove_selected_file)
        self.chat_panel.clear_files_btn.config(command=self.clear_all_files)
        
        self.chat_panel.message_input.bind("<Control-Return>", lambda e: self.send_message())
        self.root.bind("<F11>", self.toggle_fullscreen)
        self.root.bind("<Escape>", self.exit_fullscreen)
    
    def _log_startup(self):
        self.log("AIC v10.3 запущена - 10-ЭТАПНАЯ СИСТЕМА", "success")
        self.log("Пользователь -> Начальник -> Аналитик -> Начальник -> Главный -> Разработчик -> Главный -> Аналитик -> Главный -> Начальник -> Пользователь", "info")
        self.log("Ожидание подключения к Chromium...", "info")
        
        self.check_prompt_files()
        self.control_panel.update_project_info(
            self.config.project_folder, 
            FileUtils.get_project_files(self.config.project_folder)
        )
        self.control_panel.update_settings_info(self.config.min_wait_time, self.config.max_wait_time)
    
    def check_prompt_files(self):
        required_files = ["Boss.txt", "Analyst.txt", "Chief_developer.txt", "Ordinary_developer.txt"]
        for filename in required_files:
            file_path = os.path.join(self.config.prompts_folder, filename)
            if os.path.exists(file_path):
                self.log(f"Файл {filename} найден", "success")
            else:
                self.log(f"Файл {filename} не найден", "error")
    
    def log(self, message: str, msg_type: str = "info"):
        if not message.startswith("STAGE_UPDATE:"):
            self.log_panel.add_log(message, msg_type)
        
        if message.startswith("=== ЭТАП"):
            import re
            match = re.search(r"=== ЭТАП (\d+):", message)
            if match:
                stage_num = match.group(1)
                color_map = {
                    "1": "#00d4ff", "2": "#ffaa00", "3": "#00ff9d",
                    "4": "#9b59b6", "5": "#e74c3c", "6": "#e67e22",
                    "7": "#3498db", "8": "#1abc9c", "9": "#f39c12", "10": "#2ecc71"
                }
                stage_name = message.split("===")[2].strip() if "===" in message else ""
                self.control_panel.update_stage(f"Этап {stage_num}/10: {stage_name}", color_map.get(stage_num, "#ffffff"))
    
    def toggle_fullscreen(self, event=None):
        self.fullscreen = not self.fullscreen
        self.root.attributes('-fullscreen', self.fullscreen)
        self.log(f"Полноэкранный режим: {'ВКЛ' if self.fullscreen else 'ВЫКЛ'}", "info")
    
    def exit_fullscreen(self, event=None):
        if self.fullscreen:
            self.fullscreen = False
            self.root.attributes('-fullscreen', False)
            self.log("Выход из полноэкранного режима", "info")
    
    def select_project_folder(self):
        folder = filedialog.askdirectory(title="Выберите папку проекта")
        if folder:
            self.config.project_folder = folder
            files = FileUtils.get_project_files(folder)
            self.control_panel.update_project_info(folder, files)
            self.log(f"Выбрана папка проекта: {folder}", "success")
    
    def save_project_path(self):
        self.config.save()
        self.log(f"Сохранён путь к проекту: {self.config.project_folder}", "success")
        messagebox.showinfo("Успех", f"Путь к проекту сохранён:\n{self.config.project_folder}")
    
    def save_settings(self):
        try:
            new_min = int(self.control_panel.min_time_var.get())
            new_max = int(self.control_panel.max_time_var.get())
            if new_min >= new_max:
                self.log("Ошибка: мин время должно быть меньше макс", "error")
                return
            if new_min < 60 or new_max > 600:
                self.log("Ошибка: диапазон 60-600 секунд", "error")
                return
            
            self.config.min_wait_time = new_min
            self.config.max_wait_time = new_max
            self.config.save()
            self.control_panel.update_settings_info(new_min, new_max)
            self.log(f"Настройки сохранены: {new_min}-{new_max} сек", "success")
        except ValueError:
            self.log("Ошибка: введите числа", "error")
    
    def toggle_connection(self):
        if not self.browser_manager or not self.browser_manager.is_connected:
            self.connect_to_browser()
        else:
            self.disconnect_browser()
    
    def connect_to_browser(self):
        def connect():
            self.control_panel.connect_btn.config(state=tk.DISABLED, text="ПОДКЛЮЧЕНИЕ...")
            self.browser_manager = BrowserManager(self.log)
            success = self.browser_manager.connect(self.config.browser_port)
            
            if success:
                self.message_handler = MessageHandler(self.browser_manager.driver, self.log)
                self.timer = Timer(self.log)
                self.timer.set_connection_checker(self.browser_manager.check_connection)
                self.stage_handler = StageHandler(
                    self.browser_manager, self.message_handler, self.timer, self.config, self.log
                )
                self.control_panel.update_status(True)
                self.refresh_windows()
            else:
                self.browser_manager = None
                self.control_panel.update_status(False)
            
            self.control_panel.connect_btn.config(state=tk.NORMAL)
        
        threading.Thread(target=connect, daemon=True).start()
    
    def disconnect_browser(self):
        if self.browser_manager:
            if self.message_handler:
                self.message_handler.is_connected = False
            self.browser_manager.disconnect()
            self.browser_manager = None
            self.message_handler = None
            self.timer = None
            self.stage_handler = None
        self.control_panel.update_status(False)
        self.control_panel.update_windows_list([], 0)
    
    def refresh_windows(self):
        if self.browser_manager and self.browser_manager.is_connected:
            windows_info = self.browser_manager.get_windows_info()
            self.control_panel.update_windows_list(windows_info, self.browser_manager.current_window)
    
    def switch_to_selected_window(self):
        if self.browser_manager:
            index = self.control_panel.get_selected_window_index()
            if index >= 0:
                self.browser_manager.switch_to_window(index)
                self.refresh_windows()
    
    def load_history_from_browser(self):
        if not self.browser_manager or not self.browser_manager.is_connected:
            self.log("Нет подключения к браузеру", "error")
            return
    
    def attach_files(self):
        files = filedialog.askopenfilenames(title="Выберите файлы")
        for file_path in files:
            if file_path not in self.attached_files:
                self.attached_files.append(file_path)
                self.chat_panel.update_files_list(self.attached_files)
                self.log(f"Прикреплён файл: {os.path.basename(file_path)}", "success")
    
    def remove_selected_file(self):
        index = self.chat_panel.get_selected_file_index()
        if index >= 0 and index < len(self.attached_files):
            removed = self.attached_files.pop(index)
            self.chat_panel.update_files_list(self.attached_files)
            self.log(f"Удалён файл: {os.path.basename(removed)}", "warning")
    
    def clear_all_files(self):
        self.attached_files.clear()
        self.chat_panel.update_files_list([])
        self.log("Все файлы удалены", "warning")
    
    def send_message(self):
        if not self.browser_manager or not self.browser_manager.check_connection():
            self.log("Сначала подключитесь к Chromium!", "error")
            messagebox.showwarning("Ошибка", "Сначала подключитесь к Chromium!")
            return
        
        if self.browser_manager.windows_count < 4:
            self.log(f"ОШИБКА: Требуется минимум 4 окна, открыто {self.browser_manager.windows_count}", "error")
            messagebox.showerror("Ошибка", f"Требуется минимум 4 окна!\nОткрыто: {self.browser_manager.windows_count}")
            return
        
        user_message = self.chat_panel.get_user_message()
        if not user_message and not self.attached_files:
            return
        
        if not self.config.project_folder:
            self.log("Ошибка: не выбрана папка проекта!", "error")
            messagebox.showerror("Ошибка", "Сначала выберите папку проекта!")
            return
        
        self.user_message = user_message if user_message else "[Отправка с файлами]"
        
        display_text = user_message if user_message else "[Отправка с файлами]"
        if self.attached_files:
            file_names = [os.path.basename(f) for f in self.attached_files]
            display_text += "\n\n[Прикреплённые файлы]:\n" + "\n".join(f"  - {name}" for name in file_names)
        
        self.chat_panel.add_message("Пользователь", display_text, is_user=True)
        
        files_to_send = self.attached_files.copy()
        user_message_text = user_message
        
        self.chat_panel.clear_input()
        self.attached_files.clear()
        self.chat_panel.update_files_list([])
        
        def execute_pipeline():
            try:
                self.chat_panel.enable_send_button(False)
                
                success = self.stage_handler.execute_full_pipeline(user_message_text, files_to_send)
                
                if success:
                    self.control_panel.update_stage("Готов", "#00ff9d")
                else:
                    self.control_panel.update_stage("Ошибка", "#ff4444")
                    self.log("=== ОБРАБОТКА ПРЕРВАНА ИЗ-ЗА ОШИБКИ ===", "error")
                
            except Exception as e:
                self.log(f"Ошибка: {str(e)}", "error")
                self.control_panel.update_stage("Ошибка", "#ff4444")
            finally:
                self.chat_panel.enable_send_button(True)
        
        threading.Thread(target=execute_pipeline, daemon=True).start()
    
    def get_response(self):
        if not self.message_handler:
            self.log("Нет подключения", "error")
            return
        
        def get():
            try:
                self.log("Ручной поиск ответов...", "info")
                self.message_handler.click_continue_button()
                time.sleep(10)
                
                last_assistant_id = self.message_handler.get_last_assistant_message_id()
                response = self.message_handler.wait_for_new_assistant_message(last_assistant_id, 30)
                
                if response:
                    self.chat_panel.add_message("DeepSeek AI", response, is_user=False)
                    self.log("Найден ответ", "success")
                else:
                    self.log("Ответы не найдены", "warning")
            except Exception as e:
                self.log(f"Ошибка: {str(e)}", "error")
        
        threading.Thread(target=get, daemon=True).start()
    
    def clear_chat(self):
        self.chat_panel.clear_chat()
        self.log("Чат очищен", "info")
