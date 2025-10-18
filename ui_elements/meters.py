import tkinter as tk

class MetersPanel:
    def __init__(self, root, x, y, width=220, height=220, meter_labels=None):  # Increased default height from 200 to 220
        if meter_labels is None:
            meter_labels = ["Military", "HRA", "Scientist", "Medic"]
        self.num_meters = 4
        self.width = width
        self.height = height
        # Fixed colors - no theme dependency
        self.bg_color = '#000000'
        self.label_fg = '#00ff00'
        self.bar_bg = '#333333'
        self.bar_fg = '#00ff00'
        self.border_color = '#00ff00'
        
        self.canvas = tk.Canvas(root, width=width, height=height, bg=self.bg_color, highlightthickness=0)
        self.canvas.place(x=x, y=y, width=width, height=self.height)
        
        # Add title label matching capacity meter style
        self.title_label = tk.Label(self.canvas, text="Metrics", font=("Courier New", 22, "bold"), fg="#00ff00", bg="#000000")
        self.canvas.create_window(width//2, 15, anchor=tk.N, window=self.title_label)
        
        self.meter_frames = []
        self.progress_bars = []
        self.labels = []
        self.bar_canvases = []
        self.bar_rectangles = []
        self.meter_rectangles = []  # Store rectangles around each meter section
        

        title_space = 40  # Space for title and top padding
        bottom_margin = 40  # Increased bottom margin from 20 to 40
        available_height = height - title_space - bottom_margin
        meter_spacing = available_height // self.num_meters
        
        for i in range(self.num_meters):
            frame = tk.Frame(self.canvas, bg=self.bg_color)
            y_position = title_space + (i * meter_spacing) + (meter_spacing // 2)
            # Increased frame height to accommodate larger labels and proper spacing
            self.canvas.create_window(width//2, y_position, anchor=tk.N, window=frame, width=width-20, height=50)
            
            # Create label above the meter bar with larger font
            label = tk.Label(frame, text=meter_labels[i], font=("Courier New", 16, "bold"), bg=self.bg_color, fg=self.label_fg)
            label.pack(side=tk.TOP, pady=(0, 4))
            
            # Create custom progress bar using canvas
            bar_canvas = tk.Canvas(frame, bg=self.bar_bg, height=12, highlightthickness=0)
            bar_canvas.pack(side=tk.TOP, fill=tk.X, expand=True, padx=(0, 0))
            
            # Create the progress bar rectangle
            bar_rect = bar_canvas.create_rectangle(0, 0, 0, 12, fill=self.bar_fg, outline=self.border_color, width=1)
            
            # Create rectangle around the entire meter section (label + bar)
            meter_rect = self.canvas.create_rectangle(
                10, y_position - 5, width - 10, y_position + 55,
                outline=self.border_color, width=2, fill=""
            )
            
            self.labels.append(label)
            self.bar_canvases.append(bar_canvas)
            self.bar_rectangles.append(bar_rect)
            self.meter_frames.append(frame)
            self.meter_rectangles.append(meter_rect)
            
            # Store max values for each meter
            if not hasattr(self, 'max_values'):
                self.max_values = []
            self.max_values.append(1000)  # Default max value

    def update_meter(self, idx, value, max_value):
        if 0 <= idx < len(self.bar_rectangles):
            self.max_values[idx] = max_value
            bar_canvas = self.bar_canvases[idx]
            bar_rect = self.bar_rectangles[idx]
            
            # Get canvas dimensions
            canvas_width = bar_canvas.winfo_width()
            if canvas_width <= 1:  # Canvas not yet rendered
                bar_canvas.update_idletasks()
                canvas_width = bar_canvas.winfo_width()
            
            # Calculate progress bar width
            progress_width = min(canvas_width, max(0, (value / max_value) * canvas_width))
            
            # Update the progress bar rectangle
            bar_canvas.coords(bar_rect, 0, 0, progress_width, 12)

    def hide(self):
        """Hide the meters panel"""
        self.canvas.place_forget()

    def show(self, x, y):
        """Show the meters panel at specified position"""
        self.canvas.place(x=x, y=y, width=self.width, height=self.height)

