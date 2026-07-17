import tkinter as tk
from tkinter import ttk


# adding an additional gui class to assist with incorporating the other facets of the program more seamlessly
# into the current gui framework without porting everything into seperate
# TKinter scripts
class AddedGUI:
    def __init__(self, title="Context Window"):
        print("Window opened.")
        self.root = tk.Tk()
        self.root.title(title)
        self.root.minsize(400, 100)
        self.root.maxsize(800, 400)
        self.row = 0
        self.column = 0

    def reset(self):
        for child in self.root.winfo_children():
            child.destroy()
        self.row = 0
        self.column = 0

    def add_label(self, message):
        ttk.Label(self.root, text=message).grid(
            column=self.column, row=self.row, sticky=tk.W
        )
        self.row += 1

    def add_button(self, text, cmd):

        text_len = len(text)
        width = 15
        if text_len > width:
            width = text_len

        ttk.Button(self.root, text=text, command=cmd, width=width).grid(
            column=self.column, row=self.row, sticky=tk.W, padx=5, pady=1
        )
        self.row += 1
