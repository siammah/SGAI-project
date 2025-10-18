import tkinter as tk
from tkinter import messagebox


class ConfirmationDialog:
    def __init__(self, parent):
        self.parent = parent
        self.result = False
    
    def show(self, title="Confirm", message="Are you sure?"):
        """
        Shows a confirmation dialog and returns True if user clicks Yes, False otherwise
        """
        self.result = messagebox.askyesno(title, message)
        return self.result 