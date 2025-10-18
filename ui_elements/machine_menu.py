import tkinter as tk
import platform


class MachineMenu(object):
    def __init__(self, root, items):
        self.canvas = tk.Canvas(root, width=500, height=150, bg='#000000')  # Increased height from 80 to 150
        self.canvas.place(x=450, y=720)
        self.buttons = create_buttons(self.canvas, items)
        create_menu(self.buttons)
    
    def disable_buttons(self):
        """Disable all buttons"""
        for button in self.buttons:
            button.config(state="disabled")


def create_buttons(canvas, items):
    buttons = []
    # Use tkmacosx on macOS for better button styling
    if platform.system() == "Darwin":
        try:
            from tkmacosx import Button as MacButton
            ButtonClass = MacButton
        except ImportError:
            ButtonClass = tk.Button
    else:
        ButtonClass = tk.Button
    
    for item in items:
        (text, action) = item
        buttons.append(ButtonClass(canvas, text=text, height=60, width=200,
                                 bg="#000000", fg="#00ff00", relief=tk.RAISED, bd=3,
                                 bordercolor="#00ff00", highlightcolor="#00ff00",
                                 activebackground="#111111", activeforeground="#00ff00",
                                 font=("Courier New", 14, "bold"), cursor="hand2",
                                 command=action))
    return buttons


def create_menu(buttons):
    for button in buttons:
        button.pack(side=tk.LEFT, padx=15)  # Increased padding from 10 to 15
