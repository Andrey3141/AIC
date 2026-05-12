import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import os
import json
import subprocess

from ui.panels import ControlPanel, ChatPanel, LogPanel, SettingsDialog
from core.lm_studio_client import LMStudioClient
from core.orchestrator import Orchestrator

CONFIG_FILE = "config.json"
PROMPTS_FOLDER = "prompts"

subprocess.Popen(["python", "script.py"])

class AICApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("AIC - Artificial Intelligence Company v2.0")
        self.root.geometry("1400x900")
        self.root.configure(bg="#1e1e2e")
        
        self.config = self._load_config()
        self.employees = self.config.get("employees", [])
        self.lm_client = LMStudioClient(self.log)
        self.orchestrator = Orchestrator(self.lm_client, self.log, self.employees, on_message=self._on_employee_message)
        self.lm_client.temperature = self.config["temperature"]
        self.lm_client.max_tokens = self.config["max_tokens"]
        
        self.attached_files = []
        self.fullscreen = False
        self.conversation_history = []
        self._log_buffer = ""
        
        self._create_ui()
        self._apply_config_to_ui()
        self._bind_events()
        self._log_startup()
    
    def _load_config(self):
        default = {
            "lm_studio_url": "http://localhost:1234/v1/chat/completions",
            "model": "Qwen2.5-Coder-7B-Instruct",
            "temperature": 0.6,
            "max_tokens": 4096,
            "format_params": {"language": "Python", "platform": "Desktop", "ide": "VS Code"}
        }
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    saved = json.load(f)
                    default.update(saved)
            except:
                pass
        return default
    
    def _save_config(self):
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except:
            pass
    
    def _create_ui(self):
        main_paned = tk.PanedWindow(self.root, bg="#1e1e2e", sashwidth=5, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.control_panel = ControlPanel(main_paned, self.log)
        main_paned.add(self.control_panel, width=380)
        
        self.chat_panel = ChatPanel(main_paned, self.employees)
        main_paned.add(self.chat_panel, width=780)
        
        self.log_panel = LogPanel(main_paned)
        main_paned.add(self.log_panel, width=150)
    
    def _bind_events(self):
        self.control_panel.connect_btn.config(command=self.toggle_connection)
        self.control_panel.save_settings_btn.config(command=self.save_settings)
        self.control_panel.fullscreen_btn.config(command=self.toggle_fullscreen)
        
        self.chat_panel.send_btn.config(command=self.send_message)
        self.chat_panel.format_btn.config(command=self.open_format_dialog)
        self.chat_panel.attach_btn.config(command=self.attach_files)
        self.chat_panel.clear_btn.config(command=self.clear_chat)
        self.chat_panel.remove_file_btn.config(command=self.remove_selected_file)
        self.chat_panel.clear_files_btn.config(command=self.clear_all_files)
        
        self.chat_panel.message_input.bind("<Control-Return>", lambda e: self.send_message())
        self.root.bind("<F11>", self.toggle_fullscreen)
        self.root.bind("<Escape>", self.exit_fullscreen)
    
    def _log_startup(self):
        self.log("AIC - Artificial Intelligence Company v2.0 запущена", "success")
        self.log(f"URL: {self.config['lm_studio_url']}", "info")
        self.log(f"Модель: {self.config['model']}", "info")
        self.log("Статус: ожидание подключения к LM Studio", "info")
        self.control_panel.update_status(False)
    
    def log(self, message: str, msg_type: str = "info"):
        self.log_panel.add_log(message, msg_type)

        if hasattr(self, "_log_buffer"):
            self._log_buffer += message + "\n"
        else:
            self._log_buffer = message + "\n"
    
    def toggle_fullscreen(self, event=None):
        self.fullscreen = not self.fullscreen
        self.root.attributes('-fullscreen', self.fullscreen)
    
    def exit_fullscreen(self, event=None):
        if self.fullscreen:
            self.fullscreen = False
            self.root.attributes('-fullscreen', False)
    
    def save_settings(self):
        try:
            new_url = self.control_panel.url_var.get().strip()
            new_model = self.control_panel.model_var.get().strip()
            new_temp = float(self.control_panel.temp_var.get())
            new_max = int(self.control_panel.max_tokens_var.get())
            
            self.config["lm_studio_url"] = new_url
            self.config["model"] = new_model
            self.config["temperature"] = new_temp
            self.config["max_tokens"] = new_max
            self._save_config()
            
            self.control_panel.update_settings_info(new_url, new_model, new_temp, new_max)
            self.log("Настройки сохранены", "success")
        except ValueError:
            self.log("Ошибка: проверьте введённые значения", "error")
    
    def toggle_connection(self):
        if not self.lm_client.is_connected:
            self.connect_to_lm_studio()
        else:
            self.disconnect_lm_studio()
    
    def connect_to_lm_studio(self):
        def connect():
            self.control_panel.connect_btn.config(state=tk.DISABLED, text="ПОДКЛЮЧЕНИЕ...")
            success = self.lm_client.connect(self.config["lm_studio_url"], self.config["model"])
            
            if success:
                self.control_panel.update_status(True)
                self.log("Успешно подключено к LM Studio!", "success")
            else:
                self.control_panel.update_status(False)
                self.log("Ошибка подключения к LM Studio", "error")
            
            self.control_panel.connect_btn.config(state=tk.NORMAL)
        
        threading.Thread(target=connect, daemon=True).start()
    
    def disconnect_lm_studio(self):
        self.lm_client.disconnect()
        self.control_panel.update_status(False)
        self.log("Отключено от LM Studio", "warning")
    
    def open_format_dialog(self):
        current_params = self.config.get("format_params", {"language": "Python", "platform": "Desktop", "ide": "VS Code"})
        
        def on_save(params):
            self.config["format_params"] = params
            self._save_config()
            self.chat_panel.set_format_params(params)
            self.log(f"Формат запроса: {params['language']}, {params['platform']}, {params['ide']}", "success")
        
        SettingsDialog(self.root, current_params, on_save)
    
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
        if not self.chat_panel.is_format_set:
            messagebox.showwarning("Внимание", "Сначала настройте формат запроса (кнопка ФОРМАТ ЗАПРОСА)")
            return
        
        if not self.lm_client.is_connected:
            self.log("Сначала подключитесь к LM Studio!", "error")
            messagebox.showwarning("Ошибка", "Сначала подключитесь к LM Studio!")
            return
        
        user_message = self.chat_panel.get_user_message()
        if not user_message:
            return
        
        if not self.conversation_history:
            if not user_message.startswith("Язык:"):
                messagebox.showwarning("Внимание", "Первое сообщение должно быть в формате!")
                return
        
        files_content = []
        for file_path in self.attached_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    files_content.append(f"\n=== ФАЙЛ: {os.path.basename(file_path)} ===\n{content}")
            except Exception as e:
                files_content.append(f"\n=== ФАЙЛ: {os.path.basename(file_path)} ===\n[Ошибка чтения: {e}]")
        
        # Лог с правильным отправителем
        self.log("USER → pipeline start", "info")
        if self.attached_files:
            file_names = [os.path.basename(f) for f in self.attached_files]
            self.log(f"📎 Файлы: {', '.join(file_names)}", "info")
        self.log("⏳ Отправка...", "info")
        
        # В чат показываем от пользователя к начальнику
        display_text = user_message
        if self.attached_files:
            file_names = [os.path.basename(f) for f in self.attached_files]
            display_text += "\n\n📎 " + ", ".join(file_names)
        
        self.chat_panel.add_message("Пользователь", display_text)
        
        self.attached_files.clear()
        self.chat_panel.update_files_list([])
        
        def send():
            try:
                self.chat_panel.enable_send_button(False)

                result = self.orchestrator.run_pipeline(user_message)

                if "error" in result:
                    self.chat_panel.add_message("Система", f"[Ошибка: {result['error']}]")
                    return  
                
                final = result.get("final", "")
                responses = result.get("responses", {})
                distribution = result.get("distribution", {})
                    
                name_map = {e["token"].upper(): e["name"] for e in self.employees}
                    
            except Exception as e:
                self.log(f"Ошибка: {e}", "error")

            finally:
                self.chat_panel.enable_send_button(True)
        
        self.conversation_history.append(user_message)
        
        threading.Thread(target=send, daemon=True).start()
    
    def clear_chat(self):
        self.conversation_history.clear()
        self.chat_panel.clear_chat()
        self.log("Чат очищен", "info")
        
    def _apply_config_to_ui(self):
        self.control_panel.url_var.set(self.config.get("lm_studio_url", ""))
        self.control_panel.model_var.set(self.config.get("model", ""))
        self.control_panel.temp_var.set(str(self.config.get("temperature", 0.6)))
        self.control_panel.max_tokens_var.set(str(self.config.get("max_tokens", 4096)))
        
    def _on_employee_message(self, role, message, distribution):
        name_map = {e["token"].upper(): e["name"] for e in self.employees}

        # ВАЖНО: Tkinter поток
        self.root.after(0, lambda: self.chat_panel.add_message(
            name_map.get(role, role),
            message,
            distribution=distribution
        ))
        
    def _save_log_to_file(self):
        from datetime import datetime

        now = datetime.now()
        folder = f"logs/{now.strftime('%Y-%m-%d')}"
        os.makedirs(folder, exist_ok=True)

        filename = f"{folder}/{now.strftime('%H-%M-%S')}.txt"

        with open(filename, "w", encoding="utf-8") as f:
            f.write(self._log_buffer)

def main():
    root = tk.Tk()
    root.lift()
    root.attributes('-topmost', True)
    app = AICApp(root)
    root.after(100, lambda: root.attributes('-topmost', False))
    
    def on_close():
        app._save_log_to_file()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()

if __name__ == "__main__":
    main()
