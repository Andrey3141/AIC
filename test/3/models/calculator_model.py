# файл: models/calculator_model.py
import ast
import operator

class CalculatorModel:
    """Модель калькулятора, отвечает за вычисление выражений"""
    
    def __init__(self):
        self.allowed_operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.USub: operator.neg,
            ast.UAdd: operator.pos
        }
        
        # Разрешенные типы узлов AST
        self.allowed_node_types = {
            ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant, ast.Num
        }
    
    def evaluate_expression(self, expression: str) -> float:
        """
        Вычисляет математическое выражение с поддержкой + - * / ( ) и десятичных дробей
        Возвращает float, округленный до 10 знаков
        
        Args:
            expression (str): Математическое выражение для вычисления
            
        Returns:
            float: Результат вычисления, округленный до 10 знаков
            
        Raises:
            ZeroDivisionError: При делении на ноль
            ValueError: При синтаксической ошибке или недопустимых операциях
        """
        if not expression or not expression.strip():
            raise ValueError("Выражение не может быть пустым")
        
        try:
            # Парсим выражение в AST
            tree = ast.parse(expression, mode='eval')
            
            # Проверяем безопасность AST
            self._validate_ast(tree)
            
            # Вычисляем выражение
            result = self._safe_eval(tree.body)
            
            # Округляем до 10 знаков
            return round(result, 10)
            
        except ZeroDivisionError:
            raise ZeroDivisionError("Деление на ноль")
        except (SyntaxError, ValueError, TypeError) as e:
            raise ValueError(f"Синтаксическая ошибка: {str(e)}")
        except Exception as e:
            raise ValueError(f"Ошибка в выражении: {str(e)}")
    
    def _validate_ast(self, node):
        """
        Рекурсивно проверяет AST на наличие небезопасных узлов
        
        Args:
            node: Узел AST для проверки
            
        Raises:
            ValueError: Если обнаружен неразрешенный тип узла
        """
        # Проверяем текущий узел
        if type(node) not in self.allowed_node_types and \
           type(node) not in self.allowed_operators:
            raise ValueError(f"Обнаружена недопустимая операция: {type(node).__name__}")
        
        # Рекурсивно проверяем дочерние узлы
        for child in ast.iter_child_nodes(node):
            self._validate_ast(child)
    
    def _safe_eval(self, node):
        """
        Безопасное вычисление AST узла
        
        Args:
            node: Узел AST для вычисления
            
        Returns:
            Результат вычисления узла
            
        Raises:
            ValueError: При неподдерживаемом типе узла
        """
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Num):  # для старых версий Python
            return node.n
        elif isinstance(node, ast.BinOp):
            left = self._safe_eval(node.left)
            right = self._safe_eval(node.right)
            op = self.allowed_operators.get(type(node.op))
            if op is None:
                raise ValueError(f"Неподдерживаемая операция: {type(node.op).__name__}")
            return op(left, right)
        elif isinstance(node, ast.UnaryOp):
            operand = self._safe_eval(node.operand)
            op = self.allowed_operators.get(type(node.op))
            if op is None:
                raise ValueError(f"Неподдерживаемая операция: {type(node.op).__name__}")
            return op(operand)
        elif isinstance(node, ast.Expression):
            return self._safe_eval(node.body)
        else:
            raise ValueError(f"Неподдерживаемый тип узла: {type(node).__name__}")
