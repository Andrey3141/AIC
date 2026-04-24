# файл: aic/ui/timer_display.py
import tkinter as tk
from tkinter import ttk

class TimerDisplay(tk.Frame):
    """Виджет для отображения таймера"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(bg="#2d2d3d")
        
        self.timer_label = tk.Label(
            self,
            text="Таймер: 00:00",
            font=("Arial", 11, "bold"),
            bg="#2d2d3d",
            fg="#ffaa00"
        )
        self.timer_label.pack(pady=5)
        
        self.progress = ttk.Progressbar(
            self,
            length=200,
            mode='determinate',
            style="Timer.Horizontal.TProgressbar"
        )
        self.progress.pack(pady=5, padx=10, fill=tk.X)
        
        self.is_running = False
        self.current_time = 0
        self.max_time = 0
    
    def start_timer(self, total_seconds: int):
        """Запуск таймера"""
        self.max_time = total_seconds
        self.current_time = 0
        self.is_running = True
        self.progress['maximum'] = total_seconds
        self.progress['value'] = 0
        self._update_timer()
    
    def stop_timer(self):
        """Остановка таймера"""
        self.is_running = False
        self.timer_label.config(text="Таймер: 00:00", fg="#888888")
        self.progress['value'] = 0
    
    def _update_timer(self):
        """Обновление отображения таймера"""
        if not self.is_running:
            return
        
        if self.current_time < self.max_time:
            self.current_time += 1
            remaining = self.max_time - self.current_time
            minutes = remaining // 60
            seconds = remaining % 60
            self.timer_label.config(text=f"Таймер: {minutes:02d}:{seconds:02d}", fg="#ffaa00")
            self.progress['value'] = self.current_time
            self.after(1000, self._update_timer)
        else:
            self.is_running = False
            self.timer_label.config(text="Таймер: 00:00", fg="#ff4444")
