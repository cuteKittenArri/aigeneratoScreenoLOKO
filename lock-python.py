#!/usr/bin/env python3
"""
Simple Lock Screen with Image Background
Uses Python3 + Tkinter (built-in on most Linux systems)
No external packages required!
"""

import tkinter as tk
from tkinter import messagebox
import sys
import os

# === CONFIGURATION ===
PASSWORD = "arri"  # Change this!
LOCK_IMAGE = os.path.expanduser("lock_bg.png")  # Change to your image path
# ====================

class LockScreen:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Screen Lock")
        
        # Make fullscreen
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-topmost', True)
        
        # Prevent closing
        self.root.protocol("WM_DELETE_WINDOW", self.do_nothing)
        
        # Disable Alt+F4, etc.
        self.root.bind('<Alt-F4>', self.do_nothing)
        self.root.bind('<Control-c>', self.do_nothing)
        
        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Try to load and display the background image
        try:
            # Try with PIL first (if available)
            try:
                from PIL import Image, ImageTk
                img = Image.open(LOCK_IMAGE)
                img = img.resize((screen_width, screen_height), Image.LANCZOS)
                self.bg_image = ImageTk.PhotoImage(img)
                self.use_pil = True
            except ImportError:
                # Fallback to basic Tkinter (works with GIF/PGM/PPM only)
                self.bg_image = tk.PhotoImage(file=LOCK_IMAGE)
                self.use_pil = False
            
            # Create background label
            bg_label = tk.Label(self.root, image=self.bg_image)
            bg_label.place(x=0, y=0, relwidth=1, relheight=1)
            
        except Exception as e:
            print(f"Could not load image: {e}")
            # Use solid black background instead
            self.root.configure(bg='black')
        
        # Create lock interface container (no background - transparent effect)
        container = tk.Frame(self.root, bd=0, highlightthickness=0)
        container.place(relx=0.5, rely=0.5, anchor='center')
        
        # Password entry (only element)
        self.password_entry = tk.Entry(
            container,
            show='●',
            font=('Arial', 14),
            width=25,
            justify='center'
        )
        self.password_entry.pack()
        self.password_entry.focus()
        
        # Bind Enter key
        self.password_entry.bind('<Return>', self.check_password)
        
        # Grab keyboard focus
        self.root.grab_set()
        
    def do_nothing(self, event=None):
        """Prevent window from being closed"""
        return "break"
    
    def check_password(self, event=None):
        """Check if entered password is correct"""
        entered = self.password_entry.get()
        
        if entered == PASSWORD:
            self.root.after(500, self.root.destroy)
        else:
            self.password_entry.delete(0, tk.END)
    
    def run(self):
        """Start the lock screen"""
        self.root.mainloop()

def main():
    # Check if image exists
    if not os.path.exists(LOCK_IMAGE):
        print(f"Warning: Image not found at {LOCK_IMAGE}")
        print("Edit the LOCK_IMAGE path in the script, or the lock screen will use a black background")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    # Check if we're in a graphical environment
    if not os.environ.get('DISPLAY'):
        print("Error: No X11 display found")
        sys.exit(1)
    
    try:
        lock = LockScreen()
        lock.run()
    except tk.TclError as e:
        print(f"Error: Could not create GUI - {e}")
        print("Tkinter may not be installed. Install it with: apt install python3-tk")
        sys.exit(1)

if __name__ == "__main__":
    main()
