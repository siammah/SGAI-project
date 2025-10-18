import tkinter as tk
import os
import platform
from PIL import Image, ImageTk, ImageDraw

def get_button_class():
    """Get the appropriate button class based on platform"""
    if platform.system() == "Darwin":
        try:
            from tkmacosx import Button as MacButton
            return MacButton
        except ImportError:
            return tk.Button
    else:
        return tk.Button

class LaunchScreen:
    def __init__(self, root, on_continue):
        self.root = root
        self.on_continue = on_continue
        width, height = 1280, 800
        
        # Create canvas
        self.canvas = tk.Canvas(self.root, width=width, height=height, highlightthickness=0, bg='#000000')
        self.canvas.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        # Load and display background image
        bg_path = os.path.join(os.path.dirname(__file__), '../ui_elements/graphics/ambulancegraphic2.jpeg')
        bg_path = os.path.abspath(bg_path)
        bg_img = Image.open(bg_path).resize((width, height), Image.Resampling.LANCZOS)
        
        # Create a dark gradient overlay using PIL
        gradient = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        for y in range(height):
            alpha = int(150 + 100 * (y / height))  # Top: 150, Bottom: 250 (darker overlay for better text readability)
            ImageDraw.Draw(gradient).rectangle([(0, y), (width, y+1)], fill=(0, 0, 0, alpha))
        bg_img = bg_img.convert('RGBA')
        blended = Image.alpha_composite(bg_img, gradient)
        self.bg_photo = ImageTk.PhotoImage(blended)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.bg_photo)
        
        # Create story content area
        story_w, story_h = 1000, 600  # Increased from 800x500 to 1000x600
        story_x, story_y = (width - story_w) // 2, (height - story_h) // 2 - 50
        
        # Store coordinates as instance variables for typing animation
        self.story_x = story_x
        self.story_y = story_y
        self.story_w = story_w
        self.story_h = story_h
        
        # Draw a semi-transparent rounded rectangle for the story area
        story_img = Image.new('RGBA', (story_w, story_h), (0, 0, 0, 180))  # Semi-transparent black
        draw = ImageDraw.Draw(story_img)
        radius = 30
        
        # Draw rounded rectangle
        draw.rounded_rectangle([(0, 0), (story_w, story_h)], radius=radius, fill=(0, 0, 0, 180), outline=(0, 255, 0, 255), width=3)
        
        self.story_photo = ImageTk.PhotoImage(story_img)
        self.canvas.create_image(story_x, story_y, anchor=tk.NW, image=self.story_photo)
        
        # Title
        self.canvas.create_text(
            width // 2, story_y + 50,
            text="EMERGENCY RESPONSE MISSION",
            font=("Courier New", 36, "bold"),  # Increased from 32 to 36
            fill="#00ff00",
            anchor=tk.CENTER
        )
        
        # Story text - display directly on canvas instead of scrollable widget
        self.story_text = (
            "You are an emergency response operator in a world devastated by a mysterious outbreak. "
            "Your mission is to coordinate rescue operations and make critical decisions about who to save "
            "and who to leave behind.\n\n"
            
            "The outbreak has created different types of affected individuals:\n"
            "• HEALTHY survivors who need immediate rescue\n"
            "• INJURED victims requiring urgent medical attention\n"
            "• ZOMBIES who may be carriers of the infection\n"
            "• CORPSES that cannot be saved\n\n"
            
            "Your decisions will be evaluated across four critical reputation metrics:\n"
            "• MILITARY: Prioritize law enforcement and eliminate threats\n"
            "• HUMAN RIGHTS ACTIVIST: Focus on humanitarian rescue of all survivors\n"
            "• SCIENTIST: Study zombies to find a cure\n"
            "• MEDIC: Provide medical care to the injured\n\n"
            
            "Time is critical. Your ambulance has limited capacity. "
            "Every decision matters in this race against the outbreak.\n\n"

            "Good Luck." 
        )
        
        # Start typing animation
        self.current_text = ""
        self.text_index = 0
        self.typing_speed = 10  # milliseconds between characters
        self.start_typing_animation()
        
        # Continue button (initially disabled)
        ButtonClass = get_button_class()
        if ButtonClass.__name__ == 'Button':  # tkmacosx Button
            self.continue_btn = ButtonClass(
                self.root, text="CONTINUE", font=("Courier New", 20, "bold"),
                bg="#111111", fg="#666666", relief=tk.RAISED, bd=4, width=200, height=60,  # Dark colors when disabled
                bordercolor="#333333", highlightcolor="#333333",  # Dark border when disabled
                activebackground="#111111", activeforeground="#666666", cursor="hand2",
                command=self.continue_to_start, state=tk.DISABLED  # Initially disabled
            )
        else:  # Regular tk.Button
            self.continue_btn = ButtonClass(
                self.root, text="CONTINUE", font=("Courier New", 20, "bold"),
                bg="#111111", fg="#666666", relief=tk.RAISED, bd=4, width=200, height=60,  # Dark colors when disabled
                activebackground="#111111", activeforeground="#666666", cursor="hand2",
                command=self.continue_to_start, state=tk.DISABLED  # Initially disabled
            )
        
        self._add_hover_effect(self.continue_btn, "#000000", "#111111")
        self.canvas.create_window(width // 2 - 110, story_y + story_h + 30, window=self.continue_btn, anchor=tk.CENTER)
        
        # Skip button (always enabled)
        if ButtonClass.__name__ == 'Button':  # tkmacosx Button
            self.skip_btn = ButtonClass(
                self.root, text="SKIP", font=("Courier New", 20, "bold"),
                bg="#000000", fg="#00ff00", relief=tk.RAISED, bd=4, width=200, height=60,
                bordercolor="#00ff00", highlightcolor="#00ff00",
                activebackground="#111111", activeforeground="#00ff00", cursor="hand2",
                command=self.continue_to_start  # Same function as continue
            )
        else:  # Regular tk.Button
            self.skip_btn = ButtonClass(
                self.root, text="SKIP", font=("Courier New", 20, "bold"),
                bg="#000000", fg="#00ff00", relief=tk.RAISED, bd=4, width=200, height=60,
                activebackground="#111111", activeforeground="#00ff00", cursor="hand2",
                command=self.continue_to_start  # Same function as continue
            )
        
        self._add_hover_effect(self.skip_btn, "#000000", "#111111")
        self.canvas.create_window(width // 2 + 110, story_y + story_h + 30, window=self.skip_btn, anchor=tk.CENTER)

    def _add_hover_effect(self, btn, normal, hover):
        def on_enter(e): btn.config(bg=hover)
        def on_leave(e): btn.config(bg=normal)
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)

    def continue_to_start(self):
        """Continue to the start screen"""
        self.canvas.destroy()
        if self.on_continue:
            self.on_continue() 

    def start_typing_animation(self):
        """Start the typing animation"""
        self.typing_id = self.canvas.create_text(
            self.story_x + self.story_w // 2, self.story_y + 300,
            text="",
            font=("Courier New", 14),
            fill="#00ff00",
            anchor=tk.CENTER,
            width=self.story_w - 100,
            justify=tk.LEFT
        )
        self.type_next_character()

    def type_next_character(self):
        """Type the next character in the animation"""
        if self.text_index < len(self.story_text):
            # Add next character
            self.current_text += self.story_text[self.text_index]
            self.text_index += 1
            
            # Update the text on canvas
            self.canvas.itemconfig(self.typing_id, text=self.current_text)
            
            # Schedule next character
            self.root.after(self.typing_speed, self.type_next_character)
        else:
            # Animation complete, enable continue button with bright appearance
            self.continue_btn.config(
                state=tk.NORMAL,
                bg="#000000",
                fg="#00ff00",
                bordercolor="#00ff00",
                highlightcolor="#00ff00",
                activebackground="#111111",
                activeforeground="#00ff00"
            ) 