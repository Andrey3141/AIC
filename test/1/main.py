# файл: main.py
import tkinter as tk
from calculator_view import CalculatorView
from calculator_viewmodel import CalculatorViewModel

def main():
    """Точка входа, сборка MVVM, запуск приложения"""
    # Создание корневого окна
    root = tk.Tk()
    
    # Создание ViewModel
    viewmodel = CalculatorViewModel()
    
    # Создание View с передачей ViewModel
    view = CalculatorView(root, viewmodel)
    
    # Запуск главного цикла приложения
    root.mainloop()

if __name__ == "__main__":
    main()
