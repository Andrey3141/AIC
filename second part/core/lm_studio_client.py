import requests
import json
from typing import Optional, Callable

class LMStudioClient:
    def __init__(self, log_callback: Callable[[str, str], None] = None):
        self.log_callback = log_callback
        self.is_connected = False
        self.url = None
        self.model = None
        self.temperature = 0.6
        self.max_tokens = 4096
    
    def log(self, message: str, msg_type: str = "info"):
        if self.log_callback:
            self.log_callback(message, msg_type)
    
    def connect(self, url: str, model: str) -> bool:
        self.url = url
        self.model = model
        
        try:
            test_payload = {
                "model": model,
                "messages": [{"role": "user", "content": "ping"}],
                "max_tokens": 1,
                "stream": False
            }
            response = requests.post(url, json=test_payload, timeout=60)
            
            if response.status_code == 200:
                self.is_connected = True
                self.log("LM Studio доступен", "success")
                return True
            else:
                self.log(f"Ошибка: код {response.status_code}", "error")
                self.is_connected = False
                return False
        except requests.exceptions.ConnectionError:
            self.log("Не удалось подключиться к LM Studio. Запустите сервер (вкладка Developer → Start Server)", "error")
            self.is_connected = False
            return False
        except Exception as e:
            self.log(f"Ошибка: {str(e)}", "error")
            self.is_connected = False
            return False
    
    def disconnect(self):
        self.is_connected = False
        self.url = None
        self.model = None
    
    def send_message(self, message):
        if not self.is_connected or not self.url:
            self.log("Нет подключения к LM Studio", "error")
            return None
        
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": message}],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": False
        }
        
        headers = {"Content-Type": "application/json"}
        self.log(f"REQUEST: {self._escape(message)}", "info")
        
        try:
            self.log("Отправка запроса...", "info")
            response = requests.post(self.url, json=payload, headers=headers, timeout=1800)
            
            if response.status_code != 200:
                self.log(f"Ошибка API: {response.status_code}", "error")
                return None
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            self.log(f"Ответ получен ({len(content)} символов)", "success")
            self.log(f"RESPONSE: {self._escape(content)}", "info")
            return content
            
        except requests.exceptions.Timeout:
            self.log("Таймаут ожидания ответа", "error")
            return None
        except Exception as e:
            self.log(f"Ошибка: {str(e)}", "error")
            return None
            
    def inject_employees(self, prompt: str, employees: list):
        tokens = "\n".join([f"[{e['token']}]" for e in employees])
        return prompt.replace("{available_employees}", tokens)
        
    def _escape(self, text):
        return text.replace("\n", "\\n")
