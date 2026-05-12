# файл: aic/handlers/tester_handler.py
import os
import shutil
import subprocess
import sys
import json
from datetime import datetime
from typing import Dict, List, Optional, Callable
from pathlib import Path


class TesterHandler:
    """Полный обработчик для Тестировщика (без токенов)"""
    
    def __init__(self, project_folder: str, log_callback: Callable):
        self.project_folder = project_folder
        self.log = log_callback
        
        # Определяем пути
        self.aic_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.tests_folder = os.path.join(self.aic_root, "testers", "unit_tests")
        self.copy_folder = os.path.join(self.aic_root, "copy")
        self.output_folder = os.path.join(self.aic_root, "output")
        
        # Создаём необходимые папки
        os.makedirs(self.copy_folder, exist_ok=True)
        os.makedirs(self.output_folder, exist_ok=True)
        os.makedirs(self.tests_folder, exist_ok=True)
    
    def create_backup(self) -> str:
        """Создаёт резервную копию текущих тестов в папку aic/copy/"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = os.path.join(self.copy_folder, f"unit_tests_backup_{timestamp}")
        
        if os.path.exists(self.tests_folder):
            # Копируем все тестовые файлы
            shutil.copytree(self.tests_folder, backup_dir, dirs_exist_ok=True)
            self.log(f"Создана резервная копия тестов: {backup_dir}", "success")
            return backup_dir
        else:
            self.log("Папка с тестами не существует, резервная копия не создана", "warning")
            return None
    
    def restore_from_backup(self, backup_path: str) -> bool:
        """Восстанавливает тесты из резервной копии"""
        if backup_path and os.path.exists(backup_path):
            shutil.copytree(backup_path, self.tests_folder, dirs_exist_ok=True)
            self.log(f"Восстановлены тесты из резервной копии: {backup_path}", "success")
            return True
        return False
    
    def save_tester_files(self, tester_response: str, files: Dict[str, str]) -> bool:
        """
        Сохраняет файлы, которые написал Тестировщик, в папку output
        files: {"test_continue_button.py": "содержимое файла", ...}
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for filename, content in files.items():
            if filename.endswith('.py'):
                output_path = os.path.join(self.output_folder, f"tester_{timestamp}_{filename}")
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.log(f"Сохранён файл тестов: {output_path}", "info")
        
        # Сохраняем полный ответ тестировщика
        response_path = os.path.join(self.output_folder, f"tester_response_{timestamp}.md")
        with open(response_path, 'w', encoding='utf-8') as f:
            f.write(tester_response)
        self.log(f"Сохранён ответ тестировщика: {response_path}", "info")
        
        return True
    
    def replace_test_files(self, new_files: Dict[str, str]) -> bool:
        """
        Заменяет файлы тестов в проекте на новые (написанные Тестировщиком)
        new_files: {"test_continue_button.py": "новое содержимое", ...}
        """
        try:
            for filename, content in new_files.items():
                if filename.endswith('.py'):
                    filepath = os.path.join(self.tests_folder, filename)
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    self.log(f"Обновлён файл тестов: {filepath}", "success")
            return True
        except Exception as e:
            self.log(f"Ошибка замены файлов тестов: {str(e)}", "error")
            return False
    
    def get_current_test_files(self) -> Dict[str, str]:
        """Получает содержимое текущих тестовых файлов в проекте"""
        files_content = {}
        
        if os.path.exists(self.tests_folder):
            for filename in os.listdir(self.tests_folder):
                if filename.endswith('.py') and filename != '__init__.py':
                    filepath = os.path.join(self.tests_folder, filename)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        files_content[filename] = f.read()
        
        return files_content
    
    def build_message_for_tester(self, chief_response: str, files_to_send: List[str]) -> str:
        """
        Формирует сообщение для Тестировщика в чат DeepSeek
        Формат точно как в схеме:
        === ФАЙЛЫ ПРОЕКТА ===
        файл1.py
        файл2.py
        === КОНЕЦ ФАЙЛОВ ПРОЕКТА ===
        [задание для тестировщика]
        """
        # Читаем промт Tester.txt
        prompts_folder = os.path.join(self.aic_root, "prompts")
        tester_prompt_path = os.path.join(prompts_folder, "Tester.txt")
        
        tester_prompt = ""
        if os.path.exists(tester_prompt_path):
            with open(tester_prompt_path, 'r', encoding='utf-8') as f:
                tester_prompt = f.read()
        else:
            tester_prompt = "Ты - Тестировщик. Напиши unit-тесты на основе описания функционала."
        
        # Формируем список файлов для отправки
        files_list = "\n".join(files_to_send)
        
        # Извлекаем описание функционала из ответа главного
        # (убираем часть с файлами проекта, если она есть)
        clean_chief = chief_response
        if "=== ФАЙЛЫ ПРОЕКТА ===" in clean_chief:
            import re
            clean_chief = re.sub(r'=== ФАЙЛЫ ПРОЕКТА ===.*?=== КОНЕЦ ФАЙЛОВ ПРОЕКТА ===', '', clean_chief, flags=re.DOTALL)
        
        message = f"""{tester_prompt}

=== ФАЙЛЫ ПРОЕКТА ===
{files_list}
=== КОНЕЦ ФАЙЛОВ ПРОЕКТА ===

=== ЗАДАНИЕ ДЛЯ ТЕСТИРОВЩИКА ===
{clean_chief}

Твоя задача:
1. Напиши unit-тесты для проверки описанного выше функционала
2. Не смотри на существующий код - пиши тесты на основе ТОЛЬКО описания
3. Тесты должны проверять, что код работает так, как описано
4. Верни ТОЛЬКО файлы с тестами (каждый файл начинай с маркера [ФАЙЛ: имя_файла.py])

=== ФОРМАТ ОТВЕТА ===
[ФАЙЛ: test_название.py]
содержимое файла теста

[ФАЙЛ: test_другой.py]
содержимое другого файла

=== ИНСТРУКЦИЯ ===
Ты должен вернуть ТОЛЬКО файлы с тестами. Никаких лишних объяснений.
Каждый файл начинается с маркера [ФАЙЛ: имя_файла.py] и содержит код Python с pytest-тестами.
"""
        return message
    
    def parse_tester_files_response(self, tester_response: str) -> Dict[str, str]:
        """Парсит ответ Тестировщика и извлекает файлы с тестами"""
        files = {}
        
        import re
        # Ищем блоки [ФАЙЛ: имя_файла.py] ... (до следующего [ФАЙЛ: или конца)
        pattern = r'\[ФАЙЛ:\s*([^\]]+)\]\s*\n(.*?)(?=\n\[ФАЙЛ:|\Z)'
        
        matches = re.findall(pattern, tester_response, re.DOTALL)
        
        for filename, content in matches:
            filename = filename.strip()
            content = content.strip()
            if filename.endswith('.py'):
                files[filename] = content
                self.log(f"Извлечён файл теста: {filename} ({len(content)} символов)", "info")
        
        return files
    
    def run_pytest_in_venv(self, tests_folder: str = None) -> Dict[str, any]:
        """
        Запускает pytest в виртуальном окружении, которое находится в папке unit_tests/venv
        """
        if tests_folder is None:
            tests_folder = self.tests_folder
        
        # Ищем venv в папке unit_tests
        venv_python = None
        possible_venv_paths = [
            os.path.join(tests_folder, "venv", "bin", "python"),
            os.path.join(tests_folder, "venv", "Scripts", "python.exe"),  # Windows
            os.path.join(self.tests_folder, "venv", "bin", "python"),
        ]
        
        for path in possible_venv_paths:
            if os.path.exists(path):
                venv_python = path
                break
        
        # Если venv не найден, используем системный python
        if venv_python is None:
            venv_python = sys.executable
            self.log("Виртуальное окружение не найдено, используется системный Python", "warning")
        else:
            self.log(f"Используется venv: {venv_python}", "info")
        
        # Проверяем, установлен ли pytest в venv
        try:
            check_result = subprocess.run(
                [venv_python, "-m", "pytest", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if check_result.returncode != 0:
                self.log("pytest не установлен в venv. Установите: pip install pytest", "error")
                return {
                    "passed": False,
                    "stdout": "",
                    "stderr": "pytest не установлен в виртуальном окружении",
                    "returncode": 1
                }
        except Exception as e:
            self.log(f"Ошибка проверки pytest: {str(e)}", "error")
        
        # Запускаем тесты
        self.log(f"Запуск pytest в папке: {tests_folder}", "info")
        
        try:
            result = subprocess.run(
                [venv_python, "-m", "pytest", tests_folder, "-v", "--tb=short", "--color=no"],
                capture_output=True,
                text=True,
                timeout=60  # таймаут 60 секунд
            )
            
            self.log(f"pytest завершён с кодом: {result.returncode}", "info")
            
            return {
                "passed": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            self.log("pytest превысил таймаут (60 секунд)", "error")
            return {
                "passed": False,
                "stdout": "",
                "stderr": "pytest превысил таймаут (60 секунд)",
                "returncode": -1
            }
        except Exception as e:
            self.log(f"Ошибка запуска pytest: {str(e)}", "error")
            return {
                "passed": False,
                "stdout": "",
                "stderr": str(e),
                "returncode": -1
            }
    
    def save_test_results(self, result: Dict[str, any]) -> str:
        """Сохраняет результаты тестов в папку output"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_path = os.path.join(self.output_folder, f"test_results_{timestamp}.json")
        
        with open(result_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        self.log(f"Сохранены результаты тестов: {result_path}", "success")
        return result_path
    
    def build_report_for_chief(self, test_result: Dict[str, any], tester_original_response: str) -> str:
        """Формирует докладную Тестировщика для Главного"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if test_result["passed"]:
            status = "✅ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО"
            emoji = "✅"
        else:
            status = "❌ ТЕСТЫ НЕ ПРОЙДЕНЫ"
            emoji = "❌"
        
        report = f"""=== ДОКЛАДНАЯ ТЕСТИРОВЩИКА ===
Время: {timestamp}
Статус: {status}

=== РЕЗУЛЬТАТЫ ТЕСТОВ ===
Всего тестов: (см. вывод)
Пройдено: (см. вывод)
Упало: (см. вывод)

=== ПОЛНЫЙ ВЫВОД PYTEST ===
{test_result['stdout']}

=== ОШИБКИ (stderr) ===
{test_result['stderr']}

=== ИСХОДНЫЙ ОТВЕТ ТЕСТИРОВЩИКА ===
{tester_original_response[:2000]}{"..." if len(tester_original_response) > 2000 else ""}

=== ЗАКЛЮЧЕНИЕ ===
{emoji} Тестировщик {'одобряет' if test_result['passed'] else 'НЕ одобряет'} код к выпуску.

=== СТАТУС ===
{'TESTS_PASSED' if test_result['passed'] else 'TESTS_FAILED'}
"""
        return report
