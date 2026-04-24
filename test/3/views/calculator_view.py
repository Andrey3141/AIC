# файл: views/calculator_view.py
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                                QGridLayout, QPushButton, QLineEdit)
from PySide6.QtCore import Qt, Slot

class CalculatorView(QMainWindow):
    """View для калькулятора с Excel-стилем"""
    
    def __init__(self, view_model):
        super().__init__()
        self.view_model = view_model
        self.setup_ui()
        self.bind_commands()
        
        # Подключаем сигналы ViewModel
        self.view_model.display_updated.connect(self.update_display_slot)
        self.view_model.error_occurred.connect(self.show_error)
        self.view_model.voice_processing_started.connect(self.on_voice_started)
        self.view_model.voice_processing_finished.connect(self.on_voice_finished)
        
        self.setWindowTitle("Калькулятор Excel-стиль с голосовым вводом")
        self.setFixedSize(400, 500)
    
    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # Строка формул (как в Excel)
        self.formula_line = QLineEdit()
        self.formula_line.setPlaceholderText("Введите выражение или используйте голос...")
        self.formula_line.setStyleSheet("""
            QLineEdit {
                font-size: 18px;
                padding: 10px;
                border: 2px solid #ccc;
                border-radius: 5px;
                min-height: 40px;
            }
        """)
        main_layout.addWidget(self.formula_line)
        
        # Сетка кнопок 5x5
        self.button_grid = QGridLayout()
        main_layout.addLayout(self.button_grid)
        
        # Определяем кнопки согласно ТЗ (сетка 5x5)
        buttons = [
            ['1', '2', '3', '+', '('],
            ['4', '5', '6', '-', ')'],
            ['7', '8', '9', '*', 'Голос'],
            ['0', '.', '/', '=', 'C']
        ]
        
        # Создаем кнопки
        self.buttons = {}
        for row, row_buttons in enumerate(buttons):
            for col, btn_text in enumerate(row_buttons):
                button = QPushButton(btn_text)
                button.setStyleSheet("""
                    QPushButton {
                        font-size: 16px;
                        padding: 15px;
                        margin: 2px;
                        border: 1px solid #999;
                        border-radius: 3px;
                        background-color: #f0f0f0;
                    }
                    QPushButton:hover {
                        background-color: #e0e0e0;
                    }
                    QPushButton:pressed {
                        background-color: #d0d0d0;
                    }
                """)
                self.button_grid.addWidget(button, row, col)
                self.buttons[btn_text] = button
        
        self.formula_line.setFocus()
    
    def bind_commands(self):
        """Привязка команд к кнопкам"""
        # Цифры
        for digit in '0123456789':
            if digit in self.buttons:
                self.buttons[digit].clicked.connect(
                    lambda checked, d=digit: self.view_model.on_number_clicked(d)
                )
        
        # Операторы
        operators = {'+', '-', '*', '/', '(', ')'}
        for op in operators:
            if op in self.buttons:
                self.buttons[op].clicked.connect(
                    lambda checked, o=op: self.view_model.on_operator_clicked(o)
                )
        
        # Кнопка равно
        if '=' in self.buttons:
            self.buttons['='].clicked.connect(self.on_equal_clicked)
        
        # Кнопка очистки
        if 'C' in self.buttons:
            self.buttons['C'].clicked.connect(self.view_model.on_clear_clicked)
        
        # Кнопка голосового ввода
        if 'Голос' in self.buttons:
            self.buttons['Голос'].clicked.connect(self.view_model.on_voice_input_triggered)
        
        # Кнопка десятичной точки
        if '.' in self.buttons:
            self.buttons['.'].clicked.connect(
                lambda checked: self.view_model.on_operator_clicked('.')
            )
        
        # Подключаем ввод через строку формул (Excel-стиль)
        self.formula_line.returnPressed.connect(self.on_formula_entered)
        self.formula_line.textChanged.connect(self.on_formula_text_changed)
    
    def on_equal_clicked(self):
        """Обработка нажатия кнопки ="""
        # В Excel-стиле при нажатии = вычисляется содержимое строки формул
        expression = self.formula_line.text()
        self.view_model.evaluate_from_formula_line(expression)
    
    def on_formula_entered(self):
        """Обработка ввода формулы в строку (нажатие Enter)"""
        expression = self.formula_line.text()
        self.view_model.evaluate_from_formula_line(expression)
    
    def on_formula_text_changed(self, text):
        """
        Синхронизация строки формул с current_expression
        При ручном вводе в строку обновляем выражение в ViewModel
        """
        self.view_model.set_expression_from_view(text)
    
    @Slot(str)
    def update_display_slot(self, value):
        """Обновление отображения"""
        # Обновляем строку формул
        self.formula_line.setText(value)
    
    @Slot(str)
    def show_error(self, message):
        """Отображение ошибки"""
        self.formula_line.setText(f"Ошибка: {message}")
        # Таймер для очистки сообщения об ошибке через 2 секунды
        from PySide6.QtCore import QTimer
        QTimer.singleShot(2000, lambda: self.formula_line.setText(""))
    
    @Slot()
    def on_voice_started(self):
        """Обработка начала голосового ввода"""
        self.buttons['Голос'].setStyleSheet("""
            QPushButton {
                font-size: 16px;
                padding: 15px;
                margin: 2px;
                border: 1px solid #999;
                border-radius: 3px;
                background-color: #ff9999;
            }
        """)
        self.formula_line.setPlaceholderText("Слушаю... Говорите... (нажмите Голос для остановки)")
    
    @Slot()
    def on_voice_finished(self):
        """Обработка завершения голосового ввода"""
        self.buttons['Голос'].setStyleSheet("""
            QPushButton {
                font-size: 16px;
                padding: 15px;
                margin: 2px;
                border: 1px solid #999;
                border-radius: 3px;
                background-color: #f0f0f0;
            }
        """)
        self.formula_line.setPlaceholderText("Введите выражение или используйте голос...")
