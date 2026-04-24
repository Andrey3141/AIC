# файл: voice/command_parser.py
import re

class CommandParser:
    """Парсер голосовых команд для преобразования русской речи в математические выражения"""
    
    def __init__(self):
        # Словари для преобразования чисел прописью до 100
        self.units = {
            'один': 1, 'одна': 1, 'одно': 1,
            'два': 2, 'две': 2,
            'три': 3,
            'четыре': 4,
            'пять': 5,
            'шесть': 6,
            'семь': 7,
            'восемь': 8,
            'девять': 9,
            'десять': 10,
            'одиннадцать': 11,
            'двенадцать': 12,
            'тринадцать': 13,
            'четырнадцать': 14,
            'пятнадцать': 15,
            'шестнадцать': 16,
            'семнадцать': 17,
            'восемнадцать': 18,
            'девятнадцать': 19
        }
        
        self.tens = {
            'двадцать': 20,
            'тридцать': 30,
            'сорок': 40,
            'пятьдесят': 50,
            'шестьдесят': 60,
            'семьдесят': 70,
            'восемьдесят': 80,
            'девяносто': 90
        }
        
        self.hundreds = {
            'сто': 100
        }
        
        # Операторы
        self.operators = {
            'плюс': '+',
            'минус': '-',
            'умножить': '*',
            'умножьте': '*',
            'умножь': '*',
            'разделить': '/',
            'поделить': '/',
            'открыть': '(',
            'открыть скобку': '(',
            'закрыть': ')',
            'закрыть скобку': ')',
            'скобка': '(',
            'точка': '.',
            'запятая': '.'
        }
    
    def parse_voice_text(self, text: str) -> str:
        """
        Преобразует текстовую команду на русском языке в математическое выражение
        
        Args:
            text (str): Распознанный текст на русском языке
            
        Returns:
            str: Математическое выражение
        """
        if not text:
            return ""
        
        text = text.lower().strip()
        
        # Заменяем операторы
        result = text
        for word, symbol in self.operators.items():
            # Заменяем только целые слова
            result = re.sub(r'\b' + re.escape(word) + r'\b', symbol, result)
        
        # Обрабатываем числа прописью (поддержка до 100)
        words = result.split()
        parsed_words = []
        i = 0
        
        while i < len(words):
            word = words[i]
            
            # Проверяем составные числа (десятки + единицы) до 99
            if i + 1 < len(words) and word in self.tens and words[i + 1] in self.units:
                number = self.tens[word] + self.units[words[i + 1]]
                parsed_words.append(str(number))
                i += 2
            # Проверяем числа от 1 до 19
            elif word in self.units:
                parsed_words.append(str(self.units[word]))
                i += 1
            # Проверяем десятки (20,30,40...90)
            elif word in self.tens:
                parsed_words.append(str(self.tens[word]))
                i += 1
            # Проверяем сотню (100)
            elif word in self.hundreds:
                parsed_words.append(str(self.hundreds[word]))
                i += 1
            else:
                # Сохраняем операторы и другие символы
                parsed_words.append(word)
                i += 1
        
        result = ' '.join(parsed_words)
        
        # Удаляем лишние пробелы вокруг операторов
        for op in ['+', '-', '*', '/', '(', ')']:
            result = result.replace(f' {op} ', f'{op}')
            result = result.replace(f'{op} ', f'{op}')
            result = result.replace(f' {op}', f'{op}')
        
        # Обрабатываем особые случаи
        result = re.sub(r'(\d+)\s+на\s+(\d+)', r'\1*\2', result)
        result = re.sub(r'(\d+)\s+разделить\s+на\s+(\d+)', r'\1/\2', result)
        result = re.sub(r'(\d+)\s+делить\s+на\s+(\d+)', r'\1/\2', result)
        result = re.sub(r'(\d+)\s+умножить\s+на\s+(\d+)', r'\1*\2', result)
        
        # Обработка десятичных дробей
        result = re.sub(r'(\d+)\s+точка\s+(\d+)', r'\1.\2', result)
        result = re.sub(r'(\d+)\s+запятая\s+(\d+)', r'\1.\2', result)
        
        # Удаляем лишние пробелы
        result = ' '.join(result.split())
        
        print(f"Распарсенное выражение: {result}")
        return result
