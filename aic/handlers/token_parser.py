# файл: aic/handlers/token_parser.py
import re

class TokenParser:
    """Парсер токенов статусов"""
    
    # Токены начальника
    BOSS_TOKENS = {
        "WAITING_USER": "=== СТАТУС ===\nЖДУ ОТВЕТА ПОЛЬЗОВАТЕЛЯ",
        "SENT_TO_USER": "=== СТАТУС ===\nОТПРАВЛЕНО ПОЛЬЗОВАТЕЛЮ",
        "NEEDS_REVISION": "=== СТАТУС ===\nТРЕБУЕТ ДОРАБОТКИ",
        "WAITING_ANALYST": "=== СТАТУС ===\nЖДУ УТОЧНЁННОЕ ТЗ",
        "WAITING_CHIEF": "=== СТАТУС ===\nЖДУ ОТЧЁТ И ДОКУМЕНТАЦИЮ",
        "NEEDS_FULL_CYCLE": "=== СТАТУС ===\nТРЕБУЕТ ПОВТОРНОГО ЦИКЛА"
    }
    
    # Токены аналитика
    ANALYST_TOKENS = {
        "SENT_TO_BOSS": "=== СТАТУС ===\nОТПРАВЛЕНО НАЧАЛЬНИКУ",
        "SENT_TO_CHIEF": "=== СТАТУС ===\nОТПРАВЛЕНО ГЛАВНОМУ РАЗРАБОТЧИКУ"
    }
    
    # Токены главного разработчика
    CHIEF_TOKENS = {
        "NEEDS_TZ_REVISION": "=== СТАТУС ===\nТРЕБУЕТ ДОРАБОТКИ ТЗ",
        "SENT_TO_BOSS": "=== СТАТУС ===\nОТПРАВЛЕНО НАЧАЛЬНИКУ",
        "WAITING_CODE": "=== СТАТУС ===\nЖДУ КОД",
        "NEEDS_CODE_REVISION": "=== СТАТУС ===\nТРЕБУЕТ ДОРАБОТКИ КОДА",
        "WAITING_DOCS": "=== СТАТУС ===\nЖДУ ДОКУМЕНТАЦИЮ",
        "NEEDS_DOCS_REVISION": "=== СТАТУС ===\nТРЕБУЕТ ДОРАБОТКИ ДОКУМЕНТАЦИИ"
    }
    
    @classmethod
    def _normalize_text(cls, text: str) -> str:
        """Нормализация текста для поиска"""
        if not text:
            return ""
        return text.replace('\r\n', '\n').replace('\r', '\n').strip()
    
    @classmethod
    def parse_boss_token(cls, message: str) -> str:
        if not message:
            return "NO_TOKEN"
        
        normalized = cls._normalize_text(message)
        
        for key, value in cls.BOSS_TOKENS.items():
            if value in normalized:
                return key
        
        # Гибкий поиск
        if "ЖДУ УТОЧНЁННОЕ ТЗ" in normalized:
            return "WAITING_ANALYST"
        if "ЖДУ ОТЧЁТ И ДОКУМЕНТАЦИЮ" in normalized:
            return "WAITING_CHIEF"
        if "ТРЕБУЕТ ДОРАБОТКИ" in normalized:
            return "NEEDS_REVISION"
        if "ЖДУ ОТВЕТА ПОЛЬЗОВАТЕЛЯ" in normalized:
            return "WAITING_USER"
            
        return "NO_TOKEN"
    
    @classmethod
    def parse_analyst_token(cls, message: str) -> str:
        if not message:
            return "NO_TOKEN"
        
        normalized = cls._normalize_text(message)
        
        for key, value in cls.ANALYST_TOKENS.items():
            if value in normalized:
                return key
        
        if "ОТПРАВЛЕНО ГЛАВНОМУ РАЗРАБОТЧИКУ" in normalized:
            return "SENT_TO_CHIEF"
        if "ОТПРАВЛЕНО НАЧАЛЬНИКУ" in normalized:
            return "SENT_TO_BOSS"
            
        return "NO_TOKEN"
    
    @classmethod
    def parse_chief_token(cls, message: str) -> str:
        if not message:
            return "NO_TOKEN"
        
        normalized = cls._normalize_text(message)
        
        for key, value in cls.CHIEF_TOKENS.items():
            if value in normalized:
                return key
        
        # Гибкий поиск
        if "ЖДУ КОД" in normalized:
            return "WAITING_CODE"
        if "ЖДУ ДОКУМЕНТАЦИЮ" in normalized:
            return "WAITING_DOCS"
        if "ТРЕБУЕТ ДОРАБОТКИ КОДА" in normalized:
            return "NEEDS_CODE_REVISION"
        if "ТРЕБУЕТ ДОРАБОТКИ ДОКУМЕНТАЦИИ" in normalized:
            return "NEEDS_DOCS_REVISION"
        if "ТРЕБУЕТ ДОРАБОТКИ ТЗ" in normalized:
            return "NEEDS_TZ_REVISION"
        if "ОТПРАВЛЕНО НАЧАЛЬНИКУ" in normalized:
            return "SENT_TO_BOSS"
            
        return "NO_TOKEN"
    
    @classmethod
    def remove_boss_token(cls, message: str) -> str:
        result = message
        for value in cls.BOSS_TOKENS.values():
            result = result.replace(value, "")
        return result.strip()
    
    @classmethod
    def remove_analyst_token(cls, message: str) -> str:
        result = message
        for value in cls.ANALYST_TOKENS.values():
            result = result.replace(value, "")
        return result.strip()
    
    @classmethod
    def remove_chief_token(cls, message: str) -> str:
        result = message
        for value in cls.CHIEF_TOKENS.values():
            result = result.replace(value, "")
        return result.strip()
    
    @classmethod
    def parse_file_list_token(cls, message: str) -> list:
        token_start = "=== ФАЙЛЫ ПРОЕКТА ==="
        token_end = "=== КОНЕЦ ФАЙЛОВ ПРОЕКТА ==="
        
        if token_start not in message:
            return []
        
        parts = message.split(token_start)
        if len(parts) < 2:
            return []
        
        content = parts[1].strip()
        
        if token_end in content:
            content = content.split(token_end)[0].strip()
        
        files = []
        for line in content.split('\n'):
            line = line.strip()
            if line and not line.startswith('===') and not line.startswith('{'):
                if not line.startswith('Библиотеки:') and not line.startswith('Конкретная'):
                    files.append(line)
        
        return files
    
    @classmethod
    def extract_code_block(cls, message: str) -> str:
        code_token = "=== КОД ==="
        if code_token not in message:
            return ""
        
        start_idx = message.find(code_token) + len(code_token)
        next_token = "=== СТАТУС ==="
        end_idx = message.find(next_token, start_idx)
        
        if end_idx == -1:
            return message[start_idx:].strip()
        return message[start_idx:end_idx].strip()
