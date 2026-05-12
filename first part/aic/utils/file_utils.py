# файл: aic/utils/file_utils.py
import os
from typing import List, Optional

class FileUtils:
    """Утилиты для работы с файлами"""
    
    @staticmethod
    def read_file(file_path: str, encoding: str = 'utf-8') -> Optional[str]:
        """Чтение файла с обработкой ошибок"""
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return f.read().strip()
            except Exception as e:
                return f"[Ошибка чтения файла {file_path}: {str(e)}]"
        return None
    
    @staticmethod
    def get_project_files(project_folder: str) -> List[str]:
        """Получение списка файлов проекта"""
        if not project_folder or not os.path.exists(project_folder):
            return []
        
        files = []
        for f in ["CHANGELOG.md", "PROJECT_STRUCTURE.md", "README.md", "FAQ.md", "ROADMAP.md"]:
            if os.path.exists(os.path.join(project_folder, f)):
                files.append(f)
        return files
    
    @staticmethod
    def ensure_folder(folder_path: str) -> None:
        """Создание папки если её нет"""
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
