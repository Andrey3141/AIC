# файл: calculator_viewmodel.py
from typing import List, Dict, Any, Callable
from calculator_model import CalculatorModel
from history_storage import HistoryStorage

class CalculatorViewModel:
    """Состояние UI, команды, привязка к модели, обработка клавиатуры"""
    
    def __init__(self):
        self.model = CalculatorModel()
        self.storage = HistoryStorage()
        self._expression = ""
        self._result = ""
        self._update_callback: Callable = None
        self._current_theme = "dark"
        
        # Загрузка сохранённой истории
        saved_history = self.storage.load_history()
        for entry in saved_history:
            self.model.add_to_history(entry['expression'], entry['result'])
        
        self._keyboard_map = {
            '0': '0', '1': '1', '2': '2', '3': '3', '4': '4',
            '5': '5', '6': '6', '7': '7', '8': '8', '9': '9',
            '+': '+', '-': '-', '*': '*', '/': '/',
            '.': '.', '(': '(', ')': ')', '%': '%',
            'Return': '=', 'Escape': 'C', 'BackSpace': '⌫'
        }
    
    def set_update_callback(self, callback: Callable):
        """Установка callback для обновления UI"""
        self._update_callback = callback
    
    def _notify_update(self):
        """Уведомление об изменении состояния"""
        if self._update_callback:
            self._update_callback()
    
    def get_expression(self) -> str:
        return self._expression
    
    def get_result(self) -> str:
        return self._result
    
    def append_to_expression(self, value: str):
        """Добавление символа к выражению"""
        self._expression += value
        self._notify_update()
    
    def clear_expression(self):
        """Очистка выражения"""
        self._expression = ""
        self._result = ""
        self._notify_update()
    
    def backspace(self):
        """Удаление последнего символа"""
        self._expression = self._expression[:-1]
        self._notify_update()
    
    def calculate(self):
        """Вычисление выражения"""
        if not self._expression:
            return
        
        result = self.model.evaluate_expression(self._expression)
        if result is not None:
            self._result = str(result)
            self.model.add_to_history(self._expression, result)
            self.storage.save_history(self.model.get_history())
            self._expression = str(result)
        else:
            self._result = "Ошибка"
            self._expression = ""
        
        self._notify_update()
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Получение истории"""
        return self.model.get_history()
    
    def clear_history(self):
        """Очистка истории"""
        self.model.clear_history()
        self.storage.clear_history()
        self._notify_update()
    
    def memory_set(self):
        """Установка текущего результата в память"""
        try:
            value = float(self._result) if self._result else 0
            self.model.set_memory(value)
        except ValueError:
            pass
    
    def memory_recall(self):
        """Восстановление из памяти"""
        memory = self.model.get_memory()
        if memory is not None:
            self._expression += str(memory)
            self._notify_update()
    
    def memory_clear(self):
        """Очистка памяти"""
        self.model.clear_memory()
    
    def memory_add(self):
        """Добавление текущего значения к памяти"""
        try:
            value = float(self._result) if self._result else 0
            self.model.memory_add(value)
        except ValueError:
            pass
    
    def handle_keyboard(self, event):
        """Обработка клавиатурных событий"""
        key = event.keysym
        
        if key in self._keyboard_map:
            action = self._keyboard_map[key]
            if action == '=':
                self.calculate()
            elif action == 'C':
                self.clear_expression()
            elif action == '⌫':
                self.backspace()
            else:
                self.append_to_expression(action)
    
    def toggle_theme(self) -> str:
        """Переключение темы"""
        self._current_theme = "light" if self._current_theme == "dark" else "dark"
        self._notify_update()
        return self._current_theme
    
    def get_current_theme(self) -> str:
        return self._current_theme
