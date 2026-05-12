# файл: aic/core/timer.py
import time
import threading
from typing import Callable, Optional

class Timer:
    """Таймер с обратным отсчётом"""
    
    def __init__(self, log_callback: Callable[[str, str], None]):
        self.log_callback = log_callback
        self.connection_checker: Optional[Callable[[], bool]] = None
        self._current_timer: Optional[threading.Timer] = None
        self._current_interval: int = 0
    
    def set_connection_checker(self, checker: Callable[[], bool]) -> None:
        self.connection_checker = checker
    
    def reset_timer(self) -> None:
        """Перезапускает таймер ожидания (сбрасывает текущий отсчёт)"""
        # Сохранить текущий интервал, отменить текущий таймер, запустить новый
        if self._current_timer is not None:
            self._current_timer.cancel()
            self._current_timer = None
        
        if self._current_interval > 0:
            self.log_callback("Таймер ожидания сброшен и перезапущен", "info")
            # Запускаем новый таймер с сохранённым интервалом
            self._start_countdown(self._current_interval)
    
    def _start_countdown(self, seconds: int) -> None:
        """Запускает обратный отсчёт с заданным интервалом"""
        if self._current_timer is not None:
            self._current_timer.cancel()
        
        self._current_interval = seconds
        self._current_timer = threading.Timer(seconds, self._on_timeout)
        self._current_timer.daemon = True
        self._current_timer.start()
    
    def _on_timeout(self) -> None:
        """Обработчик истечения таймера"""
        self.log_callback("Время ожидания истекло", "warning")
        self._current_timer = None
    
    def wait_with_countdown(self, seconds: int) -> bool:
        """Ожидание с обратным отсчётом - логи только каждые 30 секунд"""
        self._current_interval = seconds
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
        
        self._current_timer = None
        return True
    
    def wait(self, seconds: int) -> None:
        """Простое ожидание без логов"""
        time.sleep(seconds)
