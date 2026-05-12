# файл: aic/handlers/stage_handler.py
import os
import time
import random
import shutil
import re
from datetime import datetime
from typing import Optional, Callable, Union, List, Dict
import subprocess
import json

from aic.core.file_search import FileSearch
from aic.handlers.token_parser import TokenParser
from aic.utils.file_utils import FileUtils
from aic.utils.text_utils import TextUtils


class StageHandler:
    """Обработчик этапов диалога (этапы 1-12)"""
    
    STANDARD_FILES_PATH = "/home/lenovo/Documents/standard"
    
    def __init__(self, browser_manager, message_handler, timer, config, log_callback: Callable):
        self.browser_manager = browser_manager
        self.message_handler = message_handler
        self.timer = timer
        self.config = config
        self.log = log_callback
        self.file_search = FileSearch(log_callback)
        
        self.boss_window_index = None
        self.analyst_window_index = None
        self.chief_window_index = None
        self.developer_window_index = None
        self.tester_window_index = None
        
        self.output_folder = "output"
        FileUtils.ensure_folder(self.output_folder)
        
        self.copy_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), "copy")
        os.makedirs(self.copy_folder, exist_ok=True)
        
        self.tests_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), "testers", "unit_tests")
        os.makedirs(self.tests_folder, exist_ok=True)
        
        self.completed_stages = 0
        
        if self.message_handler:
            self.message_handler.set_timer(timer)
    
    def _send_stage_update(self, stage_num: int, stage_name: str):
        self.log(f"=== ЭТАП {stage_num}: {stage_name} ===", "info")
    
    def _save_to_output(self, content: str, filename_prefix: str, extension: str = "md") -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{timestamp}.{extension}"
        filepath = os.path.join(self.output_folder, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            self.log(f"Сохранён файл: {filepath}", "success")
            return filepath
        except Exception as e:
            self.log(f"Ошибка сохранения файла {filename}: {str(e)}", "error")
            return None
    
    def _extract_code_block(self, response: str) -> str:
        code_token = "=== КОД ==="
        if code_token not in response:
            return ""
        
        start_idx = response.find(code_token) + len(code_token)
        next_token = "=== СТАТУС ==="
        end_idx = response.find(next_token, start_idx)
        
        if end_idx == -1:
            return response[start_idx:].strip()
        return response[start_idx:end_idx].strip()
    
    def _extract_old_files(self, response: str) -> str:
        old_files_token = "=== СТАРЫЕ ФАЙЛЫ ==="
        if old_files_token not in response:
            return ""
        
        start_idx = response.find(old_files_token) + len(old_files_token)
        next_token = "=== СТАТУС ==="
        end_idx = response.find(next_token, start_idx)
        
        if end_idx == -1:
            return response[start_idx:].strip()
        return response[start_idx:end_idx].strip()
    
    def _ensure_minimum_windows(self, required: int = 5) -> bool:
        if not self.browser_manager or not self.browser_manager.is_connected:
            self.log("Нет подключения к браузеру", "error")
            return False
        
        window_count = self.browser_manager.windows_count
        if window_count < required:
            self.log(f"ОШИБКА: Требуется минимум {required} окна, доступно {window_count}", "error")
            return False
        
        return True
    
    def _read_prompt_file(self, filename: str) -> str:
        prompts_folder = self.config.prompts_folder
        file_path = os.path.join(prompts_folder, filename)
        content = FileUtils.read_file(file_path)
        if not content or content.startswith("[Ошибка"):
            return f"[Файл {filename} не найден]"
        return content
    
    def _read_project_file(self, filename: str) -> Optional[str]:
        if not self.config.project_folder:
            return None
        file_path = os.path.join(self.config.project_folder, filename)
        content = FileUtils.read_file(file_path)
        return content if content and not content.startswith("[Ошибка") else None
    
    def _read_standard_file(self, filename: str) -> Optional[str]:
        file_path = os.path.join(self.STANDARD_FILES_PATH, filename)
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                self.log(f"Ошибка чтения стандартного файла {filename}: {str(e)}", "error")
                return None
        return None
    
    def _get_project_files_content(self) -> str:
        if not self.config.project_folder:
            return ""
        parts = []
        for filename in ["CHANGELOG.md", "PROJECT_STRUCTURE.md"]:
            content = self._read_project_file(filename)
            if content:
                parts.append(f"\n[ФАЙЛ {filename}]:\n{content}")
        return "\n".join(parts)
    
    def _get_all_project_files_content(self) -> str:
        if not self.config.project_folder:
            return ""
        parts = []
        files_to_check = ["CHANGELOG.md", "PROJECT_STRUCTURE.md", "README.md", "FAQ.md", "ROADMAP.md"]
        for filename in files_to_check:
            content = self._read_project_file(filename)
            if content:
                parts.append(f"\n[ФАЙЛ {filename}]:\n{content}")
        return "\n".join(parts)
    
    def _get_standard_files_content(self) -> str:
        parts = []
        standard_files = ["CHANGELOG.md", "FAQ.md", "README.md", "ROADMAP.md"]
        
        for filename in standard_files:
            content = self._read_standard_file(filename)
            if content:
                parts.append(f"\n[СТАНДАРТНЫЙ ФАЙЛ {filename}]:\n{content}")
            else:
                self.log(f"Стандартный файл {filename} не найден в {self.STANDARD_FILES_PATH}", "warning")
        
        return "\n".join(parts)
    
    def _send_and_wait(self, message: str, target_name: str, custom_wait: int = None) -> Optional[str]:
        last_id = self.message_handler.get_last_assistant_message_id()
        wait_time = custom_wait if custom_wait else random.randint(self.config.min_wait_time, self.config.max_wait_time)
        
        if not self.message_handler.send_message(message):
            self.log(f"Ошибка отправки сообщения {target_name}", "error")
            return None
        
        self.timer.wait_with_countdown(wait_time)
        response = self.message_handler.wait_for_new_assistant_message(last_id, wait_time)
        
        if not response:
            self.log(f"Ответ от {target_name} не получен", "error")
            return None
        
        return response
    
    # ========== МЕТОДЫ ДЛЯ РАБОТЫ С ФАЙЛАМИ ==========
    
    def _create_file_backup(self, filepath: str) -> str:
        if not os.path.exists(filepath):
            self.log(f"Файл {filepath} не существует", "warning")
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        relative_path = os.path.relpath(filepath, start=os.path.dirname(os.path.dirname(__file__)))
        safe_name = relative_path.replace(os.sep, "_")
        backup_name = f"{safe_name}_backup_{timestamp}"
        backup_path = os.path.join(self.copy_folder, backup_name)
        
        shutil.copy2(filepath, backup_path)
        self.log(f"Создана резервная копия: {backup_path}", "success")
        return backup_path
    
    def _create_tests_backup(self, files_to_backup: List[str] = None) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = os.path.join(self.copy_folder, f"unit_tests_backup_{timestamp}")
        os.makedirs(backup_dir, exist_ok=True)
        
        if files_to_backup is None:
            if os.path.exists(self.tests_folder):
                for filename in os.listdir(self.tests_folder):
                    if filename.endswith('.py'):
                        src = os.path.join(self.tests_folder, filename)
                        dst = os.path.join(backup_dir, filename)
                        shutil.copy2(src, dst)
        else:
            for filename in files_to_backup:
                src = os.path.join(self.tests_folder, filename)
                if os.path.exists(src):
                    dst = os.path.join(backup_dir, filename)
                    shutil.copy2(src, dst)
        
        return backup_dir
    
    def _parse_developer_code(self, developer_response: str) -> Dict[str, str]:
        files = {}
        code_pattern = r'=== КОД ===\s*\n```(\w+)\s*\n(.*?)\n```'
        matches = re.findall(code_pattern, developer_response, re.DOTALL)
        
        for lang, code_block in matches:
            file_pattern = r'# файл:\s*([^\n]+)'
            file_match = re.search(file_pattern, code_block)
            
            if file_match:
                filename = file_match.group(1).strip()
                code_without_file_marker = re.sub(r'# файл:\s*[^\n]+\n?', '', code_block, count=1)
                files[filename] = code_without_file_marker.strip()
        
        return files
    
    def _save_developer_code_to_output(self, developer_response: str, files: Dict[str, str]) -> None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        response_path = os.path.join(self.output_folder, f"developer_response_{timestamp}.md")
        with open(response_path, 'w', encoding='utf-8') as f:
            f.write(developer_response)
        
        for filename, content in files.items():
            safe_name = filename.replace(os.sep, "_")
            file_path = os.path.join(self.output_folder, f"developer_{timestamp}_{safe_name}")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
    
    def _apply_developer_code_to_project(self, files: Dict[str, str]) -> bool:
        project_root = self.config.project_folder
        if not project_root:
            return False
        
        success_count = 0
        for filename, content in files.items():
            filepath = os.path.join(project_root, filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            if os.path.exists(filepath):
                backup_path = self._create_file_backup(filepath)
                if backup_path:
                    self._save_to_output(backup_path, f"backup_{filename.replace(os.sep, '_')}", "txt")
            
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                success_count += 1
            except Exception as e:
                self.log(f"Ошибка записи {filepath}: {str(e)}", "error")
        
        return success_count == len(files)
    
    def _parse_tester_files(self, tester_response: str) -> Dict[str, str]:
        files = {}
        pattern = r'\[ФАЙЛ:\s*([^\]]+)\]\s*\n(.*?)(?=\n\[ФАЙЛ:|\Z)'
        matches = re.findall(pattern, tester_response, re.DOTALL)
        
        for filename, content in matches:
            filename = filename.strip()
            content = content.strip()
            if filename.endswith('.py'):
                files[filename] = content
                self.log(f"Извлечён файл теста: {filename}", "info")
        
        return files
    
    def _replace_test_files(self, new_files: Dict[str, str]) -> bool:
        try:
            for filename, content in new_files.items():
                if filename.endswith('.py'):
                    filepath = os.path.join(self.tests_folder, filename)
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
            return True
        except Exception as e:
            self.log(f"Ошибка замены тестов: {str(e)}", "error")
            return False
    
    def _get_venv_python(self) -> Optional[str]:
        possible_paths = [
            os.path.join(self.tests_folder, "venv", "bin", "python"),
            os.path.join(self.tests_folder, "venv", "Scripts", "python.exe"),
            os.path.join(self.tests_folder, "venv", "bin", "python3"),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        return None
    
    def _install_package_in_venv(self, venv_python: str, package_name: str) -> bool:
        self.log(f"Установка пакета {package_name} в venv...", "info")
        
        try:
            result = subprocess.run(
                [venv_python, "-m", "pip", "install", package_name],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                self.log(f"Пакет {package_name} установлен", "success")
                return True
            else:
                self.log(f"Ошибка установки {package_name}: {result.stderr}", "error")
                return False
        except Exception as e:
            self.log(f"Ошибка: {str(e)}", "error")
            return False
    
    def _run_pytest_with_auto_install(self, venv_python: str, max_attempts: int = 3) -> Dict[str, any]:
        for attempt in range(max_attempts):
            self.log(f"Запуск pytest (попытка {attempt + 1})...", "info")
            
            try:
                result = subprocess.run(
                    [venv_python, "-m", "pytest", self.tests_folder, "-v", "--tb=short", "--color=no"],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if result.returncode == 0 or "ModuleNotFoundError" not in result.stderr:
                    return {
                        "passed": result.returncode == 0,
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "returncode": result.returncode
                    }
                
                import_match = re.search(r"ModuleNotFoundError: No module named '([^']+)'", result.stderr)
                
                if import_match:
                    missing_module = import_match.group(1)
                    if self._install_package_in_venv(venv_python, missing_module):
                        continue
                    else:
                        return {
                            "passed": False,
                            "stdout": result.stdout,
                            "stderr": f"Не удалось установить {missing_module}",
                            "returncode": result.returncode
                        }
                else:
                    return {
                        "passed": False,
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "returncode": result.returncode
                    }
            except subprocess.TimeoutExpired:
                return {
                    "passed": False,
                    "stdout": "",
                    "stderr": "pytest timeout",
                    "returncode": -1
                }
            except Exception as e:
                return {
                    "passed": False,
                    "stdout": "",
                    "stderr": str(e),
                    "returncode": -1
                }
        
        return {
            "passed": False,
            "stdout": "",
            "stderr": "Превышено количество попыток",
            "returncode": -1
        }
    
    def _build_message_for_tester(self, chief_response: str, files_to_send: List[str]) -> str:
        prompts_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts")
        tester_prompt_path = os.path.join(prompts_folder, "Tester.txt")
        
        tester_prompt = ""
        if os.path.exists(tester_prompt_path):
            with open(tester_prompt_path, 'r', encoding='utf-8') as f:
                tester_prompt = f.read()
        else:
            tester_prompt = "Ты - Тестировщик. Напиши unit-тесты на основе описания функционала."
        
        files_list = "\n".join(files_to_send)
        
        clean_chief = chief_response
        if "=== ФАЙЛЫ ПРОЕКТА ===" in clean_chief:
            clean_chief = re.sub(r'=== ФАЙЛЫ ПРОЕКТА ===.*?=== КОНЕЦ ФАЙЛОВ ПРОЕКТА ===', '', clean_chief, flags=re.DOTALL)
        
        return f"""{tester_prompt}

=== ФАЙЛЫ ПРОЕКТА ===
{files_list}
=== КОНЕЦ ФАЙЛОВ ПРОЕКТА ===

=== ЗАДАНИЕ ДЛЯ ТЕСТИРОВЩИКА ===
{clean_chief}

=== ФОРМАТ ОТВЕТА ===
[ФАЙЛ: test_название.py]
содержимое файла теста
"""
    
    def _save_tester_files_to_output(self, tester_response: str, new_files: Dict[str, str]):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for filename, content in new_files.items():
            output_path = os.path.join(self.output_folder, f"tester_{timestamp}_{filename}")
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        response_path = os.path.join(self.output_folder, f"tester_response_{timestamp}.md")
        with open(response_path, 'w', encoding='utf-8') as f:
            f.write(tester_response)
    
    def _build_tester_report(self, test_result: Dict[str, any], tester_response: str) -> str:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status = "✅ ТЕСТЫ ПРОЙДЕНЫ" if test_result["passed"] else "❌ ТЕСТЫ НЕ ПРОЙДЕНЫ"
        
        return f"""=== ДОКЛАДНАЯ ТЕСТИРОВЩИКА ===
Время: {timestamp}
Статус: {status}

=== ВЫВОД PYTEST ===
{test_result['stdout']}

=== ОШИБКИ ===
{test_result['stderr']}

=== СТАТУС ===
{'TESTS_PASSED' if test_result['passed'] else 'TESTS_FAILED'}
"""
    
    # ========== ЭТАП 1: ПОЛЬЗОВАТЕЛЬ -> НАЧАЛЬНИК (ЦИКЛ) ==========
    def execute_stage1_user_to_boss(self, user_message: str) -> Union[str, dict, None]:
        """Этап 1: Пользователь отправляет задачу Начальнику с циклом на уточнение"""
        self._send_stage_update(1, "пользователь -> начальник")
        if not self._ensure_minimum_windows(5):
            return None
        
        self.boss_window_index = 0
        self.browser_manager.switch_to_window(self.boss_window_index)
        
        current_message = user_message
        
        while True:
            boss_prompt = self._read_prompt_file("Boss.txt")
            parts = [boss_prompt]
            if current_message:
                parts.append(f"\n[СООБЩЕНИЕ ПОЛЬЗОВАТЕЛЯ]:\n{current_message}")
            project_files = self._get_project_files_content()
            if project_files:
                parts.append(project_files)
            
            message = TextUtils.remove_emojis("\n\n".join(parts))
            
            response = self._send_and_wait(message, "начальника")
            if not response:
                return None
            
            token = TokenParser.parse_boss_token(response)
            clean_response = TokenParser.remove_boss_token(response)
            
            self.log(f"Ответ начальника (токен: {token})", "info")
            
            if token == "WAITING_USER":
                self.log("Начальник запросил уточнение у пользователя", "warning")
                # TODO: ожидание ввода пользователя
                return {"type": "need_clarification", "message": clean_response}
            elif token == "SENT_TO_USER":
                return {"type": "sent_to_user", "message": clean_response}
            elif token == "NEEDS_REVISION":
                return {"type": "needs_revision", "message": clean_response}
            elif token == "WAITING_ANALYST":
                return clean_response
            elif token == "WAITING_CHIEF":
                return clean_response
            elif token == "NEEDS_FULL_CYCLE":
                return {"type": "need_full_cycle", "message": clean_response}
            else:
                self.log(f"Неизвестный токен: {token}", "warning")
                self.message_handler.send_message("НЕИЗВЕСНЫЙ СТАТУС! ПОДТВЕРДИТЕ СТАТУС")
                return None
    
    # ========== ЭТАП 2: НАЧАЛЬНИК -> АНАЛИТИК (ЦИКЛ) ==========
    def execute_stage2_boss_to_analyst(self, boss_response: str) -> Union[str, dict, None]:
        """Этап 2: Начальник отправляет ТЗ Аналитику"""
        self._send_stage_update(2, "начальник -> аналитик")
        
        self.analyst_window_index = 1
        self.browser_manager.switch_to_window(self.analyst_window_index)
        
        time.sleep(2)
        self.browser_manager.ensure_empty_chat()
        
        if not self.browser_manager.is_input_available():
            self.log("Поле ввода недоступно", "error")
            return None
        
        analyst_prompt = self._read_prompt_file("Analyst.txt")
        parts = [analyst_prompt]
        parts.append(f"\n[ТЗ ОТ НАЧАЛЬНИКА]:\n{boss_response}")
        all_files = self._get_all_project_files_content()
        if all_files:
            parts.append(all_files)
        
        message = TextUtils.remove_emojis("\n\n".join(parts))
        
        response = self._send_and_wait(message, "аналитика")
        if not response:
            return None
        
        token = TokenParser.parse_analyst_token(response)
        clean_response = TokenParser.remove_analyst_token(response)
        
        self.log(f"Ответ аналитика (токен: {token})", "info")
        
        if token == "SENT_TO_BOSS":
            return clean_response
        elif token == "SENT_TO_CHIEF":
            return {"type": "to_chief_direct", "message": clean_response}
        else:
            self.log(f"Неизвестный токен аналитика: {token}", "warning")
            return None
    
    # ========== ЭТАП 3: АНАЛИТИК -> НАЧАЛЬНИК (ЦИКЛ С РЕКУРСИЕЙ) ==========
    def execute_stage3_analyst_to_boss(self, analyst_response: str) -> Union[str, dict, None]:
        """Этап 3: Аналитик отправляет уточнённое ТЗ Начальнику с циклом доработки"""
        self._send_stage_update(3, "аналитик -> начальник")
        
        self.browser_manager.switch_to_window(self.boss_window_index)
        time.sleep(2)
        self.browser_manager.ensure_empty_chat()
        
        if not self.browser_manager.is_input_available():
            self.log("Поле ввода недоступно", "error")
            return None
        
        boss_prompt = self._read_prompt_file("Boss.txt")
        parts = [boss_prompt]
        parts.append(f"\n[УТОЧНЁННОЕ ТЗ ОТ АНАЛИТИКА]:\n{analyst_response}")
        project_files = self._get_project_files_content()
        if project_files:
            parts.append(project_files)
        
        message = TextUtils.remove_emojis("\n\n".join(parts))
        
        response = self._send_and_wait(message, "начальника")
        if not response:
            return None
        
        token = TokenParser.parse_boss_token(response)
        clean_response = TokenParser.remove_boss_token(response)
        
        self.log(f"Ответ начальника (токен: {token})", "info")
        
        # Цикл: если начальник снова отправил WAITING_ANALYST, повторяем этап 2
        if token == "WAITING_ANALYST":
            self.log("Начальник требует повторной доработки аналитиком", "warning")
            
            # Отправляем аналитику замечания
            self.browser_manager.switch_to_window(self.analyst_window_index)
            time.sleep(2)
            self.browser_manager.ensure_empty_chat()
            
            revision_msg = f"Начальник требует доработки:\n{clean_response}"
            new_analyst = self._send_and_wait(revision_msg, "аналитика")
            if not new_analyst:
                return None
            
            new_token = TokenParser.parse_analyst_token(new_analyst)
            new_clean = TokenParser.remove_analyst_token(new_analyst)
            
            if new_token == "SENT_TO_CHIEF":
                return {"type": "to_chief_direct", "message": new_clean}
            elif new_token == "SENT_TO_BOSS":
                # Рекурсивно возвращаемся к начальнику с новым ТЗ
                return self.execute_stage3_analyst_to_boss(new_clean)
            else:
                return new_clean
        
        # Цикл: если начальник требует доработки (NEEDS_REVISION)
        attempt = 0
        while token == "NEEDS_REVISION":
            attempt += 1
            self.log(f"Начальник требует доработки (попытка {attempt})", "warning")
            
            self.browser_manager.switch_to_window(self.analyst_window_index)
            time.sleep(2)
            self.browser_manager.ensure_empty_chat()
            
            revision_msg = f"Начальник требует доработки:\n{clean_response}"
            new_analyst = self._send_and_wait(revision_msg, "аналитика")
            
            if not new_analyst:
                return None
            
            new_token = TokenParser.parse_analyst_token(new_analyst)
            new_clean = TokenParser.remove_analyst_token(new_analyst)
            
            if new_token == "SENT_TO_CHIEF":
                return {"type": "to_chief_direct", "message": new_clean}
            
            self.browser_manager.switch_to_window(self.boss_window_index)
            time.sleep(2)
            self.browser_manager.ensure_empty_chat()
            
            boss_prompt = self._read_prompt_file("Boss.txt")
            parts = [boss_prompt]
            parts.append(f"\n[УТОЧНЁННОЕ ТЗ ОТ АНАЛИТИКА]:\n{new_clean}")
            if project_files:
                parts.append(project_files)
            
            message = TextUtils.remove_emojis("\n\n".join(parts))
            response = self._send_and_wait(message, "начальника")
            
            if not response:
                return None
            
            token = TokenParser.parse_boss_token(response)
            clean_response = TokenParser.remove_boss_token(response)
            self.log(f"Новый ответ начальника (токен: {token})", "info")
        
        if token == "WAITING_CHIEF":
            return clean_response
        elif token == "WAITING_ANALYST":
            return clean_response
        elif token == "NEEDS_FULL_CYCLE":
            return {"type": "need_full_cycle", "message": clean_response}
        elif token == "WAITING_USER":
            return {"type": "need_clarification", "message": clean_response}
        else:
            self.log(f"Не удалось получить одобрение. Токен: {token}", "error")
            return None
    
    # ========== ЭТАП 4: НАЧАЛЬНИК -> ГЛАВНЫЙ (ЦИКЛ) ==========
    def execute_stage4_boss_to_chief(self, final_tz: str) -> Optional[str]:
        """Этап 4: Начальник отправляет финальное ТЗ Главному с циклом на NEEDS_TZ_REVISION"""
        self._send_stage_update(4, "начальник -> главный разработчик")
        
        chief_path = os.path.join(self.config.prompts_folder, "Chief_developer.txt")
        if not os.path.exists(chief_path):
            self.log("Файл Chief_developer.txt не найден", "error")
            return None
        
        self.chief_window_index = 2
        self.browser_manager.switch_to_window(self.chief_window_index)
        
        time.sleep(2)
        self.browser_manager.ensure_empty_chat()
        
        if not self.browser_manager.is_input_available():
            self.log("Поле ввода недоступно", "error")
            return None
        
        current_tz = final_tz
        attempt = 0
        
        while True:
            attempt += 1
            if attempt > 1:
                self.log(f"Повторная отправка ТЗ главному (попытка {attempt})", "info")
            
            chief_prompt = self._read_prompt_file("Chief_developer.txt")
            parts = [chief_prompt]
            parts.append(f"\n[ФИНАЛЬНОЕ ТЗ ОТ НАЧАЛЬНИКА]:\n{current_tz}")
            project_files = self._get_project_files_content()
            if project_files:
                parts.append(project_files)
            
            message = TextUtils.remove_emojis("\n\n".join(parts))
            
            response = self._send_and_wait(message, "главного разработчика")
            if not response:
                return None
            
            token = TokenParser.parse_chief_token(response)
            clean_response = TokenParser.remove_chief_token(response)
            
            self.log(f"Ответ главного (токен: {token})", "info")
            
            if token == "NEEDS_TZ_REVISION":
                self.log("Главный требует доработки ТЗ, возврат к начальнику", "warning")
                # Отправляем замечания начальнику
                self.browser_manager.switch_to_window(self.boss_window_index)
                time.sleep(2)
                self.browser_manager.ensure_empty_chat()
                
                revision_msg = f"Главный требует доработки ТЗ:\n{clean_response}"
                boss_response = self._send_and_wait(revision_msg, "начальника")
                if not boss_response:
                    return None
                
                boss_token = TokenParser.parse_boss_token(boss_response)
                current_tz = TokenParser.remove_boss_token(boss_response)
                
                if boss_token == "WAITING_CHIEF":
                    continue  # Повторяем цикл с новым ТЗ
                else:
                    self.log(f"Начальник не отправил ТЗ главному, токен: {boss_token}", "error")
                    return None
            else:
                return response
    
    # ========== ЭТАП 5: ГЛАВНЫЙ -> РЯДОВОЙ ==========
    def execute_stage5_chief_to_developer(self, chief_response: str, files_to_send: list, revision_feedback: str = "") -> Optional[str]:
        self._send_stage_update(5, "главный -> разработчик")
        
        self.developer_window_index = 3
        self.browser_manager.switch_to_window(self.developer_window_index)
        
        time.sleep(2)
        self.browser_manager.ensure_empty_chat()
        
        if not self.browser_manager.is_input_available():
            self.log("Поле ввода недоступно", "error")
            return None
        
        found_files = self._find_files_with_paths(self.config.project_folder, files_to_send)
        
        token_files = "=== ФАЙЛЫ ПРОЕКТА ===\n"
        for requested_path, actual_path in found_files.items():
            token_files += f"{requested_path}\n"
        
        parts = []
        ordinary_prompt = self._read_prompt_file("Ordinary_developer.txt")
        if ordinary_prompt and not ordinary_prompt.startswith("[Файл"):
            parts.append(ordinary_prompt)
        else:
            parts.append("[РОЛЕВОЙ ПРОМТ: РЯДОВОЙ РАЗРАБОТЧИК]")
        
        if revision_feedback:
            parts.append(f"\n[ЗАМЕЧАНИЯ НА ДОРАБОТКУ]:\n{revision_feedback}")
        else:
            parts.append(f"\n[ЗАПРОС ОТ ГЛАВНОГО]:\n{chief_response}")
        
        parts.append(f"\n{token_files}")
        
        for requested_path, actual_path in found_files.items():
            content = self.file_search.read_file_content(actual_path)
            if content:
                parts.append(f"\n[СОДЕРЖИМОЕ {requested_path}]:\n```\n{content}\n```")
        
        message = TextUtils.remove_emojis("\n\n".join(parts))
        
        response = self._send_and_wait(message, "рядового разработчика")
        return response
    
    # ========== ЭТАП 6: РЯДОВОЙ -> ГЛАВНЫЙ ==========
    def execute_stage6_developer_to_chief(self, developer_response: str) -> Optional[str]:
        self._send_stage_update(6, "разработчик -> главный")
        
        developer_files = self._parse_developer_code(developer_response)
        
        if developer_files:
            self._save_developer_code_to_output(developer_response, developer_files)
            self._apply_developer_code_to_project(developer_files)
            self.log(f"Применено {len(developer_files)} файлов", "success")
        
        self.browser_manager.switch_to_window(self.chief_window_index)
        
        time.sleep(2)
        self.browser_manager.ensure_empty_chat()
        
        if not self.browser_manager.is_input_available():
            self.log("Поле ввода недоступно", "error")
            return None
        
        chief_prompt = self._read_prompt_file("Chief_developer.txt")
        parts = [chief_prompt]
        parts.append("\n[ОТВЕТ ОТ РАЗРАБОТЧИКА]:")
        parts.append(developer_response)
        
        project_files = self._get_project_files_content()
        if project_files:
            parts.append(project_files)
        
        message = TextUtils.remove_emojis("\n\n".join(parts))
        
        response = self._send_and_wait(message, "главного разработчика")
        return response
    
    # ========== ЭТАП 7: ГЛАВНЫЙ -> ТЕСТИРОВЩИК ==========
    def execute_stage7_chief_to_tester(self, chief_response: str, files_to_send: List[str]) -> Optional[str]:
        self._send_stage_update(7, "главный -> тестировщик")
        
        if self.tester_window_index is None:
            self.tester_window_index = 4
        
        self.browser_manager.switch_to_window(self.tester_window_index)
        time.sleep(2)
        self.browser_manager.ensure_empty_chat()
        
        if not self.browser_manager.is_input_available():
            self.log("Поле ввода недоступно", "error")
            return None
        
        if files_to_send:
            self._create_tests_backup(files_to_send)
        
        message = self._build_message_for_tester(chief_response, files_to_send)
        
        response = self._send_and_wait(message, "тестировщика")
        return response
    
    # ========== ЭТАП 8: ТЕСТИРОВЩИК -> ГЛАВНЫЙ (ЦИКЛ) ==========
    def execute_stage8_tester_to_chief(self, tester_response: str) -> Dict[str, any]:
        self._send_stage_update(8, "тестировщик -> главный")
        
        new_test_files = self._parse_tester_files(tester_response)
        
        if not new_test_files:
            return {
                "passed": False,
                "error": "Нет файлов тестов",
                "report": "Тестировщик не вернул файлы"
            }
        
        self._save_tester_files_to_output(tester_response, new_test_files)
        
        success = self._replace_test_files(new_test_files)
        if not success:
            return {
                "passed": False,
                "error": "Ошибка замены тестов",
                "report": "Не удалось заменить тесты"
            }
        
        venv_python = self._get_venv_python()
        if venv_python is None:
            venv_python = sys.executable
        
        test_result = self._run_pytest_with_auto_install(venv_python)
        
        self._save_to_output(json.dumps(test_result, indent=2), "test_results", "json")
        
        report = self._build_tester_report(test_result, tester_response)
        self._save_to_output(report, "tester_report", "md")
        
        self.log(f"Тесты {'ПРОЙДЕНЫ' if test_result['passed'] else 'НЕ ПРОЙДЕНЫ'}")
        
        self.browser_manager.switch_to_window(self.chief_window_index)
        
        return {
            "passed": test_result["passed"],
            "stdout": test_result["stdout"],
            "stderr": test_result["stderr"],
            "report": report,
            "new_test_files": new_test_files
        }
    
    # ========== ЭТАП 9: ГЛАВНЫЙ -> АНАЛИТИК ==========
    def execute_stage9_chief_to_analyst(self, chief_response: str, developer_response: str, old_files_content: str = "") -> Optional[str]:
        self._send_stage_update(9, "главный -> аналитик (документация)")
        
        new_code = self._extract_code_block(developer_response)
        if not new_code:
            new_code = developer_response
        
        self.browser_manager.switch_to_window(self.analyst_window_index)
        
        time.sleep(2)
        self.browser_manager.ensure_empty_chat()
        
        if not self.browser_manager.is_input_available():
            self.log("Поле ввода недоступно", "error")
            return None
        
        analyst_prompt = self._read_prompt_file("Analyst.txt")
        parts = [analyst_prompt]
        
        parts.append("\n[ИНСТРУКЦИЯ]:")
        parts.append("Обнови README.md, CHANGELOG.md, FAQ.md")
        parts.append("PROJECT_STRUCTURE.md НЕ ТРОГАЙ")
        
        parts.append(f"\n=== НОВЫЙ КОД ===\n{new_code}")
        
        project_files = self._get_all_project_files_content()
        if project_files:
            parts.append(f"\n[ФАЙЛЫ ПРОЕКТА]:{project_files}")
        
        clean_chief = TokenParser.remove_chief_token(chief_response)
        parts.append(f"\n[ЗАПРОС ОТ ГЛАВНОГО]:\n{clean_chief}")
        
        message = TextUtils.remove_emojis("\n\n".join(parts))
        
        response = self._send_and_wait(message, "аналитика")
        return response
    
    # ========== ЭТАП 10: АНАЛИТИК -> ГЛАВНЫЙ ==========
    def execute_stage10_analyst_to_chief(self, analyst_response: str) -> Optional[str]:
        self._send_stage_update(10, "аналитик -> главный")
        
        self.browser_manager.switch_to_window(self.chief_window_index)
        
        time.sleep(2)
        self.browser_manager.ensure_empty_chat()
        
        if not self.browser_manager.is_input_available():
            self.log("Поле ввода недоступно", "error")
            return None
        
        token = TokenParser.parse_analyst_token(analyst_response)
        clean_analyst = TokenParser.remove_analyst_token(analyst_response)
        
        self.log(f"Ответ аналитика (токен: {token})", "info")
        
        self._save_to_output(clean_analyst, "documentation", "md")
        
        chief_prompt = self._read_prompt_file("Chief_developer.txt")
        parts = [chief_prompt]
        
        parts.append("\n[ДОКУМЕНТАЦИЯ ОТ АНАЛИТИКА]:")
        parts.append(clean_analyst)
        
        project_files = self._get_all_project_files_content()
        if project_files:
            parts.append(project_files)
        
        message = TextUtils.remove_emojis("\n\n".join(parts))
        
        response = self._send_and_wait(message, "главного разработчика")
        return response
    
    # ========== ЭТАП 11: ГЛАВНЫЙ -> НАЧАЛЬНИК ==========
    def execute_stage11_chief_to_boss(self, chief_response: str, analyst_response: str = "") -> Optional[str]:
        self._send_stage_update(11, "главный -> начальник (отчёт)")
        
        self.browser_manager.switch_to_window(self.boss_window_index)
        
        time.sleep(2)
        self.browser_manager.ensure_empty_chat()
        
        if not self.browser_manager.is_input_available():
            self.log("Поле ввода недоступно", "error")
            return None
        
        chief_token = TokenParser.parse_chief_token(chief_response)
        clean_chief = TokenParser.remove_chief_token(chief_response)
        
        self.log(f"Ответ главного (токен: {chief_token})", "info")
        
        boss_prompt = self._read_prompt_file("Boss.txt")
        parts = [boss_prompt]
        
        parts.append("\n[ОТЧЁТ ОТ ГЛАВНОГО]:")
        parts.append(clean_chief)
        
        if analyst_response:
            clean_analyst = TokenParser.remove_analyst_token(analyst_response)
            parts.append("\n[ДОКУМЕНТАЦИЯ ОТ АНАЛИТИКА]:")
            parts.append(clean_analyst)
        
        project_files = self._get_all_project_files_content()
        if project_files:
            parts.append(project_files)
        
        message = TextUtils.remove_emojis("\n\n".join(parts))
        
        response = self._send_and_wait(message, "начальника")
        return response
    
    # ========== ЭТАП 12: НАЧАЛЬНИК -> ПОЛЬЗОВАТЕЛЬ ==========
    def execute_stage12_boss_to_user(self, boss_response: str) -> Optional[str]:
        self._send_stage_update(12, "начальник -> пользователь")
        
        self.browser_manager.switch_to_window(self.boss_window_index)
        
        time.sleep(2)
        self.browser_manager.ensure_empty_chat()
        
        if not self.browser_manager.is_input_available():
            self.log("Поле ввода недоступно", "error")
            return None
        
        boss_token = TokenParser.parse_boss_token(boss_response)
        clean_boss = TokenParser.remove_boss_token(boss_response)
        
        self.log(f"Ответ начальника (токен: {boss_token})", "info")
        
        self._save_to_output(clean_boss, "final_report", "md")
        
        parts = []
        parts.append("[СООБЩЕНИЕ ОТ НАЧАЛЬНИКА]:")
        parts.append(clean_boss)
        parts.append("\n[ДОКЛАДНАЯ ЗАПИСКА]:")
        parts.append("Работа завершена.")
        
        message = TextUtils.remove_emojis("\n\n".join(parts))
        
        response = self._send_and_wait(message, "пользователя")
        return response
    
    # ========== ПОЛНЫЙ ПАЙПЛАЙН ==========
    def execute_full_pipeline(self, user_message: str, files_to_send: list = None) -> bool:
        self.completed_stages = 0
        
        self.boss_window_index = 0
        self.analyst_window_index = 1
        self.chief_window_index = 2
        self.developer_window_index = 3
        self.tester_window_index = 4
        
        # ========== ЭТАП 1 ==========
        result1 = self.execute_stage1_user_to_boss(user_message)
        if not result1:
            return False
        
        if isinstance(result1, dict):
            if result1.get("type") == "need_clarification":
                self.completed_stages = 1
                return True
            elif result1.get("type") == "need_full_cycle":
                return self.execute_full_pipeline(user_message, files_to_send)
            elif result1.get("type") == "needs_revision":
                self.completed_stages = 1
                return True
            else:
                return False
        
        boss_response = result1
        self.completed_stages = 1
        
        # ========== ЭТАП 2 ==========
        result2 = self.execute_stage2_boss_to_analyst(boss_response)
        if not result2:
            return False
        
        if isinstance(result2, dict) and result2.get("type") == "to_chief_direct":
            chief_response = result2["message"]
            skip_to_chief = True
        else:
            analyst_response = result2
            skip_to_chief = False
            self.completed_stages = 2
            
            # ========== ЭТАП 3 ==========
            result3 = self.execute_stage3_analyst_to_boss(analyst_response)
            if not result3:
                return False
            self.completed_stages = 3
            
            if isinstance(result3, dict):
                if result3.get("type") == "to_chief_direct":
                    chief_response = result3["message"]
                    skip_to_chief = True
                elif result3.get("type") == "need_clarification":
                    return True
                elif result3.get("type") == "need_full_cycle":
                    return self.execute_full_pipeline(user_message, files_to_send)
                else:
                    return False
            else:
                final_tz = result3
                # ========== ЭТАП 4 ==========
                chief_response = self.execute_stage4_boss_to_chief(final_tz)
                if not chief_response:
                    return False
                self.completed_stages = 4
                skip_to_chief = False
        
        # ========== ОБРАБОТКА ГЛАВНОГО ==========
        chief_token = TokenParser.parse_chief_token(chief_response)
        clean_chief = TokenParser.remove_chief_token(chief_response)
        
        self.log(f"Токен главного: {chief_token}", "info")
        
        if chief_token == "WAITING_CODE":
            files_to_find = TokenParser.parse_file_list_token(chief_response)
            if not files_to_find:
                files_to_find = files_to_send or ["main.py"]
            
            attempt = 0
            current_clean_chief = clean_chief
            developer_response_for_docs = None
            chief_response_for_docs = None
            
            while True:
                attempt += 1
                self.log(f"Генерация кода, попытка {attempt}", "info")
                
                revision_feedback = "" if attempt == 1 else f"Доработка: {current_clean_chief}"
                
                developer_response = self.execute_stage5_chief_to_developer(
                    current_clean_chief, files_to_find, revision_feedback
                )
                if not developer_response:
                    return False
                self.completed_stages = 5
                
                final_chief = self.execute_stage6_developer_to_chief(developer_response)
                if not final_chief:
                    return False
                self.completed_stages = 6
                
                final_token = TokenParser.parse_chief_token(final_chief)
                self.log(f"Токен после проверки: {final_token}", "info")
                
                if final_token == "WAITING_DOCS":
                    self._save_to_output(developer_response, "approved_code", "txt")
                    
                    files_to_test = [f for f in os.listdir(self.tests_folder) if f.endswith('.py') and f != '__init__.py']
                    
                    chief_with_description = f"""=== ФУНКЦИОНАЛ ===
{clean_chief}

=== ФАЙЛЫ ПРОЕКТА ===
{chr(10).join(files_to_test)}
=== КОНЕЦ ФАЙЛОВ ПРОЕКТА ===
"""
                    tester_response = self.execute_stage7_chief_to_tester(chief_with_description, files_to_test)
                    if not tester_response:
                        return False
                    self.completed_stages = 7
                    
                    test_result = self.execute_stage8_tester_to_chief(tester_response)
                    self.completed_stages = 8
                    
                    if not test_result["passed"]:
                        self.log("Тесты не пройдены, доработка", "error")
                        current_clean_chief = f"❌ ТЕСТЫ НЕ ПРОШЛИ!\n{test_result['report']}"
                        continue
                    
                    chief_response_for_docs = final_chief
                    developer_response_for_docs = developer_response
                    break
                    
                elif final_token == "NEEDS_CODE_REVISION":
                    self.log("Код требует доработки", "warning")
                    current_clean_chief = TokenParser.remove_chief_token(final_chief)
                    continue
                    
                elif final_token == "NEEDS_TZ_REVISION":
                    self.log("ТЗ требует доработки", "warning")
                    return False
                    
                elif final_token == "SENT_TO_BOSS":
                    boss_final = self.execute_stage11_chief_to_boss(final_chief)
                    if not boss_final:
                        return False
                    self.completed_stages = 11
                    
                    user_final = self.execute_stage12_boss_to_user(boss_final)
                    if user_final:
                        self.completed_stages = 12
                    return True
                    
                else:
                    return False
            
            if chief_response_for_docs and developer_response_for_docs:
                # Этап 9
                docs_response = self.execute_stage9_chief_to_analyst(chief_response_for_docs, developer_response_for_docs)
                if not docs_response:
                    return False
                self.completed_stages = 9
                
                analyst_token = TokenParser.parse_analyst_token(docs_response)
                
                if analyst_token == "SENT_TO_CHIEF":
                    # Этап 10
                    chief_after_docs = self.execute_stage10_analyst_to_chief(docs_response)
                    if not chief_after_docs:
                        return False
                    self.completed_stages = 10
                    
                    # Цикл доработки документации
                    docs_token = TokenParser.parse_chief_token(chief_after_docs)
                    docs_attempt = 0
                    
                    while docs_token == "NEEDS_DOCS_REVISION":
                        docs_attempt += 1
                        self.log(f"Документация требует доработки (попытка {docs_attempt})", "warning")
                        
                        revision_feedback = TokenParser.remove_chief_token(chief_after_docs)
                        revised_docs = self.execute_stage9_chief_to_analyst(
                            f"Доработайте:\n{revision_feedback}",
                            developer_response_for_docs
                        )
                        if not revised_docs:
                            return False
                        
                        chief_after_docs = self.execute_stage10_analyst_to_chief(revised_docs)
                        if not chief_after_docs:
                            return False
                        
                        docs_token = TokenParser.parse_chief_token(chief_after_docs)
                        
                        if docs_token == "WAITING_DOCS" or docs_token == "SENT_TO_BOSS":
                            break
                    
                    # Этап 11
                    boss_final = self.execute_stage11_chief_to_boss(chief_after_docs, docs_response)
                    if not boss_final:
                        return False
                    self.completed_stages = 11
                    
                    # Этап 12
                    user_final = self.execute_stage12_boss_to_user(boss_final)
                    if user_final:
                        self.completed_stages = 12
                        self.log("=== ДОКЛАДНАЯ ОТПРАВЛЕНА ===", "success")
                    return True
                    
                elif analyst_token == "SENT_TO_BOSS":
                    boss_final = self.execute_stage11_chief_to_boss("", docs_response)
                    if not boss_final:
                        return False
                    self.completed_stages = 11
                    
                    user_final = self.execute_stage12_boss_to_user(boss_final)
                    if user_final:
                        self.completed_stages = 12
                    return True
                    
        elif chief_token == "WAITING_UNIT_TESTS":
            self.log("Главный отправил задание тестировщику", "info")
            
            # Получаем список файлов для отправки тестировщику
            files_to_test = []
            if os.path.exists(self.tests_folder):
                files_to_test = [f for f in os.listdir(self.tests_folder) if f.endswith('.py') and f != '__init__.py']
            
            # Этап 7
            tester_response = self.execute_stage7_chief_to_tester(clean_chief, files_to_test)
            if not tester_response:
                return False
            self.completed_stages = 7
            
            # Этап 8
            test_result = self.execute_stage8_tester_to_chief(tester_response)
            self.completed_stages = 8
            
            if not test_result["passed"]:
                self.log("Тесты не пройдены, возврат к разработчику", "error")
                # Возвращаемся к этапу 5
                current_clean_chief = f"❌ ТЕСТЫ НЕ ПРОШЛИ!\n{test_result['report']}"
                # Нужно продолжить цикл, но для этого нужно переписать логику
                # Пока просто выходим с ошибкой
                return False
            
            # Если тесты пройдены, продолжаем к документации
            chief_response_for_docs = chief_response
            developer_response_for_docs = developer_response  # нужно сохранить предыдущий ответ разработчика
        
        elif chief_token == "SENT_TO_BOSS":
            boss_final = self.execute_stage11_chief_to_boss(chief_response)
            if not boss_final:
                return False
            self.completed_stages = 11
            
            user_final = self.execute_stage12_boss_to_user(boss_final)
            if user_final:
                self.completed_stages = 12
            return True
        
        else:
            self.log(f"Неизвестный токен: {chief_token}", "error")
            return False
        
        self.log(f"ВЫПОЛНЕНО {self.completed_stages} ИЗ 12 ЭТАПОВ", "success")
        return True
        
    def _find_files_with_paths(self, project_root: str, filenames: List[str]) -> Dict[str, str]:
        """Поиск файлов с поддержкой путей (например tests/test_calculator.py)"""
        found = {}
        
        for filename in filenames:
            # Прямой путь
            direct_path = os.path.join(project_root, filename)
            if os.path.exists(direct_path):
                found[filename] = direct_path
                continue
            
            # Поиск по имени файла (без учёта пути)
            basename = os.path.basename(filename)
            for root, dirs, files in os.walk(project_root):
                if basename in files:
                    full_path = os.path.join(root, basename)
                    found[filename] = full_path
                    break
        
        return found
