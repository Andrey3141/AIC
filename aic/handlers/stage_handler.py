# файл: aic/handlers/stage_handler.py
import os
import time
import random
from datetime import datetime
from typing import Optional, Callable, Union, List, Dict

from aic.core.file_search import FileSearch
from aic.handlers.token_parser import TokenParser
from aic.utils.file_utils import FileUtils
from aic.utils.text_utils import TextUtils

class StageHandler:
    """Обработчик этапов диалога"""
    
    # Путь к папке со стандартными файлами
    STANDARD_FILES_PATH = "/home/lenovo/Documents/standard"
    
    def __init__(self, browser_manager, message_handler, timer, config, log_callback: Callable):
        self.browser_manager = browser_manager
        self.message_handler = message_handler
        self.timer = timer
        self.config = config
        self.log = log_callback
        self.file_search = FileSearch(log_callback)
        
        # Индексы окон
        self.boss_window_index = None
        self.analyst_window_index = None
        self.chief_window_index = None
        self.developer_window_index = None
        
        # Папка для сохранения выходных файлов
        self.output_folder = "output"
        FileUtils.ensure_folder(self.output_folder)
        
        # Счетчик реально выполненных этапов
        self.completed_stages = 0
    
    def _send_stage_update(self, stage_num: int, stage_name: str):
        """Отправка обновления этапа в UI"""
        self.log(f"=== ЭТАП {stage_num}: {stage_name} ===", "info")
    
    def _save_to_output(self, content: str, filename_prefix: str, extension: str = "md") -> str:
        """Сохранение содержимого в папку output"""
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
    
    def _ensure_minimum_windows(self, required: int = 4) -> bool:
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
    
    # ========== ЭТАП 1: ПОЛЬЗОВАТЕЛЬ -> НАЧАЛЬНИК (окно 1) ==========
    def execute_stage1_user_to_boss(self, user_message: str) -> Union[str, dict, None]:
        self._send_stage_update(1, "пользователь -> начальник")
        if not self._ensure_minimum_windows(4):
            return None
        
        self.boss_window_index = 0
        self.browser_manager.switch_to_window(self.boss_window_index)
        
        boss_prompt = self._read_prompt_file("Boss.txt")
        parts = [boss_prompt]
        if user_message:
            parts.append(f"\n[СООБЩЕНИЕ ПОЛЬЗОВАТЕЛЯ]:\n{user_message}")
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
        
        # Обработка всех возможных токенов начальника
        if token == "WAITING_USER":
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
            self.log(f"Неизвестный токен начальника: {token}", "warning")
            self.message_handler.send_message("НЕИЗВЕСНЫЙ СТАТУС! ПОДТВЕРДИТЕ СТАТУС")
            return None
    
    # ========== ЭТАП 2: НАЧАЛЬНИК -> АНАЛИТИК (окно 2) ==========
    def execute_stage2_boss_to_analyst(self, boss_response: str) -> Union[str, dict, None]:
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
        
        # Обработка всех возможных токенов аналитика
        if token == "SENT_TO_BOSS":
            return clean_response
        elif token == "SENT_TO_CHIEF":
            return {"type": "to_chief_direct", "message": clean_response}
        else:
            self.log(f"Неизвестный токен аналитика: {token}", "warning")
            self.message_handler.send_message("НЕИЗВЕСНЫЙ СТАТУС! ПОДТВЕРДИТЕ СТАТУС")
            return None
    
    # ========== ЭТАП 3: АНАЛИТИК -> НАЧАЛЬНИК (окно 1) ==========
    def execute_stage3_analyst_to_boss(self, analyst_response: str) -> Union[str, dict, None]:
        self._send_stage_update(3, "аналитик -> начальник")
        
        self.browser_manager.switch_to_window(self.boss_window_index)
        time.sleep(2)
        
        self.browser_manager.ensure_empty_chat()
        
        if not self.browser_manager.is_input_available():
            self.log("Поле ввода в окне начальника недоступно", "error")
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
        
        attempt = 0
        
        # Бесконечный цикл доработки ТЗ (без ограничений)
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
        
        # Обработка всех возможных результатов
        if token == "WAITING_CHIEF":
            return clean_response
        elif token == "WAITING_ANALYST":
            return clean_response
        elif token == "NEEDS_FULL_CYCLE":
            return {"type": "need_full_cycle", "message": clean_response}
        elif token == "WAITING_USER":
            return {"type": "need_clarification", "message": clean_response}
        else:
            self.log(f"Не удалось получить одобрение начальника. Токен: {token}", "error")
            return None
    
    # ========== ЭТАП 4: НАЧАЛЬНИК -> ГЛАВНЫЙ (окно 3) ==========
    def execute_stage4_boss_to_chief(self, final_tz: str) -> Optional[str]:
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
        
        chief_prompt = self._read_prompt_file("Chief_developer.txt")
        parts = [chief_prompt]
        parts.append(f"\n[ФИНАЛЬНОЕ ТЗ ОТ НАЧАЛЬНИКА]:\n{final_tz}")
        project_files = self._get_project_files_content()
        if project_files:
            parts.append(project_files)
        
        message = TextUtils.remove_emojis("\n\n".join(parts))
        
        response = self._send_and_wait(message, "главного разработчика")
        return response
    
    # ========== ЭТАП 5: ГЛАВНЫЙ -> РЯДОВОЙ (окно 4) ==========
    def execute_stage5_chief_to_developer(self, chief_response: str, files_to_send: list, revision_feedback: str = "") -> Optional[str]:
        self._send_stage_update(5, "главный -> разработчик")
        
        found_files = self.file_search.find_files(self.config.project_folder, files_to_send)
        
        token_files = "=== ФАЙЛЫ ПРОЕКТА ===\n"
        for requested_path, actual_path in found_files.items():
            token_files += f"{requested_path}\n"
        
        parts = []
        ordinary_prompt = self._read_prompt_file("Ordinary_developer.txt")
        if ordinary_prompt and not ordinary_prompt.startswith("[Файл"):
            parts.append(ordinary_prompt)
        else:
            parts.append("[РОЛЕВОЙ ПРОМТ: РЯДОВОЙ РАЗРАБОТЧИК]")
            parts.append("Твоя задача - написать код в соответствии с ТЗ.")
        
        if revision_feedback:
            parts.append(f"\n[ЗАМЕЧАНИЯ НА ДОРАБОТКУ]:\n{revision_feedback}")
        else:
            parts.append(f"\n[ЗАПРОС ОТ ГЛАВНОГО РАЗРАБОТЧИКА]:\n{chief_response}")
        
        parts.append(f"\n{token_files}")
        
        for requested_path, actual_path in found_files.items():
            content = self.file_search.read_file_content(actual_path)
            if content:
                parts.append(f"\n[СОДЕРЖИМОЕ ФАЙЛА {requested_path}]:\n```\n{content}\n```")
        
        message = TextUtils.remove_emojis("\n\n".join(parts))
        
        self.developer_window_index = 3
        self.browser_manager.switch_to_window(self.developer_window_index)
        
        time.sleep(2)
        self.browser_manager.ensure_empty_chat()
        
        if not self.browser_manager.is_input_available():
            self.log("Поле ввода недоступно", "error")
            return None
        
        response = self._send_and_wait(message, "рядового разработчика")
        return response
    
    # ========== ЭТАП 6: РЯДОВОЙ -> ГЛАВНЫЙ (окно 3) ==========
    def execute_stage6_developer_to_chief(self, developer_response: str) -> Optional[str]:
        self._send_stage_update(6, "разработчик -> главный")
        
        self.browser_manager.switch_to_window(self.chief_window_index)
        
        time.sleep(2)
        self.browser_manager.ensure_empty_chat()
        
        if not self.browser_manager.is_input_available():
            self.log("Поле ввода в окне главного разработчика недоступно", "error")
            return None
        
        chief_prompt = self._read_prompt_file("Chief_developer.txt")
        parts = [chief_prompt]
        parts.append("\n[ОТВЕТ ОТ РЯДОВОГО РАЗРАБОТЧИКА]:")
        parts.append(developer_response)
        
        project_files = self._get_project_files_content()
        if project_files:
            parts.append(project_files)
        
        message = TextUtils.remove_emojis("\n\n".join(parts))
        
        response = self._send_and_wait(message, "главного разработчика")
        return response
    
    # ========== ЭТАП 7: ГЛАВНЫЙ -> АНАЛИТИК (документация, окно 2) ==========
    def execute_stage7_chief_to_analyst(self, chief_response: str, developer_response: str, old_files_content: str = "") -> Optional[str]:
        self._send_stage_update(7, "главный -> аналитик (документация)")
        
        new_code = self._extract_code_block(developer_response)
        if new_code:
            self.log(f"Извлечён код разработчика ({len(new_code)} символов)", "success")
        else:
            self.log("Код не найден в ответе разработчика", "warning")
            new_code = developer_response
        
        old_files = self._extract_old_files(chief_response) if not old_files_content else old_files_content
        
        self.browser_manager.switch_to_window(self.analyst_window_index)
        
        time.sleep(2)
        self.browser_manager.ensure_empty_chat()
        
        if not self.browser_manager.is_input_available():
            self.log("Поле ввода в окне аналитика недоступно", "error")
            return None
        
        analyst_prompt = self._read_prompt_file("Analyst.txt")
        parts = [analyst_prompt]
        
        parts.append("\n[ИНСТРУКЦИЯ]:")
        parts.append("Твоя задача - обновить документацию проекта.")
        parts.append("У тебя есть:")
        parts.append("1. Старые файлы проекта (если есть)")
        parts.append("2. Новый код, который написал разработчик")
        parts.append("3. Стандартные файлы для ориентира")
        parts.append("4. Файлы текущего проекта")
        parts.append("\nНужно обновить документацию, опираясь на стандартные файлы.")
        parts.append("Если какого-то файла не было в проекте - создай его с нуля по стандарту.")
        
        if old_files:
            parts.append(f"\n=== СТАРЫЕ ФАЙЛЫ ===\n{old_files}")
        
        parts.append(f"\n=== НОВЫЕ ФАЙЛЫ (КОД ОТ РАЗРАБОТЧИКА) ===\n{new_code}")
        
        standard_files = self._get_standard_files_content()
        if standard_files:
            parts.append(f"\n{standard_files}")
        
        project_files = self._get_all_project_files_content()
        if project_files:
            parts.append(f"\n[ТЕКУЩИЕ ФАЙЛЫ ПРОЕКТА]:{project_files}")
        
        clean_chief = TokenParser.remove_chief_token(chief_response)
        parts.append(f"\n[ЗАПРОС ОТ ГЛАВНОГО РАЗРАБОТЧИКА]:\n{clean_chief}")
        
        message = TextUtils.remove_emojis("\n\n".join(parts))
        
        response = self._send_and_wait(message, "аналитика")
        return response
    
    # ========== ЭТАП 8: АНАЛИТИК -> ГЛАВНЫЙ (обновлённые файлы документации, окно 3) ==========
    def execute_stage8_analyst_to_chief(self, analyst_response: str) -> Optional[str]:
        self._send_stage_update(8, "аналитик -> главный")
        
        self.browser_manager.switch_to_window(self.chief_window_index)
        
        time.sleep(2)
        self.browser_manager.ensure_empty_chat()
        
        if not self.browser_manager.is_input_available():
            self.log("Поле ввода в окне главного разработчика недоступно", "error")
            return None
        
        token = TokenParser.parse_analyst_token(analyst_response)
        clean_analyst = TokenParser.remove_analyst_token(analyst_response)
        
        self.log(f"Ответ аналитика (токен: {token})", "info")
        
        self._save_to_output(clean_analyst, "documentation", "md")
        
        chief_prompt = self._read_prompt_file("Chief_developer.txt")
        parts = [chief_prompt]
        
        parts.append("\n[ОБНОВЛЁННЫЕ ФАЙЛЫ ДОКУМЕНТАЦИИ ОТ АНАЛИТИКА]:")
        parts.append(clean_analyst)
        
        project_files = self._get_project_files_content()
        if project_files:
            parts.append(project_files)
        
        message = TextUtils.remove_emojis("\n\n".join(parts))
        
        response = self._send_and_wait(message, "главного разработчика")
        return response
    
    # ========== ЭТАП 9: ГЛАВНЫЙ -> НАЧАЛЬНИК (отчёт + документация, окно 1) ==========
    def execute_stage9_chief_to_boss(self, chief_response: str, analyst_response: str = "") -> Optional[str]:
        self._send_stage_update(9, "главный -> начальник (отчёт)")
        
        self.browser_manager.switch_to_window(self.boss_window_index)
        
        time.sleep(2)
        self.browser_manager.ensure_empty_chat()
        
        if not self.browser_manager.is_input_available():
            self.log("Поле ввода в окне начальника недоступно", "error")
            return None
        
        chief_token = TokenParser.parse_chief_token(chief_response)
        clean_chief = TokenParser.remove_chief_token(chief_response)
        
        self.log(f"Ответ главного (токен: {chief_token})", "info")
        
        boss_prompt = self._read_prompt_file("Boss.txt")
        parts = [boss_prompt]
        
        parts.append("\n[ОТЧЁТ ОТ ГЛАВНОГО РАЗРАБОТЧИКА]:")
        parts.append(clean_chief)
        
        if analyst_response:
            clean_analyst = TokenParser.remove_analyst_token(analyst_response)
            parts.append("\n[ОБНОВЛЁННАЯ ДОКУМЕНТАЦИЯ ОТ АНАЛИТИКА]:")
            parts.append(clean_analyst)
        
        project_files = self._get_project_files_content()
        if project_files:
            parts.append(project_files)
        
        message = TextUtils.remove_emojis("\n\n".join(parts))
        
        response = self._send_and_wait(message, "начальника")
        return response
    
    # ========== ЭТАП 10: НАЧАЛЬНИК -> ПОЛЬЗОВАТЕЛЬ (подробная докладная, окно 1) ==========
    def execute_stage10_boss_to_user(self, boss_response: str) -> Optional[str]:
        self._send_stage_update(10, "начальник -> пользователь")
        
        self.browser_manager.switch_to_window(self.boss_window_index)
        
        time.sleep(2)
        self.browser_manager.ensure_empty_chat()
        
        if not self.browser_manager.is_input_available():
            self.log("Поле ввода в окне начальника недоступно", "error")
            return None
        
        boss_token = TokenParser.parse_boss_token(boss_response)
        clean_boss = TokenParser.remove_boss_token(boss_response)
        
        self.log(f"Ответ начальника (токен: {boss_token})", "info")
        
        self._save_to_output(clean_boss, "report", "md")
        
        parts = []
        parts.append("[СООБЩЕНИЕ ОТ НАЧАЛЬНИКА]:")
        parts.append(clean_boss)
        parts.append("\n[ДОКЛАДНАЯ ЗАПИСКА]:")
        parts.append("Работа над проектом завершена. Подробности в прикреплённых файлах.")
        
        message = TextUtils.remove_emojis("\n\n".join(parts))
        
        response = self._send_and_wait(message, "пользователя")
        return response
    
    # ========== ПОЛНЫЙ ПАЙПЛАЙН С ОБРАБОТКОЙ ВСЕХ ТОКЕНОВ ==========
    def execute_full_pipeline(self, user_message: str, files_to_send: list = None) -> bool:
        self.completed_stages = 0
        
        # ========== ЭТАП 1 ==========
        result1 = self.execute_stage1_user_to_boss(user_message)
        if not result1:
            return False
        
        # Обработка различных исходов этапа 1
        if isinstance(result1, dict):
            if result1.get("type") == "need_clarification":
                self.log("Начальник запросил уточнение у пользователя. Ожидание ввода.", "warning")
                self.completed_stages = 1
                return True
            elif result1.get("type") == "need_full_cycle":
                self.log("Требуется полный цикл. Начало заново.", "warning")
                return self.execute_full_pipeline(user_message, files_to_send)
            elif result1.get("type") == "needs_revision":
                self.log("ТЗ требует доработки пользователем.", "warning")
                return True
            else:
                self.log(f"Неизвестный тип ответа этапа 1: {result1.get('type')}", "error")
                return False
        
        boss_response = result1
        self.completed_stages = 1
        
        # ========== ЭТАП 2 ==========
        result2 = self.execute_stage2_boss_to_analyst(boss_response)
        if not result2:
            return False
        
        # Обработка различных исходов этапа 2
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
                    self.log("Начальник запросил уточнение у пользователя.", "warning")
                    return True
                elif result3.get("type") == "need_full_cycle":
                    self.log("Требуется полный цикл. Начало заново.", "warning")
                    return self.execute_full_pipeline(user_message, files_to_send)
                else:
                    self.log(f"Неизвестный тип ответа этапа 3: {result3.get('type')}", "error")
                    return False
            else:
                final_tz = result3
                # ========== ЭТАП 4 ==========
                chief_response = self.execute_stage4_boss_to_chief(final_tz)
                if not chief_response:
                    return False
                self.completed_stages = 4
                skip_to_chief = False
        
        # ========== ОБРАБОТКА ОТВЕТА ГЛАВНОГО ==========
        if skip_to_chief:
            pass
        
        chief_token = TokenParser.parse_chief_token(chief_response)
        clean_chief = TokenParser.remove_chief_token(chief_response)
        
        self.log(f"Токен главного после этапа 4: {chief_token}", "info")
        
        # ========== ОБРАБОТКА ВСЕХ ТОКЕНОВ ГЛАВНОГО ==========
        
        # Токен: WAITING_CODE - нужен код от разработчика
        if chief_token == "WAITING_CODE":
            files_to_find = TokenParser.parse_file_list_token(chief_response)
            if not files_to_find:
                files_to_find = files_to_send or ["main.py"]
            
            # Бесконечный цикл доработки кода (без ограничений)
            attempt = 0
            current_chief_response = chief_response
            current_clean_chief = clean_chief
            developer_response_for_docs = None
            chief_response_for_docs = None
            
            while True:
                attempt += 1
                self.log(f"Попытка генерации кода #{attempt}", "info")
                
                # Этап 5
                revision_feedback = "" if attempt == 1 else f"Код не принят. Замечания: {current_clean_chief}"
                developer_response = self.execute_stage5_chief_to_developer(
                    current_clean_chief, files_to_find, revision_feedback
                )
                if not developer_response:
                    return False
                self.completed_stages = 5
                
                # Этап 6
                final_chief = self.execute_stage6_developer_to_chief(developer_response)
                if not final_chief:
                    return False
                self.completed_stages = 6
                
                final_token = TokenParser.parse_chief_token(final_chief)
                self.log(f"Токен главного после этапа 6: {final_token}", "info")
                
                # Обработка токенов главного после проверки кода
                if final_token == "WAITING_DOCS":
                    # Код принят - сохраняем только одобренную версию
                    self._save_to_output(developer_response, "approved_code", "txt")
                    self.log(f"Код одобрен главным разработчиком на попытке #{attempt}", "success")
                    chief_response_for_docs = final_chief
                    developer_response_for_docs = developer_response
                    break
                    
                elif final_token == "NEEDS_CODE_REVISION":
                    # Код требует доработки - продолжаем цикл
                    self.log(f"Код требует доработки. Отправляем замечания разработчику...", "warning")
                    current_clean_chief = TokenParser.remove_chief_token(final_chief)
                    continue  # Повторяем цикл с замечаниями
                    
                elif final_token == "NEEDS_TZ_REVISION":
                    # ТЗ требует доработки - возвращаемся к начальнику
                    self.log("Главный требует доработки ТЗ. Возврат к начальнику.", "warning")
                    return False
                    
                elif final_token == "SENT_TO_BOSS":
                    # Отправлено начальнику напрямую
                    self.log("Главный отправил ответ напрямую начальнику.", "info")
                    boss_final = self.execute_stage9_chief_to_boss(final_chief)
                    if not boss_final:
                        return False
                    self.completed_stages = 9
                    
                    user_final = self.execute_stage10_boss_to_user(boss_final)
                    if user_final:
                        self.completed_stages = 10
                        self.log("=== ДОКЛАДНАЯ ОТПРАВЛЕНА ПОЛЬЗОВАТЕЛЮ ===", "success")
                    else:
                        self.log("Ответ от пользователя не получен", "error")
                        return False
                    return True
                    
                else:
                    self.log(f"Неизвестный токен: {final_token}", "error")
                    return False
            
            # Если код успешно принят, продолжаем с документацией
            if chief_response_for_docs and developer_response_for_docs:
                # Этап 7: главный -> аналитик (документация)
                old_files = TokenParser.parse_file_list_token(chief_response)
                old_files_content = "\n".join(old_files) if old_files else ""
                
                analyst_docs_response = self.execute_stage7_chief_to_analyst(
                    chief_response_for_docs, developer_response_for_docs, old_files_content
                )
                if not analyst_docs_response:
                    self.log("Ответ от аналитика на этапе 7 не получен", "error")
                    return False
                self.completed_stages = 7
                
                # Обработка токена аналитика
                analyst_token = TokenParser.parse_analyst_token(analyst_docs_response)
                if analyst_token == "SENT_TO_CHIEF":
                    self.log("=== ДОКУМЕНТАЦИЯ ОТ АНАЛИТИКА ПОЛУЧЕНА ===", "success")
                    
                    # Этап 8: аналитик -> главный
                    chief_after_docs = self.execute_stage8_analyst_to_chief(analyst_docs_response)
                    if not chief_after_docs:
                        self.log("Ответ от главного на этапе 8 не получен", "error")
                        return False
                    self.completed_stages = 8
                    
                    # Обработка ответа главного на этапе 8 - бесконечный цикл доработки документации
                    chief_docs_token = TokenParser.parse_chief_token(chief_after_docs)
                    docs_attempt = 0
                    
                    while chief_docs_token == "NEEDS_DOCS_REVISION":
                        docs_attempt += 1
                        self.log(f"Документация требует доработки (попытка {docs_attempt})", "warning")
                        
                        revision_feedback = TokenParser.remove_chief_token(chief_after_docs)
                        revised_analyst = self.execute_stage7_chief_to_analyst(
                            f"Доработайте документацию:\n{revision_feedback}",
                            developer_response_for_docs,
                            old_files_content
                        )
                        if not revised_analyst:
                            return False
                        
                        chief_after_docs = self.execute_stage8_analyst_to_chief(revised_analyst)
                        if not chief_after_docs:
                            return False
                        
                        chief_docs_token = TokenParser.parse_chief_token(chief_after_docs)
                        
                        if chief_docs_token == "WAITING_DOCS":
                            self.log(f"Документация одобрена на попытке #{docs_attempt}", "success")
                            break
                        elif chief_docs_token == "SENT_TO_BOSS":
                            self.log("Главный отправил документацию начальнику.", "info")
                            break
                    
                    # Этап 9: главный -> начальник
                    boss_final = self.execute_stage9_chief_to_boss(chief_after_docs, analyst_docs_response)
                    if not boss_final:
                        self.log("Ответ от начальника на этапе 9 не получен", "error")
                        return False
                    self.completed_stages = 9
                    
                    # Обработка ответа начальника
                    boss_final_token = TokenParser.parse_boss_token(boss_final)
                    if boss_final_token == "NEEDS_REVISION":
                        self.log("Начальник требует доработки отчёта.", "warning")
                    
                    # Этап 10: начальник -> пользователь
                    user_final = self.execute_stage10_boss_to_user(boss_final)
                    if user_final:
                        self.completed_stages = 10
                        self.log("=== ДОКЛАДНАЯ ОТПРАВЛЕНА ПОЛЬЗОВАТЕЛЮ ===", "success")
                    else:
                        self.log("Ответ от пользователя не получен", "error")
                        return False
                        
                elif analyst_token == "SENT_TO_BOSS":
                    self.log("Аналитик отправил документацию напрямую начальнику.", "info")
                    boss_final = self.execute_stage9_chief_to_boss("", analyst_docs_response)
                    if not boss_final:
                        return False
                    self.completed_stages = 9
                    
                    user_final = self.execute_stage10_boss_to_user(boss_final)
                    if user_final:
                        self.completed_stages = 10
                        self.log("=== ДОКЛАДНАЯ ОТПРАВЛЕНА ПОЛЬЗОВАТЕЛЮ ===", "success")
                    else:
                        self.log("Ответ от пользователя не получен", "error")
                        return False
                else:
                    self.log(f"Неизвестный токен аналитика: {analyst_token}", "error")
                    return False
        
        # Токен: WAITING_DOCS - нужна только документация (без кода)
        elif chief_token == "WAITING_DOCS":
            self.log("Запрос только документации (без кода).", "info")
            
            # Этап 7: главный -> аналитик (документация)
            analyst_docs_response = self.execute_stage7_chief_to_analyst(chief_response, "")
            if not analyst_docs_response:
                return False
            self.completed_stages = 7
            
            # Этап 8: аналитик -> главный
            chief_after_docs = self.execute_stage8_analyst_to_chief(analyst_docs_response)
            if not chief_after_docs:
                return False
            self.completed_stages = 8
            
            # Бесконечный цикл доработки документации (без ограничений)
            chief_docs_token = TokenParser.parse_chief_token(chief_after_docs)
            docs_attempt = 0
            
            while chief_docs_token == "NEEDS_DOCS_REVISION":
                docs_attempt += 1
                self.log(f"Документация требует доработки (попытка {docs_attempt})", "warning")
                
                revision_feedback = TokenParser.remove_chief_token(chief_after_docs)
                revised_analyst = self.execute_stage7_chief_to_analyst(
                    f"Доработайте документацию:\n{revision_feedback}",
                    "",
                    ""
                )
                if not revised_analyst:
                    return False
                
                chief_after_docs = self.execute_stage8_analyst_to_chief(revised_analyst)
                if not chief_after_docs:
                    return False
                
                chief_docs_token = TokenParser.parse_chief_token(chief_after_docs)
                
                if chief_docs_token == "WAITING_DOCS":
                    self.log(f"Документация одобрена на попытке #{docs_attempt}", "success")
                    break
                elif chief_docs_token == "SENT_TO_BOSS":
                    self.log("Главный отправил документацию начальнику.", "info")
                    break
            
            # Этап 9: главный -> начальник
            boss_final = self.execute_stage9_chief_to_boss(chief_after_docs, analyst_docs_response)
            if not boss_final:
                return False
            self.completed_stages = 9
            
            # Этап 10: начальник -> пользователь
            user_final = self.execute_stage10_boss_to_user(boss_final)
            if not user_final:
                return False
            self.completed_stages = 10
        
        # Токен: NEEDS_TZ_REVISION - ТЗ требует доработки
        elif chief_token == "NEEDS_TZ_REVISION":
            self.log("Главный требует доработки ТЗ. Возврат к начальнику.", "warning")
            return False
        
        # Токен: SENT_TO_BOSS - уже отправлено начальнику
        elif chief_token == "SENT_TO_BOSS":
            self.log("Главный уже отправил ответ начальнику.", "info")
            boss_final = self.execute_stage9_chief_to_boss(chief_response)
            if not boss_final:
                return False
            self.completed_stages = 9
            
            user_final = self.execute_stage10_boss_to_user(boss_final)
            if user_final:
                self.completed_stages = 10
                self.log("=== ДОКЛАДНАЯ ОТПРАВЛЕНА ПОЛЬЗОВАТЕЛЮ ===", "success")
            else:
                self.log("Ответ от пользователя не получен", "error")
                return False
        
        # Неизвестный токен
        else:
            self.log(f"Неизвестный или необработанный токен главного: {chief_token}", "error")
            return False
        
        self.log(f"=== ВЫПОЛНЕНО {self.completed_stages} ИЗ 10 ЭТАПОВ ===", "success")
        return True
