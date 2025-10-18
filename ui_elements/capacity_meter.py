import math
import tkinter as tk


class CapacityMeter(object):
    def __init__(self, root, w, h, max_cap, width=None, height=None, x=None, y=None):
        # Responsive: allow width/height to be set by parent
        self.width = width if width is not None else math.floor(0.18 * w)
        self.height = height if height is not None else 200
        self.canvas = tk.Canvas(root, width=self.width, height=self.height, bg='#000000')
        px = x if x is not None else w - self.width - 30
        py = y if y is not None else 20
        self.canvas.place(x=px, y=py, width=self.width, height=self.height)
        self.__units = []
        self.canvas.update()
        self.render(max_cap)

    def render(self, max_cap):
        self.canvas.delete("all")
        tk.Label(self.canvas, text="Capacity", font=("Courier New", 22, "bold"), fg="#00ff00", bg="#000000").place(x=self.width//2, y=15, anchor=tk.N)
        
        # Calculate box size to fit 3 rows of 4 boxes with padding
        padding = 12  # Reduced padding to fit better
        title_height = 60  # Increased space for title and padding
        bottom_margin = 20  # Add bottom margin
        available_width = self.width - 2 * padding
        available_height = self.height - title_height - bottom_margin - 2 * padding  # Leave space for title, bottom margin, and padding
        
        # Calculate box size to fit exactly 3 rows of 4 boxes
        box_width = (available_width - 3 * padding) // 4  # 4 boxes per row, 3 gaps
        box_height = (available_height - 2 * padding) // 3  # 3 rows, 2 gaps
        

        box_size = max(min(box_width, box_height), 30)  # Minimum 30px box size
        
        # Calculate starting position to center the grid
        start_x = padding + (available_width - (4 * box_size + 3 * padding)) // 2
        start_y = title_height + padding + (available_height - (3 * box_size + 2 * padding)) // 2
        

        print(f"Canvas: {self.width}x{self.height}, Box size: {box_size}, Start: ({start_x}, {start_y})")
        print(f"Available: {available_width}x{available_height}, Title height: {title_height}")
        
        # Create rectangle around the capacity boxes
        box_area_width = 4 * box_size + 3 * padding
        box_area_height = 3 * box_size + 2 * padding
        box_area_x = start_x - 12  # 5px margin around the boxes
        box_area_y = start_y - 12
        box_area_width += 24  # Add 10px total width (5px on each side)
        box_area_height += 24  # Add 10px total height (5px on each side)
        
        # Draw the border rectangle around the capacity boxes
        self.canvas.create_rectangle(
            box_area_x, box_area_y, 
            box_area_x + box_area_width, box_area_y + box_area_height,
            outline='#00ff00', width=2, fill=""
        )
        
        x = start_x
        y = start_y
        for i in range(0, max_cap):
            # Create the square - the positioning logic should ensure it fits
            self.__units.append(create_unit(self.canvas, x, y, box_size))
            print(f"Square {i+1}: ({x}, {y}) to ({x+box_size}, {y+box_size})")
            x += box_size + padding
            if (i + 1) % 4 == 0:  # New row after every 4 boxes
                x = start_x
                y += box_size + padding

    def update_fill(self, index):
        if index != 0:
            self.canvas.itemconfig(self.__units[index - 1], fill="#00ff00")  # Neon green
        else:
            for unit in self.__units:
                self.canvas.itemconfig(unit, fill="#333333")  # Dark grey



def create_unit(canvas, x, y, size):
    return canvas.create_rectangle(x, y, x+size, y+size, fill='#333333', outline='#00ff00', width=1)
