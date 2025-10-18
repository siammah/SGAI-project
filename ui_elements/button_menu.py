import tkinter as tk
import os
from PIL import ImageTk, Image
import platform

from gameplay.enums import ActionCost


class ButtonMenu(object):
    def __init__(self, root, items):
        self.canvas = tk.Canvas(root, width=500, height=400)  # Removed bg='#000000'
        self.canvas.place(x=0, y=150)  # Moved further left to avoid overlap
        self.buttons = create_buttons(self.canvas, items)
        create_menu(self.buttons)

    def disable_buttons(self, remaining_time, remaining_humanoids, at_capacity):
        # First, enable all buttons
        for i in range(0, len(self.buttons)):
            self.buttons[i].config(state="normal")
        
        # Then disable buttons based on conditions
        if remaining_humanoids == 0 or remaining_time <= 0:
            for i in range(0, len(self.buttons)):
                self.buttons[i].config(state="disabled")
        else:
            #  Not enough time left? Disable action
            if (remaining_time - ActionCost.SCRAM.value) < ActionCost.SKIP.value:
                self.buttons[0].config(state="disabled")
            if (remaining_time - ActionCost.SCRAM.value) < ActionCost.SQUISH.value:
                self.buttons[1].config(state="disabled")
            if (remaining_time - ActionCost.SCRAM.value) < ActionCost.SAVE.value:
                self.buttons[2].config(state="disabled")
            if at_capacity:
                self.buttons[0].config(state="disabled")
                self.buttons[1].config(state="disabled")
                self.buttons[2].config(state="disabled")
        if remaining_humanoids == 0 or remaining_time <= 0:
            for i in range(0, len(self.buttons)):
                self.buttons[i].config(state="disabled")  


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
        button = ButtonClass(
            canvas, 
            text=text, 
            height=60,  # Increased from 3 to 60 (pixels for tkmacosx)
            width=242,  # Increased from 20 to 200 (pixels for tkmacosx)
            bg="#000000",  # Black background
            fg="#00ff00",  # Neon green text
            relief=tk.RAISED,
            bd=3,  # Border width
            bordercolor="#00ff00",  # Neon green border
            highlightcolor="#00ff00",  # Neon green highlight
            activebackground="#111111",  # Slightly lighter black when clicked
            activeforeground="#00ff00",  # Keep neon green text when clicked
            font=("Courier New", 18, "bold"),  # Font size
            cursor="hand2",
            command=action
        )
        
        buttons.append(button)
    return buttons


def create_menu(buttons):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'graphics', 'logo7trans.png')
    img = Image.open(path).resize((300, 50), Image.LANCZOS)
    

    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    

    rgba = img.split()
    alpha = rgba[3].point(lambda x: int(x * 0.8))  # 80% opacity
    img_with_opacity = Image.merge('RGBA', rgba[:3] + (alpha,))
    
    logo = ImageTk.PhotoImage(img_with_opacity)
    label = tk.Label(image=logo)
    label.image = logo

    # Position image
    label.place(x=30, y=30)

    for button in buttons:
        button.pack(side=tk.TOP, pady=10)  # Increased padding from 10 to 15
