# файл: aic/models/config.py
from dataclasses import dataclass, field
from typing import Dict, Any
import json
import os

@dataclass
class Config:
    """Модель конфигурации приложения"""
    min_wait_time: int = 60
    max_wait_time: int = 600
    project_folder: str = ""
    prompts_folder: str = "prompts"
    browser_port: int = 9222
    
    @classmethod
    def load(cls, config_file: str = "aic_config.json") -> 'Config':
        """Загрузка конфигурации из файла"""
        config = cls()
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    config.min_wait_time = data.get('min_wait_time', 60)
                    config.max_wait_time = data.get('max_wait_time', 600)
                    config.project_folder = data.get('project_folder', '')
            except:
                pass
        return config
    
    def save(self, config_file: str = "aic_config.json") -> None:
        """Сохранение конфигурации в файл"""
        data = {
            'min_wait_time': self.min_wait_time,
            'max_wait_time': self.max_wait_time,
            'project_folder': self.project_folder
        }
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь"""
        return {
            'min_wait_time': self.min_wait_time,
            'max_wait_time': self.max_wait_time,
            'project_folder': self.project_folder
        }
