# файл: aic/core/browser_manager.py
from typing import List, Optional, Callable
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time

class BrowserManager:
    """Управление браузером и окнами"""
    
    def __init__(self, log_callback: Callable[[str, str], None]):
        self.driver = None
        self.is_connected = False
        self.window_handles: List[str] = []
        self.current_window_index = 0
        self.log_callback = log_callback
        self._connection_logged = False
    
    def connect(self, port: int = 9222) -> bool:
        try:
            self.log_callback(f"Подключение к Chromium на порту {port}...", "info")
            options = Options()
            options.add_experimental_option("debuggerAddress", f"127.0.0.1:{port}")
            self.driver = webdriver.Chrome(options=options)
            self.window_handles = self.driver.window_handles
            
            if self.window_handles:
                self.driver.switch_to.window(self.window_handles[0])
            
            self.is_connected = True
            if not self._connection_logged:
                self.log_callback("Успешно подключено к браузеру!", "success")
                self._connection_logged = True
            return True
            
        except Exception as e:
            self.log_callback(f"Ошибка подключения: {str(e)}", "error")
            self.is_connected = False
            return False
    
    def disconnect(self) -> None:
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
        self.is_connected = False
        self.window_handles = []
        self.current_window_index = 0
        self._connection_logged = False
        self.log_callback("Соединение с браузером разорвано", "warning")
    
    def check_connection(self) -> bool:
        """Проверка активности соединения"""
        if not self.driver or not self.is_connected:
            return False
        try:
            self.driver.title
            return True
        except:
            self.is_connected = False
            return False
    
    def open_new_tab(self, url: str = "https://chat.deepseek.com/") -> bool:
        if not self.check_connection():
            return False
        
        try:
            self.driver.execute_script(f"window.open('{url}', '_blank');")
            self._refresh_windows()
            self.switch_to_window(len(self.window_handles) - 1)
            self.log_callback(f"Открыта новая вкладка: {url}", "success")
            return True
        except Exception as e:
            self.log_callback(f"Ошибка открытия вкладки: {str(e)}", "error")
            return False
    
    def find_window_by_title(self, title_contains: str) -> int:
        if not self.check_connection():
            return -1
        
        self._refresh_windows()
        
        for i, handle in enumerate(self.window_handles):
            try:
                self.driver.switch_to.window(handle)
                title = self.driver.title.lower()
                if title_contains.lower() in title:
                    if 0 <= self.current_window_index < len(self.window_handles):
                        self.driver.switch_to.window(self.window_handles[self.current_window_index])
                    return i
            except:
                pass
        
        if 0 <= self.current_window_index < len(self.window_handles):
            self.driver.switch_to.window(self.window_handles[self.current_window_index])
        
        return -1
    
    def switch_to_window(self, index: int) -> bool:
        if not self.check_connection():
            return False
        
        if 0 <= index < len(self.window_handles):
            try:
                self.driver.switch_to.window(self.window_handles[index])
                self.current_window_index = index
                return True
            except Exception as e:
                self.log_callback(f"Ошибка переключения: {str(e)}", "error")
                return False
        return False
    
    def ensure_empty_chat(self) -> bool:
        if not self.check_connection():
            return False
        
        try:
            new_chat_selectors = [
                "//button[contains(text(), 'Новый чат')]",
                "//button[contains(text(), 'New chat')]",
                "//div[contains(@class, 'new-chat')]",
                "//button[contains(@aria-label, 'New chat')]",
                "//span[contains(text(), 'Новый чат')]",
                "//button[contains(@class, 'new-chat')]"
            ]
            
            for selector in new_chat_selectors:
                try:
                    new_chat_btn = self.driver.find_element(By.XPATH, selector)
                    if new_chat_btn and new_chat_btn.is_displayed():
                        new_chat_btn.click()
                        self.log_callback("Создан новый чат", "success")
                        time.sleep(2)
                        break
                except:
                    pass
            
            wait = WebDriverWait(self.driver, 5)
            input_field = wait.until(EC.presence_of_element_located((By.TAG_NAME, "textarea")))
            input_field.clear()
            self.log_callback("Чат очищен, поле ввода готово", "success")
            return True
            
        except Exception as e:
            self.log_callback(f"Чат уже пуст или не требует очистки", "info")
            return True
    
    def get_windows_info(self) -> List[str]:
        if not self.check_connection():
            return []
        
        self._refresh_windows()
        windows_info = []
        
        for i, handle in enumerate(self.window_handles):
            try:
                self.driver.switch_to.window(handle)
                title = self.driver.title[:35] if self.driver.title else "Новая вкладка"
                windows_info.append(f"Окно {i+1}: {title}")
            except:
                windows_info.append(f"Окно {i+1}: недоступно")
        
        if 0 <= self.current_window_index < len(self.window_handles):
            self.driver.switch_to.window(self.window_handles[self.current_window_index])
        
        return windows_info
    
    def is_input_available(self) -> bool:
        if not self.check_connection():
            return False
        
        try:
            input_field = self.driver.find_element(By.TAG_NAME, "textarea")
            return input_field.is_displayed() and input_field.is_enabled()
        except:
            return False
    
    def _refresh_windows(self) -> None:
        if self.driver:
            try:
                self.window_handles = self.driver.window_handles
            except:
                self.window_handles = []
    
    @property
    def current_window(self) -> int:
        return self.current_window_index
    
    @property
    def windows_count(self) -> int:
        return len(self.window_handles)
