# файл: aic/core/timer.py
import time
from typing import Callable, Optional

class Timer:
    """Таймер с обратным отсчётом"""
    
    def __init__(self, log_callback: Callable[[str, str], None]):
        self.log_callback = log_callback
        self.connection_checker: Optional[Callable[[], bool]] = None
    
    def set_connection_checker(self, checker: Callable[[], bool]) -> None:
        self.connection_checker = checker
    
    def wait_with_countdown(self, seconds: int) -> bool:
        """Ожидание с обратным отсчётом - логи только каждые 30 секунд"""
        remaining = seconds
        
        while remaining > 0:
            # Проверка соединения каждые 30 секунд
            if self.connection_checker and remaining % 30 == 0:
                if not self.connection_checker():
                    self.log_callback("Соединение с браузером потеряно", "error")
                    return False
            
            # Логируем только на 0, 30, 60 секунд и каждые 30 секунд
            if remaining == 0 or remaining % 30 == 0 or remaining <= 10:
                mins = remaining // 60
                secs = remaining % 60
                self.log_callback(f"Осталось {mins}мин{secs:02d}с...", "info")
            
            time.sleep(1)
            remaining -= 1
        
        return True
    
    def wait(self, seconds: int) -> None:
        """Простое ожидание без логов"""
        time.sleep(seconds)
