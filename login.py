# login.py
import tkinter as tk
from tkinter import messagebox
from database import authenticate_user
from main import MainGUI

class LoginWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Login")
        self.root.geometry("300x180")

        tk.Label(root, text="Username").pack()
        self.username_entry = tk.Entry(root)
        self.username_entry.pack()

        tk.Label(root, text="Password").pack()
        self.password_entry = tk.Entry(root, show="*")
        self.password_entry.pack()

        tk.Button(root, text="Login", command=self.attempt_login).pack(pady=10)

    def attempt_login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        role = authenticate_user(username, password)
        if role:
            self.root.destroy()
            main_root = tk.Tk()
            app = MainGUI(main_root, user_role=role, username=username)
            main_root.mainloop()
        else:
            messagebox.showerror("Login Failed", "Invalid username or password.")

if __name__ == "__main__":
    root = tk.Tk()
    app = LoginWindow(root)
    root.mainloop()
