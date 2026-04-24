import sys
import math
import re
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QGridLayout, QPushButton, QLabel, 
                             QFrame, QGraphicsOpacityEffect)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, QTimer
from PyQt5.QtGui import QFont, QPalette, QColor, QIcon

class ModernButton(QPushButton):
    """Современная кнопка с анимациями"""
    def __init__(self, text, color="#2C3E50", hover_color="#34495E", text_color="white"):
        super().__init__(text)
        self.default_color = color
        self.hover_color = hover_color
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: {text_color};
                border: none;
                border-radius: 10px;
                font-size: 18px;
                font-weight: bold;
                padding: 15px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            QPushButton:pressed {{
                background-color: {color};
                transform: scale(0.95);
            }}
        """)
        
        # Анимация нажатия
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(100)
        
    def animate_click(self):
        """Анимация при нажатии"""
        original_geo = self.geometry()
        self.animation.setEndValue(QRect(original_geo.x() + 2, 
                                        original_geo.y() + 2,
                                        original_geo.width() - 4,
                                        original_geo.height() - 4))
        self.animation.start()
        QTimer.singleShot(100, lambda: self.setGeometry(original_geo))

class Calculator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Professional Calculator")
        self.setFixedSize(400, 600)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Переменные для вычислений
        self.current_input = ""
        self.result = ""
        self.history = []
        
        self.setup_ui()
        self.setup_animations()
        
    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        # Центральный виджет
        central_widget = QWidget()
        central_widget.setStyleSheet("""
            QWidget {
                background-color: #1E1E1E;
                border-radius: 20px;
            }
        """)
        self.setCentralWidget(central_widget)
        
        # Главный layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        central_widget.setLayout(main_layout)
        
        # Верхняя панель с кнопкой закрытия
        top_bar = QHBoxLayout()
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #E74C3C;
                color: white;
                border: none;
                border-radius: 15px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #C0392B;
            }
        """)
        close_btn.clicked.connect(self.close)
        
        minimize_btn = QPushButton("−")
        minimize_btn.setFixedSize(30, 30)
        minimize_btn.setStyleSheet("""
            QPushButton {
                background-color: #F39C12;
                color: white;
                border: none;
                border-radius: 15px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #E67E22;
            }
        """)
        minimize_btn.clicked.connect(self.showMinimized)
        
        top_bar.addStretch()
        top_bar.addWidget(minimize_btn)
        top_bar.addWidget(close_btn)
        main_layout.addLayout(top_bar)
        
        # Поле ввода и вывода
        self.display_frame = QFrame()
        self.display_frame.setStyleSheet("""
            QFrame {
                background-color: #2C3E50;
                border-radius: 15px;
                padding: 10px;
            }
        """)
        display_layout = QVBoxLayout()
        self.display_frame.setLayout(display_layout)
        
        self.input_label = QLabel("0")
        self.input_label.setAlignment(Qt.AlignRight)
        self.input_label.setFont(QFont("Arial", 24, QFont.Bold))
        self.input_label.setStyleSheet("color: #ECF0F1; background-color: transparent;")
        
        self.result_label = QLabel("")
        self.result_label.setAlignment(Qt.AlignRight)
        self.result_label.setFont(QFont("Arial", 16))
        self.result_label.setStyleSheet("color: #95A5A6; background-color: transparent;")
        
        display_layout.addWidget(self.result_label)
        display_layout.addWidget(self.input_label)
        main_layout.addWidget(self.display_frame)
        
        # История вычислений
        self.history_label = QLabel("")
        self.history_label.setAlignment(Qt.AlignRight)
        self.history_label.setFont(QFont("Arial", 10))
        self.history_label.setStyleSheet("color: #7F8C8D; background-color: transparent;")
        main_layout.addWidget(self.history_label)
        
        # Клавиатура калькулятора
        keyboard_layout = QGridLayout()
        keyboard_layout.setSpacing(10)
        
        # Кнопки
        buttons = [
            ('C', '#E74C3C', '#C0392B'), ('⌫', '#E67E22', '#D35400'), ('%', '#3498DB', '#2980B9'), ('÷', '#3498DB', '#2980B9'),
            ('7', '#34495E', '#2C3E50'), ('8', '#34495E', '#2C3E50'), ('9', '#34495E', '#2C3E50'), ('×', '#3498DB', '#2980B9'),
            ('4', '#34495E', '#2C3E50'), ('5', '#34495E', '#2C3E50'), ('6', '#34495E', '#2C3E50'), ('−', '#3498DB', '#2980B9'),
            ('1', '#34495E', '#2C3E50'), ('2', '#34495E', '#2C3E50'), ('3', '#34495E', '#2C3E50'), ('+', '#3498DB', '#2980B9'),
            ('±', '#34495E', '#2C3E50'), ('0', '#34495E', '#2C3E50'), ('.', '#34495E', '#2C3E50'), ('=', '#27AE60', '#229954')
        ]
        
        positions = [(i, j) for i in range(5) for j in range(4)]
        
        for (text, color, hover_color), position in zip(buttons, positions):
            button = ModernButton(text, color, hover_color)
            button.clicked.connect(lambda checked, t=text: self.button_click(t))
            keyboard_layout.addWidget(button, position[0], position[1])
            
        main_layout.addLayout(keyboard_layout)
        
        # Научные функции
        scientific_layout = QHBoxLayout()
        scientific_buttons = ['sin', 'cos', 'tan', '√', 'x²', 'xʸ', 'log', 'ln', 'π', 'e']
        
        for text in scientific_buttons:
            button = ModernButton(text, "#8E44AD", "#9B59B6", "white")
            button.setFixedHeight(40)
            button.clicked.connect(lambda checked, t=text: self.scientific_function(t))
            scientific_layout.addWidget(button)
            
        main_layout.addLayout(scientific_layout)
        
    def setup_animations(self):
        """Настройка анимаций"""
        # Анимация появления
        opacity_effect = QGraphicsOpacityEffect()
        self.centralWidget().setGraphicsEffect(opacity_effect)
        self.fade_animation = QPropertyAnimation(opacity_effect, b"opacity")
        self.fade_animation.setDuration(500)
        self.fade_animation.setStartValue(0)
        self.fade_animation.setEndValue(1)
        self.fade_animation.setEasingCurve(QEasingCurve.InOutCubic)
        self.fade_animation.start()
        
    def button_click(self, value):
        """Обработка нажатий кнопок"""
        if value == 'C':
            self.current_input = ""
            self.result = ""
            self.update_display()
        elif value == '⌫':
            self.current_input = self.current_input[:-1]
            self.update_display()
        elif value == '=':
            self.calculate()
        elif value == '±':
            if self.current_input and self.current_input[0] == '-':
                self.current_input = self.current_input[1:]
            else:
                self.current_input = '-' + self.current_input
            self.update_display()
        else:
            # Замена символов операций
            if value == '÷':
                value = '/'
            elif value == '×':
                value = '*'
            elif value == '−':
                value = '-'
            
            self.current_input += value
            self.update_display()
            
            # Предварительный просмотр результата
            self.preview_result()
            
    def scientific_function(self, func):
        """Научные функции"""
        try:
            if self.current_input:
                num = float(self.current_input)
                
                if func == 'sin':
                    result = math.sin(math.radians(num))
                elif func == 'cos':
                    result = math.cos(math.radians(num))
                elif func == 'tan':
                    result = math.tan(math.radians(num))
                elif func == '√':
                    result = math.sqrt(num)
                elif func == 'x²':
                    result = num ** 2
                elif func == 'log':
                    result = math.log10(num)
                elif func == 'ln':
                    result = math.log(num)
                elif func == 'π':
                    result = math.pi
                elif func == 'e':
                    result = math.e
                elif func == 'xʸ':
                    self.current_input += '^'
                    self.update_display()
                    return
                    
                self.current_input = str(result)
                self.update_display()
                self.add_to_history(f"{func}({num})", result)
                
        except Exception as e:
            self.input_label.setText("Error")
            QTimer.singleShot(1000, self.clear_error)
            
    def calculate(self):
        """Вычисление выражения"""
        try:
            # Замена ^ на ** для возведения в степень
            expression = self.current_input.replace('^', '**')
            
            # Безопасное вычисление
            result = eval(expression)
            
            # Округление до 10 знаков
            if isinstance(result, float):
                result = round(result, 10)
                # Убираем .0 для целых чисел
                if result.is_integer():
                    result = int(result)
                    
            self.result = str(result)
            self.add_to_history(self.current_input, result)
            self.current_input = str(result)
            self.update_display()
            
        except Exception as e:
            self.input_label.setText("Error")
            QTimer.singleShot(1000, self.clear_error)
            
    def preview_result(self):
        """Предварительный просмотр результата"""
        try:
            expression = self.current_input.replace('^', '**')
            result = eval(expression)
            if isinstance(result, float):
                result = round(result, 10)
                if result.is_integer():
                    result = int(result)
            self.result_label.setText(f"= {result}")
        except:
            self.result_label.setText("")
            
    def add_to_history(self, expression, result):
        """Добавление в историю"""
        self.history.append(f"{expression} = {result}")
        if len(self.history) > 3:
            self.history.pop(0)
        
        history_text = " | ".join(self.history)
        self.history_label.setText(history_text)
        
    def update_display(self):
        """Обновление дисплея"""
        if not self.current_input:
            self.input_label.setText("0")
        else:
            self.input_label.setText(self.current_input)
            
    def clear_error(self):
        """Очистка ошибки"""
        self.current_input = ""
        self.update_display()
        self.result_label.setText("")
        
    def mousePressEvent(self, event):
        """Для перемещения окна"""
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
            
    def mouseMoveEvent(self, event):
        """Для перемещения окна"""
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Установка глобального стиля
    app.setStyle('Fusion')
    
    calculator = Calculator()
    calculator.show()
    
    sys.exit(app.exec_())
