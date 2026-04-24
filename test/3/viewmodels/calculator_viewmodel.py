# файл: viewmodels/calculator_viewmodel.py
from PySide6.QtCore import QObject, Signal
import threading

class CalculatorViewModel(QObject):
    """ViewModel для калькулятора, связывает Model и View"""
    
    # Сигналы для обновления View
    display_updated = Signal(str)
    error_occurred = Signal(str)
    voice_processing_started = Signal()
    voice_processing_finished = Signal()
    
    def __init__(self, model):
        super().__init__()
        self.model = model
        self.current_expression = ""
        self.display_text = ""
        self.voice_handler = None
        self.command_parser = None
        self.is_voice_active = False
        self.voice_thread = None
        self.voice_lock = threading.Lock()
    
    def set_voice_handler(self, handler):
        """Установка обработчика голосового ввода"""
        self.voice_handler = handler
    
    def set_command_parser(self, parser):
        """Установка парсера голосовых команд"""
        self.command_parser = parser
    
    def on_number_clicked(self, digit):
        """Обработка нажатия цифровой кнопки"""
        self.current_expression += str(digit)
        self.update_display(self.current_expression)
    
    def on_operator_clicked(self, op):
        """Обработка нажатия кнопки оператора"""
        self.current_expression += op
        self.update_display(self.current_expression)
    
    def on_equal_clicked(self):
        """Обработка нажатия кнопки = (вычисляет текущее выражение)"""
        if not self.current_expression:
            return
        
        try:
            result = self.model.evaluate_expression(self.current_expression)
            self.display_text = str(result)
            self.current_expression = str(result)
            self.update_display(self.display_text)
        except ZeroDivisionError as e:
            self.error_occurred.emit(str(e))
            self.current_expression = ""
            self.update_display("")
        except ValueError as e:
            self.error_occurred.emit(str(e))
            self.current_expression = ""
            self.update_display("")
        except Exception as e:
            self.error_occurred.emit(f"Неизвестная ошибка: {str(e)}")
            self.current_expression = ""
            self.update_display("")
    
    def on_clear_clicked(self):
        """Обработка нажатия кнопки C (очистка)"""
        self.current_expression = ""
        self.display_text = ""
        self.update_display("")
    
    def set_expression_from_view(self, expression):
        """
        Устанавливает выражение из строки формул (для Excel-стиля)
        
        Args:
            expression (str): Выражение из строки ввода
        """
        self.current_expression = expression
        self.update_display(expression)
    
    def evaluate_from_formula_line(self, expression):
        """
        Вычисляет выражение из строки формул (Excel-стиль)
        
        Args:
            expression (str): Выражение из строки ввода
        """
        if not expression:
            return
        
        self.current_expression = expression
        self.on_equal_clicked()
    
    def on_voice_input_triggered(self):
        """Обработка активации голосового ввода (запуск/остановка)"""
        if not self.voice_handler or not self.command_parser:
            self.error_occurred.emit("Голосовой ввод не доступен")
            return
        
        with self.voice_lock:
            if self.is_voice_active:
                # Останавливаем распознавание
                self.stop_voice_recognition()
            else:
                # Запускаем распознавание
                self.start_voice_recognition()
    
    def start_voice_recognition(self):
        """Запуск распознавания голоса"""
        if self.is_voice_active:
            return
        
        self.is_voice_active = True
        self.voice_processing_started.emit()
        
        def process_voice():
            try:
                # Захват и распознавание речи
                text = self.voice_handler.recognize_speech()
                
                # Проверяем, не был ли процесс остановлен
                if not self.is_voice_active:
                    return
                
                if text and text != "Не распознано":
                    # Парсинг распознанного текста
                    parsed_expression = self.command_parser.parse_voice_text(text)
                    if parsed_expression:
                        # Добавляем распознанное выражение к текущему
                        self.current_expression += parsed_expression
                        self.update_display(self.current_expression)
                    else:
                        self.error_occurred.emit("Не удалось распознать команду")
                else:
                    self.error_occurred.emit(text if text else "Не распознано")
            except Exception as e:
                self.error_occurred.emit(f"Ошибка голосового ввода: {str(e)}")
            finally:
                with self.voice_lock:
                    self.is_voice_active = False
                self.voice_processing_finished.emit()
        
        self.voice_thread = threading.Thread(target=process_voice, daemon=True)
        self.voice_thread.start()
    
    def stop_voice_recognition(self):
        """Остановка распознавания голоса"""
        if not self.is_voice_active:
            return
        
        # Останавливаем обработчик
        if self.voice_handler:
            self.voice_handler.stop_listening()
        
        self.is_voice_active = False
        self.voice_processing_finished.emit()
    
    def update_display(self, text):
        """Обновление отображаемого текста"""
        self.display_text = text
        self.display_updated.emit(text)
    
    def add_to_expression(self, text):
        """Добавление текста к текущему выражению"""
        self.current_expression += text
        self.update_display(self.current_expression)
