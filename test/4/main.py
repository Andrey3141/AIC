# calculator.py

import tkinter as tk
from tkinter import ttk
import math
import threading
import time

class Calculator:
    def __init__(self, root):
        self.root = root
        self.root.title("Professional Calculator")
        self.root.geometry("400x600")
        self.root.resizable(False, False)
        self.root.configure(bg="#2C3E50")

        # Variables
        self.expression = ""
        self.result_var = tk.StringVar()
        self.result_var.set("0")

        # Create UI
        self.create_widgets()

    def create_widgets(self):
        # Display frame
        display_frame = tk.Frame(self.root, bg="#2C3E50")
        display_frame.pack(fill=tk.X, padx=10, pady=10)

        # Display entry
        self.display = tk.Entry(
            display_frame,
            textvariable=self.result_var,
            font=("Arial", 24, "bold"),
            justify="right",
            bd=0,
            bg="#34495E",
            fg="white",
            insertbackground="white"
        )
        self.display.pack(fill=tk.X, ipady=15)

        # Buttons frame
        buttons_frame = tk.Frame(self.root, bg="#2C3E50")
        buttons_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Button layout
        buttons = [
            ['C', '(', ')', '/'],
            ['7', '8', '9', '*'],
            ['4', '5', '6', '-'],
            ['1', '2', '3', '+'],
            ['.', '0', '^', '√'],
            ['=', 'DEL', 'AC', '']
        ]

        # Create buttons
        for i, row in enumerate(buttons):
            for j, btn_text in enumerate(row):
                if btn_text == "":
                    continue

                btn = tk.Button(
                    buttons_frame,
                    text=btn_text,
                    font=("Arial", 16, "bold"),
                    bg="#3498DB" if btn_text not in ['C', 'DEL', 'AC', '='] else "#E74C3C" if btn_text in ['C', 'DEL', 'AC'] else "#2ECC71",
                    fg="white",
                    activebackground="#34495E",
                    activeforeground="white",
                    relief=tk.RAISED,
                    bd=2,
                    command=lambda t=btn_text: self.on_button_click(t),
                    highlightthickness=0
                )
                
                # Bind events for button animations
                btn.bind("<Button-1>", lambda e, b=btn: self.button_press(b))
                btn.bind("<ButtonRelease-1>", lambda e, b=btn: self.button_release(b))

                btn.grid(row=i, column=j, sticky="nsew", padx=2, pady=2)

        # Configure grid weights for responsive design
        for i in range(6):
            buttons_frame.rowconfigure(i, weight=1)
        for j in range(4):
            buttons_frame.columnconfigure(j, weight=1)

        # Bind keyboard events
        self.root.bind('<Key>', self.key_press)
        self.root.focus_set()

    def button_press(self, btn):
        """Animate button press"""
        original_bg = btn.cget('bg')
        btn.config(bg="#1ABC9C")  # Change to a lighter color on press
        
        # Create a small animation effect
        def animate():
            btn.config(relief=tk.SUNKEN)
            
        self.root.after(50, animate)

    def button_release(self, btn):
        """Animate button release"""
        original_bg = btn.cget('bg')
        if btn.cget('text') not in ['C', 'DEL', 'AC', '=']:
            btn.config(bg="#3498DB")
        elif btn.cget('text') in ['C', 'DEL', 'AC']:
            btn.config(bg="#E74C3C")
        else:
            btn.config(bg="#2ECC71")
            
        # Restore normal state
        def restore():
            btn.config(relief=tk.RAISED)
            
        self.root.after(50, restore)

    def key_press(self, event):
        """Handle keyboard input"""
        key = event.char
        if key in '0123456789+-*/.()^':
            self.append(key)
        elif key == '\r':  # Enter key
            self.calculate()
        elif key == '\x08':  # Backspace
            self.delete()
        elif key == '\x1b':  # Escape
            self.all_clear()

    def on_button_click(self, char):
        if char == 'C':
            self.clear()
        elif char == 'AC':
            self.all_clear()
        elif char == 'DEL':
            self.delete()
        elif char == '=':
            self.calculate()
        else:
            self.append(char)

    def append(self, char):
        # Handle special cases for operations
        if char in ['+', '-', '*', '/', '^', '√']:
            if self.expression and self.expression[-1] in ['+', '-', '*', '/', '^']:
                return  # Prevent consecutive operators
            if char == '√':
                self.expression += 'math.sqrt('
            else:
                self.expression += char
        elif char == '(':
            self.expression += char
        elif char == ')':
            self.expression += char
        elif char == '.':
            if not self.expression or self.expression[-1] in ['+', '-', '*', '/', '^', '(']:
                self.expression += '0'
            self.expression += char
        else:
            self.expression += char

        # Update display with current expression
        self.result_var.set(self.expression)

    def clear(self):
        if self.expression:
            self.expression = self.expression[:-1]
            self.result_var.set(self.expression)

    def delete(self):
        self.expression = ""
        self.result_var.set("0")

    def all_clear(self):
        self.expression = ""
        self.result_var.set("0")

    def calculate(self):
        try:
            # Replace math functions with their Python equivalents
            expr = self.expression.replace('^', '**')
            expr = expr.replace('√', 'math.sqrt')

            # Check for division by zero
            if '/0' in expr or '/ 0' in expr:
                raise ZeroDivisionError("Division by zero")

            # Evaluate expression safely
            result = eval(expr)
            
            # Format result to avoid scientific notation for large numbers
            if isinstance(result, float):
                if result.is_integer():
                    result = int(result)
                else:
                    result = round(result, 10)

            self.result_var.set(str(result))
            self.expression = str(result)
        except ZeroDivisionError:
            self.result_var.set("Error: Division by zero")
            self.expression = ""
        except Exception as e:
            self.result_var.set("Error")
            self.expression = ""

# Main execution
if __name__ == "__main__":
    root = tk.Tk()
    app = Calculator(root)
    root.mainloop()

