# файл: aic/core/file_search.py
import os
from typing import List, Dict, Set
from pathlib import Path

class FileSearch:
    """Поиск файлов в проекте алгоритмом расширения (BFS)"""
    
    def __init__(self, log_callback=None):
        self.log_callback = log_callback
    
    def log(self, message: str, msg_type: str = "info"):
        if self.log_callback:
            self.log_callback(message, msg_type)
    
    def find_files(self, project_folder: str, file_list: List[str]) -> Dict[str, str]:
        """
        Поиск файлов в проекте BFS алгоритмом
        
        Args:
            project_folder: корневая папка проекта
            file_list: список файлов для поиска (могут содержать пути, например "models/calculator.py")
        
        Returns:
            словарь {запрошенный_путь: найденный_абсолютный_путь}
        """
        if not project_folder or not os.path.exists(project_folder):
            self.log(f"Папка проекта не существует: {project_folder}", "error")
            return {}
        
        results = {}
        files_to_find = []
        
        # Разбираем каждый файл из списка
        for file_path in file_list:
            file_path = file_path.strip()
            if not file_path:
                continue
            
            # Определяем, это путь с подпапками или просто имя файла
            if '/' in file_path or '\\' in file_path:
                # Путь с подпапками, например "models/calculator.py"
                path_parts = file_path.replace('\\', '/').split('/')
                file_name = path_parts[-1]
                folder_path = '/'.join(path_parts[:-1])
                files_to_find.append({
                    'original': file_path,
                    'file_name': file_name,
                    'folder_path': folder_path,
                    'has_folder': True
                })
            else:
                # Просто имя файла
                files_to_find.append({
                    'original': file_path,
                    'file_name': file_path,
                    'folder_path': None,
                    'has_folder': False
                })
        
        # BFS поиск
        found_count = 0
        for item in files_to_find:
            if item['has_folder']:
                # Ищем файл в конкретной подпапке
                found_path = self._find_file_in_subfolder(project_folder, item['folder_path'], item['file_name'])
                if found_path:
                    results[item['original']] = found_path
                    found_count += 1
                    self.log(f"Найден файл: {item['original']} -> {found_path}", "success")
                else:
                    self.log(f"Файл не найден: {item['original']}", "warning")
            else:
                # Ищем файл во всём проекте BFS
                found_path = self._find_file_bfs(project_folder, item['file_name'])
                if found_path:
                    results[item['original']] = found_path
                    found_count += 1
                    self.log(f"Найден файл: {item['file_name']} -> {found_path}", "success")
                else:
                    self.log(f"Файл не найден: {item['file_name']}", "warning")
        
        self.log(f"Найдено файлов: {found_count}/{len(files_to_find)}", "info")
        return results
    
    def _find_file_bfs(self, root_folder: str, file_name: str) -> str:
        """
        Поиск файла BFS алгоритмом (сначала проверяем текущий уровень, потом все подпапки уровня)
        """
        try:
            queue = [root_folder]
            visited = set()
            
            while queue:
                current_level = []
                # Собираем все папки текущего уровня
                for folder in queue:
                    if folder in visited:
                        continue
                    visited.add(folder)
                    
                    try:
                        # Проверяем наличие файла в текущей папке
                        file_path = os.path.join(folder, file_name)
                        if os.path.isfile(file_path):
                            return file_path
                        
                        # Добавляем подпапки для следующего уровня
                        for item in os.listdir(folder):
                            item_path = os.path.join(folder, item)
                            if os.path.isdir(item_path):
                                current_level.append(item_path)
                    except (PermissionError, OSError):
                        continue
                
                queue = current_level
            
            return None
        except Exception as e:
            self.log(f"Ошибка поиска {file_name}: {str(e)}", "error")
            return None
    
    def _find_file_in_subfolder(self, root_folder: str, target_folder: str, file_name: str) -> str:
        """
        Поиск файла в конкретной подпапке BFS алгоритмом
        """
        try:
            # Сначала ищем целевую папку BFS
            target_path = self._find_folder_bfs(root_folder, target_folder)
            if not target_path:
                return None
            
            # В найденной папке ищем файл
            file_path = os.path.join(target_path, file_name)
            if os.path.isfile(file_path):
                return file_path
            
            # Если нет в корне, ищем в подпапках целевой папки BFS
            queue = [target_path]
            visited = set()
            
            while queue:
                current_level = []
                for folder in queue:
                    if folder in visited:
                        continue
                    visited.add(folder)
                    
                    file_path = os.path.join(folder, file_name)
                    if os.path.isfile(file_path):
                        return file_path
                    
                    try:
                        for item in os.listdir(folder):
                            item_path = os.path.join(folder, item)
                            if os.path.isdir(item_path):
                                current_level.append(item_path)
                    except (PermissionError, OSError):
                        continue
                
                queue = current_level
            
            return None
        except Exception as e:
            self.log(f"Ошибка поиска {target_folder}/{file_name}: {str(e)}", "error")
            return None
    
    def _find_folder_bfs(self, root_folder: str, target_folder: str) -> str:
        """Поиск папки BFS алгоритмом"""
        try:
            # Разбиваем путь на части
            folder_parts = target_folder.replace('\\', '/').split('/')
            
            queue = [root_folder]
            visited = set()
            
            while queue:
                current_level = []
                for folder in queue:
                    if folder in visited:
                        continue
                    visited.add(folder)
                    
                    # Проверяем, заканчивается ли текущий путь на target_folder
                    if folder.endswith(target_folder) or folder.endswith('/' + target_folder):
                        return folder
                    
                    # Для поиска по частям
                    current_folder_name = os.path.basename(folder)
                    if current_folder_name == folder_parts[0]:
                        # Нашли первую часть, проверяем остальные
                        full_path = self._build_path_recursive(folder, folder_parts[1:])
                        if full_path:
                            return full_path
                    
                    try:
                        for item in os.listdir(folder):
                            item_path = os.path.join(folder, item)
                            if os.path.isdir(item_path):
                                current_level.append(item_path)
                    except (PermissionError, OSError):
                        continue
                
                queue = current_level
            
            return None
        except Exception as e:
            return None
    
    def _build_path_recursive(self, current_path: str, remaining_parts: List[str]) -> str:
        """Рекурсивное построение пути по частям"""
        if not remaining_parts:
            return current_path
        
        try:
            for item in os.listdir(current_path):
                if item == remaining_parts[0]:
                    new_path = os.path.join(current_path, item)
                    return self._build_path_recursive(new_path, remaining_parts[1:])
            return None
        except:
            return None
    
    def read_file_content(self, file_path: str) -> str:
        """Чтение содержимого файла"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            self.log(f"Ошибка чтения файла {file_path}: {str(e)}", "error")
            return None
