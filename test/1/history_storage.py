# файл: history_storage.py
import json
import logging
import os
from typing import List, Dict, Any
from datetime import datetime

# Настройка логгирования
logging.basicConfig(
    filename='calculator.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class HistoryStorage:
    """Сохранение/загрузка истории в JSON, логгирование действий"""
    
    def __init__(self, filename: str = "calculator_history.json"):
        self.filename = filename
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        """Создание файла истории, если он не существует"""
        if not os.path.exists(self.filename):
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump([], f)
    
    def save_history(self, history: List[Dict[str, Any]]):
        """Сохранение истории в файл"""
        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
            logging.info(f"История сохранена. Записей: {len(history)}")
        except Exception as e:
            logging.error(f"Ошибка сохранения истории: {e}")
    
    def load_history(self) -> List[Dict[str, Any]]:
        """Загрузка истории из файла"""
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                history = json.load(f)
            logging.info(f"История загружена. Записей: {len(history)}")
            return history
        except Exception as e:
            logging.error(f"Ошибка загрузки истории: {e}")
            return []
    
    def clear_history(self):
        """Очистка истории"""
        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump([], f)
            logging.info("История очищена")
        except Exception as e:
            logging.error(f"Ошибка очистки истории: {e}")
    
    def log_action(self, action: str, details: str = ""):
        """Логгирование действий пользователя"""
        message = f"Действие: {action}"
        if details:
            message += f" | {details}"
        logging.info(message)
