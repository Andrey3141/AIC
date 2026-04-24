# файл: calculator_view.py
import tkinter as tk
from tkinter import ttk, font
from calculator_viewmodel import CalculatorViewModel
from animation_controller import AnimationController

class CalculatorView:
    """Главное окно, виджеты, тёмная/светлая тема, анимации"""
    
    def __init__(self, root: tk.Tk, viewmodel: CalculatorViewModel):
        self.root = root
        self.viewmodel = viewmodel
        self.animation = AnimationController()
        
        # Настройка главного окна
        self.root.title("Калькулятор")
        self.root.geometry("400x600")
        self.root.resizable(False, False)
        
        # Цветовые темы
        self.themes = {
            "dark": {
                "bg": "#1e1e1e",
                "fg": "#ffffff",
                "button_bg": "#2d2d2d",
                "button_fg": "#ffffff",
                "button_active": "#3d3d3d",
                "display_bg": "#252525",
                "display_fg": "#ffffff",
                "special_bg": "#4a4a4a"
            },
            "light": {
                "bg": "#f0f0f0",
                "fg": "#000000",
                "button_bg": "#ffffff",
                "button_fg": "#000000",
                "button_active": "#e0e0e0",
                "display_bg": "#ffffff",
                "display_fg": "#000000",
                "special_bg": "#d0d0d0"
            }
        }
        
        self.setup_ui()
        self.viewmodel.set_update_callback(self.update_display)
        self.setup_keyboard_bindings()
        
        # Стилизация окна
        self.apply_theme()
    
    def setup_ui(self):
        """Создание интерфейса"""
        # Дисплей для выражения
        self.display_frame = tk.Frame(self.root)
        self.display_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.expression_var = tk.StringVar()
        self.expression_var.set("0")
        self.display = tk.Label(
            self.display_frame,
            textvariable=self.expression_var,
            font=("Arial", 24),
            anchor="e",
            justify=tk.RIGHT
        )
        self.display.pack(fill=tk.BOTH, expand=True)
        
        # Дисплей для результата
        self.result_var = tk.StringVar()
        self.result_var.set("")
        self.result_display = tk.Label(
            self.display_frame,
            textvariable=self.result_var,
            font=("Arial", 14),
            anchor="e",
            justify=tk.RIGHT
        )
        self.result_display.pack(fill=tk.BOTH, expand=True)
        
        # Кнопки
        self.buttons_frame = tk.Frame(self.root)
        self.buttons_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        buttons = [
            ['C', '⌫', '(', ')', '/'],
            ['7', '8', '9', '*', '√'],
            ['4', '5', '6', '-', '^'],
            ['1', '2', '3', '+', '%'],
            ['0', '.', '±', '=', 'MC'],
            ['M+', 'M-', 'MR', 'Hist', 'Theme']
        ]
        
        self.buttons = {}
        for i, row in enumerate(buttons):
            for j, btn_text in enumerate(row):
                btn = tk.Button(
                    self.buttons_frame,
                    text=btn_text,
                    font=("Arial", 14),
                    command=lambda x=btn_text: self.button_click(x)
                )
                btn.grid(row=i, column=j, padx=5, pady=5, sticky="nsew")
                self.buttons[btn_text] = btn
                
                # Настройка веса колонок
                self.buttons_frame.grid_columnconfigure(j, weight=1)
            self.buttons_frame.grid_rowconfigure(i, weight=1)
        
        # История (скрыта по умолчанию)
        self.history_frame = tk.Frame(self.root)
        self.history_label = tk.Label(
            self.history_frame,
            text="История",
            font=("Arial", 16)
        )
        self.history_label.pack()
        
        self.history_listbox = tk.Listbox(
            self.history_frame,
            font=("Arial", 10),
            height=15
        )
        self.history_listbox.pack(fill=tk.BOTH, expand=True)
        
        self.history_close_btn = tk.Button(
            self.history_frame,
            text="Закрыть",
            command=self.hide_history
        )
        self.history_close_btn.pack()
        
        self.history_visible = False
    
    def button_click(self, value: str):
        """Обработка нажатия кнопок с анимацией"""
        # Анимация нажатия
        button = self.buttons.get(value)
        if button:
            self.animation.animate_press(button)
        
        # Обработка специальных кнопок
        if value == 'C':
            self.viewmodel.clear_expression()
        elif value == '⌫':
            self.viewmodel.backspace()
        elif value == '=':
            self.viewmodel.calculate()
        elif value == '±':
            current = self.viewmodel.get_expression()
            if current:
                if current[0] == '-':
                    self.viewmodel.clear_expression()
                    self.viewmodel.append_to_expression(current[1:])
                else:
                    self.viewmodel.clear_expression()
                    self.viewmodel.append_to_expression('-' + current)
        elif value == '√':
            self.viewmodel.append_to_expression('sqrt(')
        elif value == '^':
            self.viewmodel.append_to_expression('**')
        elif value == 'MC':
            self.viewmodel.memory_clear()
        elif value == 'M+':
            self.viewmodel.memory_add()
        elif value == 'M-':
            self.viewmodel.memory_subtract()
        elif value == 'MR':
            self.viewmodel.memory_recall()
        elif value == 'Hist':
            self.toggle_history()
        elif value == 'Theme':
            self.viewmodel.toggle_theme()
            self.apply_theme()
        else:
            self.viewmodel.append_to_expression(value)
    
    def update_display(self):
        """Обновление дисплея"""
        expression = self.viewmodel.get_expression()
        result = self.viewmodel.get_result()
        
        self.expression_var.set(expression if expression else "0")
        self.result_var.set(result)
        
        # Обновление истории
        self.update_history_display()
        
        # Адаптация размера шрифта при длинных выражениях
        if len(expression) > 20:
            self.display.config(font=("Arial", 18))
        else:
            self.display.config(font=("Arial", 24))
    
    def update_history_display(self):
        """Обновление отображения истории"""
        self.history_listbox.delete(0, tk.END)
        history = self.viewmodel.get_history()
        for entry in reversed(history[-10:]):
            self.history_listbox.insert(
                tk.END,
                f"{entry['expression']} = {entry['result']}"
            )
    
    def toggle_history(self):
        """Показ/скрытие истории"""
        if self.history_visible:
            self.hide_history()
        else:
            self.show_history()
    
    def show_history(self):
        """Показ панели истории"""
        self.history_frame.place(x=0, y=0, width=400, height=600)
        self.history_visible = True
        self.update_history_display()
    
    def hide_history(self):
        """Скрытие панели истории"""
        self.history_frame.place_forget()
        self.history_visible = False
    
    def apply_theme(self):
        """Применение текущей темы"""
        theme = self.themes[self.viewmodel.get_current_theme()]
        
        self.root.configure(bg=theme["bg"])
        self.display_frame.configure(bg=theme["bg"])
        self.display.configure(bg=theme["display_bg"], fg=theme["display_fg"])
        self.result_display.configure(bg=theme["display_bg"], fg=theme["display_fg"])
        self.buttons_frame.configure(bg=theme["bg"])
        self.history_frame.configure(bg=theme["bg"])
        self.history_label.configure(bg=theme["bg"], fg=theme["fg"])
        self.history_listbox.configure(bg=theme["display_bg"], fg=theme["fg"])
        self.history_close_btn.configure(
            bg=theme["button_bg"],
            fg=theme["button_fg"],
            activebackground=theme["button_active"]
        )
        
        for btn in self.buttons.values():
            btn.configure(
                bg=theme["button_bg"],
                fg=theme["button_fg"],
                activebackground=theme["button_active"]
            )
    
    def setup_keyboard_bindings(self):
        """Настройка обработки клавиатуры"""
        self.root.bind('<Key>', self.viewmodel.handle_keyboard)
