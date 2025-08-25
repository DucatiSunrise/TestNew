import tkinter as tk
from tkinter import ttk, messagebox
from database import (
    get_all_users, create_user, update_user_role,
    reset_user_password, delete_user
)

class EmployeeTab:
    def __init__(self, parent):
        self.parent = parent
        self.selected_user_id = None

        # Treeview
        self.tree = ttk.Treeview(parent, columns=("ID", "Username", "Role"), show="headings")
        for col in ("ID", "Username", "Role"):
            self.tree.heading(col, text=col)
        self.tree.bind("<<TreeviewSelect>>", self.on_row_select)
        self.tree.pack(fill="x", pady=5)

        # Form
        form_frame = tk.Frame(parent)
        form_frame.pack(pady=10)

        tk.Label(form_frame, text="Username").grid(row=0, column=0)
        self.username_entry = tk.Entry(form_frame)
        self.username_entry.grid(row=0, column=1)

        tk.Label(form_frame, text="Password").grid(row=1, column=0)
        self.password_entry = tk.Entry(form_frame, show="*")
        self.password_entry.grid(row=1, column=1)

        tk.Label(form_frame, text="Role").grid(row=2, column=0)
        self.role_box = ttk.Combobox(form_frame, values=["technician", "manager", "superuser"])
        self.role_box.grid(row=2, column=1)

        # Buttons
        btn_frame = tk.Frame(parent)
        btn_frame.pack(pady=5)

        tk.Button(btn_frame, text="Add User", command=self.add_user).grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text="Update Role", command=self.update_role).grid(row=0, column=1, padx=5)
        tk.Button(btn_frame, text="Reset Password", command=self.reset_password).grid(row=0, column=2, padx=5)
        tk.Button(btn_frame, text="Delete User", command=self.delete_user).grid(row=0, column=3, padx=5)

        self.refresh_tree()

    def refresh_tree(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for user in get_all_users():
            self.tree.insert("", "end", values=user)

    def on_row_select(self, event):
        selected = self.tree.selection()
        if selected:
            user = self.tree.item(selected[0])["values"]
            self.selected_user_id = user[0]
            self.username_entry.delete(0, tk.END)
            self.username_entry.insert(0, user[1])
            self.role_box.set(user[2])

    def add_user(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        role = self.role_box.get()

        if not username or not password or not role:
            messagebox.showerror("Error", "All fields are required.")
            return

        try:
            create_user(username, password, role)
            self.refresh_tree()
            messagebox.showinfo("Success", f"User '{username}' added.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def update_role(self):
        if not self.selected_user_id:
            messagebox.showerror("Error", "Select a user first.")
            return
        role = self.role_box.get()
        update_user_role(self.selected_user_id, role)
        self.refresh_tree()
        messagebox.showinfo("Updated", "User role updated.")

    def reset_password(self):
        if not self.selected_user_id:
            messagebox.showerror("Error", "Select a user first.")
            return
        password = self.password_entry.get()
        if not password:
            messagebox.showerror("Error", "Enter a new password.")
            return
        reset_user_password(self.selected_user_id, password)
        messagebox.showinfo("Success", "Password reset.")

    def delete_user(self):
        if not self.selected_user_id:
            messagebox.showerror("Error", "Select a user to delete.")
            return
        confirm = messagebox.askyesno("Confirm", "Are you sure you want to delete this user?")
        if confirm:
            delete_user(self.selected_user_id)
            self.refresh_tree()
            messagebox.showinfo("Deleted", "User deleted.")
