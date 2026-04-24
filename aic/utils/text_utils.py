# файл: aic/utils/text_utils.py
import re
from typing import List

class TextUtils:
    """Утилиты для работы с текстом"""
    
    @staticmethod
    def remove_emojis(text: str) -> str:
        """Удаление эмодзи из текста"""
        emoji_pattern = re.compile(
            "["
            u"\U0001F600-\U0001F64F"
            u"\U0001F300-\U0001F5FF"
            u"\U0001F680-\U0001F6FF"
            u"\U0001F1E0-\U0001F1FF"
            u"\U00002702-\U000027B0"
            u"\U000024C2-\U0001F251"
            u"\U0001F900-\U0001F9FF"
            u"\U0001FA70-\U0001FAFF"
            u"\U00002600-\U000026FF"
            u"\U00002B50"
            u"\U00002757"
            "]+", 
            flags=re.UNICODE
        )
        return emoji_pattern.sub(r'', text)
    
    @staticmethod
    def truncate(text: str, max_length: int = 50) -> str:
        """Обрезка текста до указанной длины"""
        if len(text) <= max_length:
            return text
        return text[:max_length] + "..."
    
    @staticmethod
    def get_line_count(text: str) -> int:
        """Подсчёт количества строк в тексте"""
        return len(text.split('\n'))
