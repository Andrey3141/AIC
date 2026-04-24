# файл: aic/core/message_handler.py
import time
import re
from dataclasses import dataclass
from typing import Optional, Callable, Tuple
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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
    
    def wait_for_new_assistant_message(self, last_assistant_id: Optional[str], timeout_seconds: int) -> Optional[str]:
        start_time = time.time()
        last_id = last_assistant_id
        
        self.log_callback(f"Ожидание ответа от ассистента (таймаут: {timeout_seconds}с)...", "info")
        
        while time.time() - start_time < timeout_seconds:
            if not self.driver or not self.is_connected:
                self.log_callback("Соединение с браузером потеряно", "error")
                return None
            
            try:
                current_text = self._get_current_assistant_text()
                current_id = self.get_last_assistant_message_id()
                
                self._debug(f"ID: {current_id}")
                self._debug(f"TEXT LEN: {len(current_text) if current_text else 0}")

                if current_text:
                   self._debug(f"TEXT START: {current_text[:100]}")
                
                if current_text and len(current_text) > 20:
                    # 🔒 если это наше же сообщение — пропускаем
                    if self._is_own_message(current_text):
                        self._debug("SKIP: own message detected")
                        self.log_callback("ПРОПУЩЕНО: своё сообщение", "warning")
                        time.sleep(1)
                        continue
                        
                    self._debug(f"last_id={last_id}, current_id={current_id}")

                    if current_text != self._last_text:
                        self._last_text = current_text
                        last_id = current_id

                        elapsed = int(time.time() - start_time)
                        elapsed_min = elapsed // 60
                        elapsed_sec = elapsed % 60

                        self.log_callback(f"Обнаружен ответ через {elapsed_min}мин{elapsed_sec:02d}с", "success")
                        self.log_callback(f"Длина ответа: {len(current_text)} символов", "info")

                        preview = self._truncate_text(current_text, 10)
                        self.log_callback(f"=== СОДЕРЖАНИЕ ОТВЕТА ===\n{preview}", "info")

                        return current_text
                
                try:
                    continue_btn = self.driver.find_elements(
                        By.XPATH, 
                        "//button[contains(text(), 'Продолжить') or contains(text(), 'Continue')]"
                    )
                    for btn in continue_btn:
                        if btn.is_displayed() and btn.is_enabled():
                            btn.click()
                            self.log_callback("Нажата кнопка 'Продолжить'", "success")
                            time.sleep(2)
                            break
                except:
                    pass
                
                elapsed = int(time.time() - start_time)
                if elapsed > 0 and elapsed % 15 == 0 and elapsed < timeout_seconds - 5:
                    remaining = timeout_seconds - elapsed
                    remaining_min = remaining // 60
                    remaining_sec = remaining % 60
                    self.log_callback(f"Ожидание ответа... осталось {remaining_min}мин{remaining_sec:02d}с", "info")
                
                time.sleep(2)
                
            except Exception as e:
                self.log_callback(f"Ошибка при ожидании: {str(e)}", "error")
                time.sleep(2)
        
        self.log_callback(f"Таймаут {timeout_seconds}с истёк, ответ не получен", "warning")
        return None
    
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
