# файл: aic/main.py
#!/usr/bin/env python3
"""
AIC - Artificial Intelligence Company
Главный модуль для запуска приложения
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aic.ui.main_window import AICApp
from aic.utils.file_utils import FileUtils
import tkinter as tk

def check_required_files():
    """Проверка наличия необходимых файлов при запуске"""
    prompts_folder = "prompts"
    required_files = ["Boss.txt", "Analyst.txt", "Chief_developer.txt", "Ordinary_developer.txt"]
    
    print("=" * 50)
    print("AIC v10.3 - Проверка файлов конфигурации")
    print("=" * 50)
    
    FileUtils.ensure_folder(prompts_folder)
    
    all_exists = True
    for filename in required_files:
        file_path = os.path.join(prompts_folder, filename)
        if os.path.exists(file_path):
            print(f"✅ {filename} - найден")
        else:
            print(f"❌ {filename} - НЕ НАЙДЕН (создайте файл в папке {prompts_folder}/)")
            all_exists = False
    
    print("=" * 50)
    
    if not all_exists:
        print("ВНИМАНИЕ: Некоторые файлы отсутствуют!")
        print("Создайте недостающие файлы в папке 'prompts/' перед запуском.")
        print("Для продолжения нажмите Enter...")
        input()
    
    return all_exists

def main():
    check_required_files()
    
    root = tk.Tk()
    app = AICApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
