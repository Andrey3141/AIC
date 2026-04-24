# файл: animation_controller.py
import threading
import time
import tkinter as tk
from typing import Optional

class AnimationController:
    """Плавные изменения цвета/размера, эффекты нажатия"""
    
    def __init__(self):
        self._active_animations = []
    
    def animate_press(self, widget: tk.Widget, duration: float = 0.1):
        """Анимация нажатия кнопки"""
        def animation():
            original_bg = widget.cget('bg')
            original_relief = widget.cget('relief')
            
            # Эффект нажатия
            widget.config(relief=tk.SUNKEN)
            
            # Изменение цвета
            self._animate_color(widget, original_bg, self._darken_color(original_bg), duration / 2)
            self._animate_color(widget, self._darken_color(original_bg), original_bg, duration / 2)
            
            # Восстановление рельефа
            widget.after(int(duration * 1000), lambda: widget.config(relief=original_relief))
        
        # Запуск анимации в отдельном потоке
        thread = threading.Thread(target=animation, daemon=True)
        thread.start()
    
    def _animate_color(self, widget: tk.Widget, start_color: str, end_color: str, duration: float):
        """Плавное изменение цвета"""
        steps = 20
        step_duration = duration / steps
        
        # Преобразование цветов в RGB
        start_rgb = self._hex_to_rgb(start_color)
        end_rgb = self._hex_to_rgb(end_color)
        
        if not start_rgb or not end_rgb:
            return
        
        def update_color(step):
            if step <= steps:
                # Интерполяция цвета
                r = start_rgb[0] + (end_rgb[0] - start_rgb[0]) * step / steps
                g = start_rgb[1] + (end_rgb[1] - start_rgb[1]) * step / steps
                b = start_rgb[2] + (end_rgb[2] - start_rgb[2]) * step / steps
                
                new_color = self._rgb_to_hex(int(r), int(g), int(b))
                widget.config(bg=new_color)
                
                # Следующий шаг
                widget.after(int(step_duration * 1000), lambda: update_color(step + 1))
        
        update_color(1)
    
    def _hex_to_rgb(self, hex_color: str):
        """Преобразование HEX в RGB"""
        hex_color = hex_color.lstrip('#')
        try:
            if len(hex_color) == 6:
                return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            elif len(hex_color) == 3:
                return tuple(int(hex_color[i]*2, 16) for i in range(3))
        except ValueError:
            return None
        return None
    
    def _rgb_to_hex(self, r: int, g: int, b: int) -> str:
        """Преобразование RGB в HEX"""
        return f'#{r:02x}{g:02x}{b:02x}'
    
    def _darken_color(self, color: str, factor: float = 0.7) -> str:
        """Затемнение цвета для эффекта нажатия"""
        rgb = self._hex_to_rgb(color)
        if rgb:
            darkened = tuple(int(c * factor) for c in rgb)
            return self._rgb_to_hex(*darkened)
        return "#000000"
    
    def animate_fade_in(self, widget: tk.Widget, duration: float = 0.3):
        """Анимация появления"""
        widget.after(10, lambda: self._animate_opacity(widget, 0, 1, duration))
    
    def animate_fade_out(self, widget: tk.Widget, duration: float = 0.3, callback=None):
        """Анимация исчезновения"""
        def on_complete():
            if callback:
                callback()
        
        self._animate_opacity(widget, 1, 0, duration, on_complete)
    
    def _animate_opacity(self, widget: tk.Widget, start: float, end: float, duration: float, callback=None):
        """Анимация прозрачности (имитация через цвета)"""
        # Примечание: tkinter не поддерживает прозрачность напрямую,
        # поэтому этот метод является заглушкой для совместимости
        pass
