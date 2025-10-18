import tkinter as tk
import os
import platform
import datetime
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

class LoginDialog:
    def __init__(self, parent):
        self.operator_name = ""
        self.player_name = ""
        self.result = False
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Log In")
        self.dialog.geometry("400x250")
        self.dialog.configure(bg="#000000")
        self.dialog.resizable(False, False)
        
        # Center the dialog
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Title
        title_label = tk.Label(self.dialog, text="Log In", font=("Courier New", 24, "bold"), fg="#00ff00", bg="#000000")
        title_label.pack(pady=20)
        
        # Operator name input
        operator_frame = tk.Frame(self.dialog, bg="#000000")
        operator_frame.pack(pady=10)
        operator_label = tk.Label(operator_frame, text="Operator Name:", font=("Courier New", 14), fg="#00ff00", bg="#000000")
        operator_label.pack()
        self.operator_entry = tk.Entry(operator_frame, font=("Courier New", 12), width=25, bg="#111111", fg="#00ff00", insertbackground="#00ff00")
        self.operator_entry.pack(pady=5)
        
        # Player name input
        player_frame = tk.Frame(self.dialog, bg="#000000")
        player_frame.pack(pady=10)
        player_label = tk.Label(player_frame, text="Player Name:", font=("Courier New", 14), fg="#00ff00", bg="#000000")
        player_label.pack()
        self.player_entry = tk.Entry(player_frame, font=("Courier New", 12), width=25, bg="#111111", fg="#00ff00", insertbackground="#00ff00")
        self.player_entry.pack(pady=5)
        
        # Buttons
        button_frame = tk.Frame(self.dialog, bg="#000000")
        button_frame.pack(pady=20)
        
        ButtonClass = get_button_class()
        if ButtonClass.__name__ == 'Button':  # tkmacosx Button
            login_btn = ButtonClass(
                button_frame, text="Log In", font=("Courier New", 12, "bold"),
                bg="#000000", fg="#00ff00", relief=tk.RAISED, bd=3, width=15, height=35,
                bordercolor="#00ff00", highlightcolor="#00ff00",
                activebackground="#111111", activeforeground="#00ff00", cursor="hand2",
                command=self.login
            )
            cancel_btn = ButtonClass(
                button_frame, text="Cancel", font=("Courier New", 12, "bold"),
                bg="#000000", fg="#00ff00", relief=tk.RAISED, bd=3, width=15, height=35,
                bordercolor="#00ff00", highlightcolor="#00ff00",
                activebackground="#111111", activeforeground="#00ff00", cursor="hand2",
                command=self.cancel
            )
        else:  # Regular tk.Button
            login_btn = ButtonClass(
                button_frame, text="Log In", font=("Courier New", 12, "bold"),
                bg="#000000", fg="#00ff00", relief=tk.RAISED, bd=3, width=15, height=35,
                activebackground="#111111", activeforeground="#00ff00", cursor="hand2",
                command=self.login
            )
            cancel_btn = ButtonClass(
                button_frame, text="Cancel", font=("Courier New", 12, "bold"),
                bg="#000000", fg="#00ff00", relief=tk.RAISED, bd=3, width=15, height=35,
                activebackground="#111111", activeforeground="#00ff00", cursor="hand2",
                command=self.cancel
            )
        
        login_btn.pack(side=tk.LEFT, padx=10)
        cancel_btn.pack(side=tk.LEFT, padx=10)
        
        # Focus on first entry
        self.operator_entry.focus()
        
        # Bind Enter key to login
        self.dialog.bind("<Return>", lambda e: self.login())
        self.dialog.bind("<Escape>", lambda e: self.cancel())
        
        # Wait for dialog to close
        self.dialog.wait_window()
    
    def login(self):
        self.operator_name = self.operator_entry.get().strip()
        self.player_name = self.player_entry.get().strip()
        
        if self.operator_name and self.player_name:
            self.result = True
            self.dialog.destroy()
        else:
            # Show error message
            error_label = tk.Label(self.dialog, text="Please enter both names", font=("Courier New", 10), fg="#ff0000", bg="#000000")
            error_label.pack(pady=5)
            self.dialog.after(2000, error_label.destroy)  # Remove error after 2 seconds
    
    def cancel(self):
        self.dialog.destroy()

class StartScreen:
    def __init__(self, root, on_start_game):
        self.root = root
        self.on_start_game = on_start_game
        self.operator_name = ""
        self.player_name = ""
        width, height = 1280, 800
        self.canvas = tk.Canvas(self.root, width=width, height=height, highlightthickness=0, bg='#000000')
        self.canvas.place(relx=0, rely=0, relwidth=1, relheight=1)
        # Load and display background image
        bg_path = os.path.join(os.path.dirname(__file__), '../ui_elements/graphics/ambulancegraphic2.jpeg')
        bg_path = os.path.abspath(bg_path)
        bg_img = Image.open(bg_path).resize((width, height), Image.Resampling.LANCZOS)
        # Create a dark gradient overlay using PIL
        gradient = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        for y in range(height):
            alpha = int(120 + 80 * (y / height))  # Top: 120, Bottom: 200 (darker overlay)
            ImageDraw.Draw(gradient).rectangle([(0, y), (width, y+1)], fill=(0, 0, 0, alpha))
        bg_img = bg_img.convert('RGBA')
        blended = Image.alpha_composite(bg_img, gradient)
        self.bg_photo = ImageTk.PhotoImage(blended)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.bg_photo)

        content_w, content_h = 600, 420
        content_x, content_y = (width-content_w)//2, 0
        content_img = Image.new('RGBA', (content_w, content_h), (0,0,0,0))
        draw = ImageDraw.Draw(content_img)
        radius = 40
        
        self.content_photo = ImageTk.PhotoImage(content_img)
        self.canvas.create_image(content_x, content_y, anchor=tk.NW, image=self.content_photo)
        # Title with drop shadow
        self.canvas.create_text(
            width//2, content_y+100,
            text="Team Quantum: SGAI Experiment",
            font=("Courier New", 48, "bold"),
            fill="#00ff00",
            anchor=tk.CENTER
        )
        

        ButtonClass = get_button_class()
        if ButtonClass.__name__ == 'Button':  # tkmacosx Button
            login_btn = ButtonClass(
                self.root, text="Log In", font=("Courier New", 18, "bold"),
                bg="#000000", fg="#00ff00", relief=tk.RAISED, bd=4, width=300, height=60,
                bordercolor="#00ff00", highlightcolor="#00ff00",
                activebackground="#111111", activeforeground="#00ff00", cursor="hand2",
                command=self.show_login
            )
        else:  # Regular tk.Button
            login_btn = ButtonClass(
                self.root, text="Log In", font=("Courier New", 18, "bold"),
                bg="#000000", fg="#00ff00", relief=tk.RAISED, bd=4, width=300, height=60,
                activebackground="#111111", activeforeground="#00ff00", cursor="hand2",
                command=self.show_login
            )
        self._add_hover_effect(login_btn, "#000000", "#111111")
        self.canvas.create_window(width//2, height-200, window=login_btn, anchor=tk.CENTER)
        
        # Start button
        if ButtonClass.__name__ == 'Button':  # tkmacosx Button
            start_btn = ButtonClass(
                self.root, text="Start Game", font=("Courier New", 18, "bold"),
                bg="#000000", fg="#00ff00", relief=tk.RAISED, bd=4, width=300, height=60,
                bordercolor="#00ff00", highlightcolor="#00ff00",
                activebackground="#111111", activeforeground="#00ff00", cursor="hand2",
                command=self.start_game
            )
        else:  # Regular tk.Button
            start_btn = ButtonClass(
                self.root, text="Start Game", font=("Courier New", 18, "bold"),
                bg="#000000", fg="#00ff00", relief=tk.RAISED, bd=4, width=300, height=60,
                activebackground="#111111", activeforeground="#00ff00", cursor="hand2",
                command=self.start_game
            )
        self._add_hover_effect(start_btn, "#000000", "#111111")
        self.canvas.create_window(width//2, height-100, window=start_btn, anchor=tk.CENTER)
        
        # Instructions button
        if ButtonClass.__name__ == 'Button':  # tkmacosx Button
            instr_btn = ButtonClass(
                self.root, text="Instructions", font=("Courier New", 18, "bold"),
                bg="#000000", fg="#00ff00", relief=tk.RAISED, bd=4, width=300, height=60,
                bordercolor="#00ff00", highlightcolor="#00ff00",
                activebackground="#111111", activeforeground="#00ff00", cursor="hand2",
                command=self.show_instructions
            )
        else:  # Regular tk.Button
            instr_btn = ButtonClass(
                self.root, text="Instructions", font=("Courier New", 18, "bold"),
                bg="#000000", fg="#00ff00", relief=tk.RAISED, bd=4, width=300, height=60,
                activebackground="#111111", activeforeground="#00ff00", cursor="hand2",
                command=self.show_instructions
            )
        self._add_hover_effect(instr_btn, "#000000", "#111111")
        self.canvas.create_window((width//2)-300, height-100, window=instr_btn, anchor=tk.CENTER)
        
        # Quit button
        if ButtonClass.__name__ == 'Button':  # tkmacosx Button
            quit_btn = ButtonClass(
                self.root, text="Quit", font=("Courier New", 18, "bold"),
                bg="#000000", fg="#00ff00", relief=tk.RAISED, bd=4, width=300, height=60,
                bordercolor="#00ff00", highlightcolor="#00ff00",
                activebackground="#111111", activeforeground="#00ff00", cursor="hand2",
                command=self.root.quit
            )
        else:  # Regular tk.Button
            quit_btn = ButtonClass(
                self.root, text="Quit", font=("Courier New", 18, "bold"),
                bg="#000000", fg="#00ff00", relief=tk.RAISED, bd=4, width=300, height=60,
                activebackground="#111111", activeforeground="#00ff00", cursor="hand2",
                command=self.root.quit
            )
        self._add_hover_effect(quit_btn, "#000000", "#111111")
        self.canvas.create_window((width//2)+300, height-100, window=quit_btn, anchor=tk.CENTER)

    def _add_hover_effect(self, btn, normal, hover):
        def on_enter(e): btn.config(bg=hover)
        def on_leave(e): btn.config(bg=normal)
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)

    def show_login(self):
        """Show the login dialog"""
        dialog = LoginDialog(self.root)
        if dialog.result:
            self.operator_name = dialog.operator_name
            self.player_name = dialog.player_name
            # Show success message
            success_label = tk.Label(self.root, text=f"Logged in as: {self.operator_name} / {self.player_name}", 
                                   font=("Courier New", 12), fg="#00ff00", bg="#000000")
            self.canvas.create_window(1280//2, 50, window=success_label, anchor=tk.CENTER)
            self.root.after(3000, success_label.destroy)  # Remove after 3 seconds

    def start_game(self):
        self.canvas.destroy()
        if self.on_start_game:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # Include milliseconds
            self.on_start_game(timestamp, self.operator_name, self.player_name)

    def show_instructions(self):
        instr_win = tk.Toplevel(self.root)
        instr_win.title("Instructions")
        instr_win.geometry("850x550")  # Increased window size
        instr_win.configure(bg="#000000")
        instr_label = tk.Label(instr_win, text="How to Play", font=("Courier New", 22, "bold"), fg="#00ff00", bg="#000000")
        instr_label.pack(pady=20)
        # Add a scrollable text widget for instructions
        import tkinter.scrolledtext as st
        text = (
            "- Use the action buttons to decide the fate of each humanoid.\n"
            "- Fill your ambulance, but beware of time and capacity!\n"
            "- Scram when full, and try to maximize your score.\n"
            "- The role and state of each humanoid is shown below the image.\n"
            "- Try to save as many as you can before time runs out!\n\n"
            "- Balance your actions to consider the reputation scores of outside observers.\n\n"
            "Reputation Scoring Metrics:\n"
            "- Human Rights Activist: Save as many people as possible, especially injured and elderly.\n"
            "- Military: Prioritize saving police and doctors, and eliminate zombies. Saving other injured (like business or elderly) is less important and may even reduce your score.\n"
            "- Scientist: Save zombies to test the cure and gain information to undo the apocalypse.\n"
            "- Medic: Save people, with extra points for saving doctors and injured individuals.\n"
        )
        instr_text = st.ScrolledText(instr_win, font=("Courier New", 15), fg="#00ff00", bg="#000000", wrap="word", height=18, width=90, borderwidth=0, highlightthickness=0, insertbackground="#00ff00")
        instr_text.insert(tk.END, text)
        instr_text.config(state=tk.DISABLED)
        instr_text.pack(pady=10, padx=30, fill="both", expand=True)
        ButtonClass = get_button_class()
        if ButtonClass.__name__ == 'Button':  # tkmacosx Button
            close_btn = ButtonClass(instr_win, text="Close", font=("Courier New", 14, "bold"), 
                                  bg="#000000", fg="#00ff00", relief=tk.RAISED, bd=4, 
                                  bordercolor="#00ff00", highlightcolor="#00ff00", 
                                  activebackground="#111111", activeforeground="#00ff00", 
                                  cursor="hand2", width=150, height=50, command=instr_win.destroy)
        else:  # Regular tk.Button
            close_btn = ButtonClass(instr_win, text="Close", font=("Courier New", 14, "bold"), 
                                  bg="#000000", fg="#00ff00", relief=tk.RAISED, bd=4, 
                                  activebackground="#111111", activeforeground="#00ff00", 
                                  cursor="hand2", width=150, height=50, command=instr_win.destroy)
        close_btn.pack(pady=20) 