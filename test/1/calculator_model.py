# файл: calculator_model.py
import math
import re
from typing import List, Dict, Any, Optional

class CalculatorModel:
    """Математическая логика, память, безопасный разбор выражений"""
    
    def __init__(self):
        self._memory: Optional[float] = None
        self._history: List[Dict[str, Any]] = []
        self._allowed_pattern = re.compile(
            r'^[\d\s\+\-\*\/\(\)\.\*\*\%\^]+$'
        )
        self._functions = {
            'sqrt': math.sqrt,
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'log': math.log10,
            'ln': math.log,
            'exp': math.exp,
            'pi': math.pi,
            'e': math.e
        }
    
    def evaluate_expression(self, expression: str) -> Optional[float]:
        """Безопасное вычисление математического выражения"""
        try:
            # Очистка и проверка выражения
            expression = expression.replace('^', '**')
            expression = expression.replace(' ', '')
            
            if not self._is_safe_expression(expression):
                return None
            
            # Замена математических функций
            for func_name, func in self._functions.items():
                if func_name in expression:
                    if func_name in ['pi', 'e']:
                        expression = expression.replace(func_name, str(func))
                    else:
                        # Используем безопасный eval с контекстом функций
                        pass
            
            # Безопасное вычисление через eval с ограниченным пространством имён
            safe_dict = {**self._functions}
            result = eval(expression, {"__builtins__": {}}, safe_dict)
            
            if isinstance(result, (int, float)) and not math.isnan(result) and not math.isinf(result):
                return round(result, 10)
            return None
        except Exception:
            return None
    
    def _is_safe_expression(self, expression: str) -> bool:
        """Проверка выражения на опасные символы"""
        # Разрешаем цифры, операции, скобки, точки и названия функций
        safe_chars_pattern = r'^[\d\s\+\-\*\/\(\)\.\*\*\%\^a-zA-Z_]+$'
        if not re.match(safe_chars_pattern, expression):
            return False
        
        # Запрещаем опасные конструкции
        dangerous = ['__', 'import', 'exec', 'eval', 'compile', 'open', 'file']
        for word in dangerous:
            if word in expression:
                return False
        
        return True
    
    def add_to_history(self, expression: str, result: float):
        """Добавление записи в историю"""
        self._history.append({
            'expression': expression,
            'result': result
        })
        # Ограничиваем историю 50 записями
        if len(self._history) > 50:
            self._history.pop(0)
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Получение всей истории"""
        return self._history.copy()
    
    def clear_history(self):
        """Очистка истории"""
        self._history.clear()
    
    def set_memory(self, value: Optional[float]):
        """Установка значения в память"""
        self._memory = value
    
    def get_memory(self) -> Optional[float]:
        """Получение значения из памяти"""
        return self._memory
    
    def clear_memory(self):
        """Очистка памяти"""
        self._memory = None
    
    def memory_add(self, value: float):
        """Добавление к значению в памяти"""
        if self._memory is None:
            self._memory = value
        else:
            self._memory += value
    
    def memory_subtract(self, value: float):
        """Вычитание из значения в памяти"""
        if self._memory is None:
            self._memory = -value
        else:
            self._memory -= value
