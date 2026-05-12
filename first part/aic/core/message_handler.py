# файл: aic/core/message_handler.py
import time
import re
import json
import os
from dataclasses import dataclass
from typing import Optional, Callable, Tuple
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pyperclip

@dataclass
class MessageSnapshot:
    message_count: int
    last_user_message_id: Optional[str] = None
    last_user_message_text: Optional[str] = None
    last_assistant_message_id: Optional[str] = None
    last_assistant_message_text: Optional[str] = None

class MessageHandler:
    
    # Токены статусов для парсинга
    STATUS_TOKENS = {
        "WAITING_USER": "=== СТАТУС ===\nЖДУ ОТВЕТА ПОЛЬЗОВАТЕЛЯ",
        "SENT_TO_USER": "=== СТАТУС ===\nОТПРАВЛЕНО ПОЛЬЗОВАТЕЛЮ",
        "NEEDS_REVISION": "=== СТАТУС ===\nТРЕБУЕТ ДОРАБОТКИ",
        "WAITING_ANALYST": "=== СТАТУС ===\nЖДУ УТОЧНЁННОЕ ТЗ",
        "WAITING_CHIEF": "=== СТАТУС ===\nЖДУ ОТЧЁТ И ДОКУМЕНТАЦИЮ",
        "NEEDS_FULL_CYCLE": "=== СТАТУС ===\nТРЕБУЕТ ПОВТОРНОГО ЦИКЛА"
    }
    
    # Мусорные фразы интерфейса DeepSeek, которые нужно фильтровать
    GARBAGE_PHRASES = [
        "Start chatting with",
        "DeepThink",
        "Search",
        "Instant",
        "Expert",
        "Chat with",
        "New chat",
        "Send message",
    ]
    
    ASSISTANT_SELECTORS = [
        "[data-message-role='assistant']",
        ".ds-message[data-role='assistant']"
    ]
    
    ANY_MESSAGE_SELECTORS = [
        ".ds-message",
        "[data-message-role]",
        "[data-role]",
        ".chat-message",
        ".message-content",
        ".ds-markdown",
        ".markdown",
        ".prose",
        "div[class*='message']"
    ]
    
    def __init__(self, driver, log_callback: Callable[[str, str], None]):
        self.driver = driver
        self.log_callback = log_callback
        self.is_connected = True
        # Храним последнее отправленное сообщение для фильтрации
        self._last_sent_message = None
        self.debug = True
        self._last_text = None
        # Загружаем селектор кнопки из конфига
        self._continue_button_selector = self._load_continue_button_selector()
    
    def _load_continue_button_selector(self) -> str:
        """Загружает селектор кнопки Continue из конфига"""
        default_selector = "button.ds-atom-button.ds-basic-button.ds-basic-button--outlined"
        try:
            config_path = os.path.join(os.path.dirname(__file__), '..', 'aic_config.json')
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    selector = config.get('continue_button_selector', default_selector)
                    self.log_callback(f"Загружен селектор кнопки Continue: {selector}", "info")
                    return selector
        except Exception as e:
            self.log_callback(f"Ошибка загрузки селектора из конфига: {str(e)}", "warning")
        self.log_callback(f"Используется стандартный селектор: {default_selector}", "info")
        return default_selector
    
    def _check_and_click_continue(self, driver) -> bool:
        """
        Поиск кнопки по CSS-селектору
        Если найдена и видима/кликабельна → нажать, вернуть True
        Иначе → вернуть False
        """
        if not driver or not self.is_connected:
            return False
        
        try:
            # Используем WebDriverWait с коротким таймаутом 0.5 сек
            wait = WebDriverWait(driver, 0.5)
            button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, self._continue_button_selector)))
            
            if button and button.is_displayed() and button.is_enabled():
                button.click()
                self.log_callback(f"Нажата кнопка Continue (селектор: {self._continue_button_selector})", "success")
                return True
        except TimeoutException:
            # Кнопка не найдена в течение таймаута - это нормально
            pass
        except NoSuchElementException:
            pass
        except Exception as e:
            self.log_callback(f"Ошибка при поиске кнопки Continue: {str(e)}", "warning")
        
        return False
    
    def _debug(self, msg: str):
        if self.debug:
            print(f"[DEBUG] {msg}")
    
    def get_file_stats(self, message: str) -> str:
        if not message:
            return "0 строк, 0 символов"
        lines = message.split('\n')
        return f"{len(lines)} строк, {len(message)} символов"
    
    def parse_boss_status_token(self, message: str) -> Optional[str]:
        for token_key, token_value in self.STATUS_TOKENS.items():
            if token_value in message:
                self.log_callback(f"Найден токен начальника: {token_key}", "info")
                return token_key
        self.log_callback("Токен начальника не найден в ответе", "warning")
        return None
    
    def remove_status_token(self, message: str) -> str:
        result = message
        for token_value in self.STATUS_TOKENS.values():
            result = result.replace(token_value, "")
        return result.strip()
    
    def get_last_assistant_message_id(self) -> Optional[str]:
        if not self.driver or not self.is_connected:
            return None

        try:
            elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-message-role='assistant']")

            if not elements:
                return None

            last_elem = elements[-1]

            msg_id = last_elem.get_attribute('data-message-id') or last_elem.get_attribute('id')

            return msg_id if msg_id else str(id(last_elem))

        except Exception as e:
            self.log_callback(f"Ошибка получения ID ассистента: {str(e)}", "error")
            return None
    
    def _truncate_text(self, text: str, max_words: int = 10) -> str:
        """Обрезает текст до указанного количества слов для лога"""
        if not text:
            return ""
        words = text.split()
        if len(words) <= max_words:
            return text
        truncated = ' '.join(words[:max_words])
        return f"{truncated} [обрезано]"
    
    def _is_garbage_response(self, text: str) -> bool:
        """
        Проверяет, является ли ответ мусором из интерфейса DeepSeek.
        Возвращает True, если ответ состоит в основном из мусорных фраз.
        """
        if not text:
            return True
        
        words = text.split()
        if len(words) <= 5:
            garbage_count = 0
            for word in words:
                for garbage in self.GARBAGE_PHRASES:
                    if garbage.lower() in word.lower():
                        garbage_count += 1
                        break
            if garbage_count >= len(words) * 0.5:
                return True
        
        cleaned = text
        for garbage in self.GARBAGE_PHRASES:
            cleaned = cleaned.replace(garbage, "")
        cleaned = cleaned.strip()
        
        if len(cleaned) < 10:
            return True
        
        return False
    
    def _is_own_message(self, text: str) -> bool:
        if not self._last_sent_message or not text:
            return False

        sent = self._last_sent_message[:300].strip()
        received = text[:300].strip()

        # нормализация
        sent = re.sub(r'\s+', ' ', sent)
        received = re.sub(r'\s+', ' ', received)

        # частичное совпадение
        if sent[:150] in received:
            return True

        return False
    
    def _clean_html(self, html_content: str) -> str:
        """
        Очищает HTML от тегов, но сохраняет символы ``` и специальные символы.
        """
        if not html_content:
            return ""
        
        text = html_content
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&amp;', '&')
        text = text.replace('&quot;', '"')
        text = text.replace('&#39;', "'")
        text = text.replace('&nbsp;', ' ')
        
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        if '```' not in text and ('python' in text or 'bash' in text or 'copy' in text):
            code_match = re.search(r'<pre><code[^>]*>(.*?)</code></pre>', html_content, re.DOTALL)
            if code_match:
                code_content = code_match.group(1)
                code_content = code_content.replace('&lt;', '<').replace('&gt;', '>')
                text = text + f"\n```\n{code_content}\n```"
        
        return text
    
    def _get_current_assistant_text(self) -> Optional[str]:
        if not self.driver:
            return None

        try:
            messages = self.driver.find_elements(By.CSS_SELECTOR, ".ds-message")

            if not messages:
                return None

            # идём с конца (последние сообщения)
            for msg in reversed(messages):
                try:
                    # 1. пробуем стандартный текст
                    full_text = msg.text or ""
    
                    # 2. fallback если Selenium тупит
                    if not full_text.strip():
                        full_text = msg.get_attribute("innerText") or ""

                    full_text = full_text.strip()
    
                    if not full_text:
                        continue

                    # 3. пропускаем своё сообщение
                    if self._is_own_message(full_text):
                        continue

                    # 4. пропускаем мусор UI
                    if self._is_garbage_response(full_text):
                        continue

                    # 5. защита от "пустых" коротких ответов UI
                    if len(full_text) < 2:
                        continue

                    self._debug(f"FOUND MSG: {full_text[:100]}")
                    return full_text
    
                except Exception as inner_e:
                    self._debug(f"skip msg error: {inner_e}")
                    continue

            return None

        except Exception as e:
            self.log_callback(f"Ошибка получения текста: {str(e)}", "error")
            return None
    
    def wait_for_new_assistant_message(self, last_message_id: str, timeout: int = 120) -> Optional[str]:
        """Ожидание нового ответа ассистента с поддержкой кнопки Continue"""
        start_time = time.time()
        full_response = ""
        continue_button_selector = self._continue_button_selector
        
        while time.time() - start_time < timeout:
            # Проверяем наличие кнопки Continue
            if self.driver:
                try:
                    continue_button = self.driver.find_elements(By.CSS_SELECTOR, continue_button_selector)
                    if continue_button and continue_button[0].is_displayed():
                        self.log_callback(f"Нажата кнопка Continue (селектор: {continue_button_selector})", "success")
                        continue_button[0].click()
                        # СБРАСЫВАЕМ ТАЙМЕР - продолжаем ждать ответ
                        start_time = time.time()
                        self.log_callback("Таймер ожидания сброшен и перезапущен", "info")
                        time.sleep(2)
                        continue
                except:
                    pass
            
            # Получаем новое сообщение
            current_text = self._get_current_assistant_text()
            if current_text and current_text != self._last_text:
                self._last_text = current_text
                full_response = current_text
                # Проверяем, не закончился ли ответ (нет кнопки Continue)
                try:
                    continue_button = self.driver.find_elements(By.CSS_SELECTOR, continue_button_selector)
                    if not continue_button or not continue_button[0].is_displayed():
                        self.log_callback("Ответ полностью получен (кнопка Continue исчезла)", "info")
                        return full_response
                except:
                    return full_response
            
            time.sleep(1)
        
        return full_response if full_response else None
    
    def set_timer(self, timer) -> None:
        """Устанавливает таймер для возможности сброса"""
        self._timer = timer
    
    def send_message(self, message: str) -> bool:
        if not self.driver or not self.is_connected:
            self.log_callback("Нет подключения к браузеру", "error")
            return False
        
        try:
            wait = WebDriverWait(self.driver, 10)
            input_field = wait.until(EC.presence_of_element_located((By.TAG_NAME, "textarea")))
            
            input_field.clear()
            time.sleep(0.3)
            
            pyperclip.copy(message)
            input_field.click()
            time.sleep(0.3)
            input_field.send_keys(Keys.CONTROL + 'v')
            time.sleep(0.5)
            
            # Запоминаем отправляемое сообщение ДО нажатия Enter
            self._last_sent_message = message
            
            # Запоминаем текущее количество сообщений в чате перед отправкой
            messages_before = len(self.driver.find_elements(By.CSS_SELECTOR, "[data-message-role]"))
            
            input_field.send_keys(Keys.ENTER)
            time.sleep(1.0)
            
            # Проверяем, что сообщение реально отправилось
            try:
                messages_after = len(self.driver.find_elements(By.CSS_SELECTOR, "[data-message-role]"))
                if messages_after <= messages_before:
                    current_value = input_field.get_attribute("value") or input_field.text or ""
                    if current_value.strip():
                        self.log_callback("ОШИБКА: Сообщение не отправилось (поле не очищено)", "error")
                        self._last_sent_message = None
                        return False
            except:
                pass
            
            line_count = len(message.split('\n'))
            self.log_callback(f"Сообщение отправлено ({line_count} строк)", "success")
            return True
            
        except Exception as e:
            self.log_callback(f"Ошибка отправки: {str(e)}", "error")
            self._last_sent_message = None
            return False
    
    def click_continue_button(self) -> bool:
        if not self.driver or not self.is_connected:
            return False
        
        try:
            elements = self.driver.find_elements(
                By.XPATH, 
                "//button[contains(text(), 'Продолжить') or contains(text(), 'Continue') or contains(text(), 'продолжить')]"
            )
            for elem in elements:
                if elem.is_displayed() and elem.is_enabled():
                    elem.click()
                    self.log_callback("Нажата кнопка 'Продолжить'", "success")
                    return True
            return False
        except:
            return False
    
    def is_connected_check(self) -> bool:
        """Проверка, что соединение с браузером активно"""
        if not self.driver or not self.is_connected:
            return False
        try:
            self.driver.title
            return True
        except:
            self.is_connected = False
            return False
