import tkinter as tk
import os
import math

# class
class Clock(object):
    def __init__(self, root, w, h, init_h, init_m):
        # Wider and shorter for top bar look
        self.width = math.floor(0.4 * w)
        self.height = 90
        self.canvas = tk.Canvas(root, width=self.width, height=self.height, bg='#000000', highlightthickness=0)
        # Place at the top center
        self.canvas.place(x=(w - self.width) // 2, y=20)
        self._draw_background()
        self.time_label = tk.Label(self.canvas, font=("Courier New", 25, "bold"), fg="#00ff00", bg="#000000")
        self.time_label.place(relx=0.5, rely=0.55, anchor=tk.CENTER)
        self.title_label = tk.Label(self.canvas, text="Remaining Time", font=("Courier New", 22, "bold"), fg="#00ff00", bg="#000000")
        self.title_label.place(relx=0.5, rely=0.18, anchor=tk.CENTER)
        self.update_time(init_h, init_m)

    def _draw_background(self):
        # Draw a rounded rectangle for the clock background
        radius = 30
        self.canvas.create_rectangle(10, 10, self.width-10, self.height-10, fill="#000000", outline="#00ff00", width=3)
        # Optionally, add a subtle shadow or border effect

    def update_time(self, h, m):
        # Format time as HH:MM with leading zeros
        time_str = f"{int(h):02d}:{int(m):02d}"
        self.time_label.config(text=time_str)
        return

# # Main Function Trigger
# if __name__ == '__main__':
#     root = Clock()
#
#     # Creating Main Loop
#     while True:
#         root.update()
#         root.update_idletasks()
#         root.update_class(12, 15)
