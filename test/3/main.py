# файл: main.py
import sys
import os
from PySide6.QtWidgets import QApplication
from models.calculator_model import CalculatorModel
from viewmodels.calculator_viewmodel import CalculatorViewModel
from views.calculator_view import CalculatorView
from voice.voice_input_handler import VoiceInputHandler
from voice.command_parser import CommandParser

def main():
    app = QApplication(sys.argv)
    
    # Инициализация модели и ViewModel
    model = CalculatorModel()
    view_model = CalculatorViewModel(model)
    
    # Путь к модели Vosk (проверяем наличие)
    model_path = "model/vosk-model-small-ru-0.22"
    if not os.path.exists(model_path):
        print(f"Предупреждение: Модель Vosk не найдена по пути {model_path}")
        print("Пожалуйста, скачайте модель и распакуйте её в папку model/")
        voice_handler = None
    else:
        voice_handler = VoiceInputHandler(model_path)
    
    command_parser = CommandParser()
    
    # Создание View
    view = CalculatorView(view_model)
    
    # Подключение голосового ввода к ViewModel
    if voice_handler:
        view_model.set_voice_handler(voice_handler)
    view_model.set_command_parser(command_parser)
    
    # Показываем окно
    view.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
