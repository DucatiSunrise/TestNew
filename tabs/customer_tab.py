"""
customer_tab.py

This module defines the CustomerTab class for managing customers in a GUI application. 
It integrates with the database to perform CRUD operations, 
load data, and export/import customer information.

Classes:
    CustomerTab - A GUI interface for customer management.

Dependencies:
    - tkinter for GUI components.
    - mysql.connector and mariadb for database connectivity.
    - database module for database operations.

Author: McClure, M.T.
Date: 12-2-24
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import mysql.connector
import mariadb
from database import (CustomerManager, get_audit_logs, validate_foreign_key, has_permission
        )


class CustomerTab:
    """
    Initialize customer tab
    """
    def __init__(self, parent, user_role):
        self.parent = parent
        self.user_role = user_role
        self.note_entry = None
        self.student_id_entry = None
        self.setup_ui()

    def setup_ui(self):
        """
        Setup UI, treeview, and buttons
        """
        tk.Label(self.parent, text="Customer Management", font=("Helvetica", 16)).pack(pady=10)

        search_frame = tk.Frame(self.parent)
        search_frame.pack(fill="x", pady=5)
        self.search_entry = tk.Entry(search_frame)
        self.search_entry.pack(side="left", fill="x", expand=True, padx=5)

        self.search_filter = ttk.Combobox(
            search_frame,
            values=["All", "Customer ID", "First Name", "Last Name",
                    "Phone", "Email", "Address", "Student/School ID"]
        )
        self.search_filter.current(0)
        self.search_filter.pack(side="left", padx=5)

        tk.Button(search_frame, text="Search",
                  command=self.search_customers).pack(side="left", padx=5)

        self.tree = ttk.Treeview(
            self.parent,
            columns=("ID", "First Name", "Last Name", "Email", "Phone"),
            show="headings"
        )
        self.tree.pack(fill="both", expand=True, pady=10)
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=150)

        button_frame = tk.Frame(self.parent)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Add",
                  command=self.open_add_customer).pack(side="left", padx=5)
        tk.Button(button_frame, text="Edit",
                  command=self.edit_customer).pack(side="left", padx=5)

        if self.user_role == "root":
            tk.Button(button_frame, text="Delete",
                      command=self.delete_customer).pack(side="left", padx=5)

        tk.Button(button_frame, text="View Notes",
                  command=self.view_customer_notes).pack(side="left", padx=5)
        tk.Button(button_frame, text="View History",
                  command=self.view_customer_history).pack(side="left", padx=5)

        if self.user_role in ["superuser", "root"]:
            tk.Button(button_frame, text="View Audit Logs",
                      command=self.view_audit_logs).pack(side="left", padx=5)

        tk.Button(button_frame, text="Export to CSV",
                  command=self.export_customers).pack(side="left", padx=5)

        if self.user_role in ["superuser", "root"]:
            tk.Button(button_frame, text="Import from CSV",
                      command=self.import_customers).pack(side="left", padx=5)

    def _customer_form(self, parent, submit_callback, customer_data=None):
        parent.geometry("500x800")

        form_data = {
            "first_name": tk.StringVar(value=customer_data["first_name"] 
                                    if customer_data else ""),
            "last_name": tk.StringVar(value=customer_data["last_name"] 
                                    if customer_data else ""),
            "street": tk.StringVar(value=customer_data.get("street", "") 
                                    if customer_data else ""),
            "city": tk.StringVar(value=customer_data.get("city", "") 
                                    if customer_data else ""),
            "state": tk.StringVar(value=customer_data.get("state", "") 
                                    if customer_data else ""),
            "zip_code": tk.StringVar(value=customer_data.get("zip_code", "") 
                                    if customer_data else ""),
            "customer_type": tk.StringVar(value=customer_data.get("customer_type", "Student") 
                                    if customer_data else "Student"),
            "student_id": tk.StringVar(value=customer_data.get("student_id", "") 
                                    if customer_data else ""),
            "contact_email": tk.BooleanVar(value=customer_data.get("contact_email", False)),
            "contact_phone": tk.BooleanVar(value=customer_data.get("contact_phone", False)),
            "contact_na": tk.BooleanVar(value=customer_data.get("contact_na", False)),
            "phone_call": tk.BooleanVar(value=customer_data.get("phone_call", False)),
            "phone_text": tk.BooleanVar(value=customer_data.get("phone_text", False)),
            "phone": tk.StringVar(value=customer_data.get("phone", "") 
                                  if customer_data else ""),
            "email": tk.StringVar(value=customer_data.get("email", "") 
                                  if customer_data else "")
        }

        def on_customer_type_change():
            if form_data["customer_type"].get() == "External Customer":
                self.student_id_entry.config(state="readonly")
                form_data["student_id"].set("N/A")
            else:
                self.student_id_entry.config(state="normal")
                form_data["student_id"].set("")

        def on_contact_preference_change():
            phone_call_checkbox.config(state="normal"
                                if form_data["contact_phone"].get() else "disabled")
            phone_text_checkbox.config(state="normal"
                                if form_data["contact_phone"].get() else "disabled")
            if form_data["contact_na"].get():
                form_data["contact_email"].set(False)
                form_data["contact_phone"].set(False)
            else:
                form_data["contact_na"].set(False)

        for label, key in [
            ("First Name", "first_name"),
            ("Last Name", "last_name"),
            ("Street", "street"),
            ("City", "city"),
            ("State", "state"),
            ("Zip Code", "zip_code"),
            ("Customer Type", "customer_type"),
            ("Student/School ID", "student_id"),
            ("Phone", "phone"),
            ("Email", "email")
        ]:
            tk.Label(parent, text=label).pack(anchor="w", padx=10, pady=2)
            if key == "customer_type":
                customer_type_dropdown = ttk.Combobox(
                    parent,
                    textvariable=form_data[key],
                    values=["Student", "Staff", "Faculty", "External Customer"],
                    state="readonly"
                )
                customer_type_dropdown.pack(fill="x", padx=10, pady=2)
                customer_type_dropdown.bind("<<ComboboxSelected>>",
                                    lambda _: on_customer_type_change())
            elif key == "student_id":
                self.student_id_entry = tk.Entry(parent, textvariable=form_data[key])
                self.student_id_entry.pack(fill="x", padx=10, pady=2)
                if form_data["customer_type"].get() == "External Customer":
                    self.student_id_entry.config(state="readonly")
            else:
                tk.Entry(parent, textvariable=form_data[key]).pack(fill="x", padx=10, pady=2)

        tk.Label(parent, text="Contact Preference").pack(anchor="w", padx=10, pady=2)
        tk.Checkbutton(
            parent, text="Email", variable=form_data["contact_email"],
            command=on_contact_preference_change
            ).pack(anchor="w", padx=10, pady=2)
        tk.Checkbutton(
            parent, text="Phone", variable=form_data["contact_phone"],
            command=on_contact_preference_change
        ).pack(anchor="w", padx=10, pady=2)
        tk.Checkbutton(
            parent, text="N/A", variable=form_data["contact_na"],
            command=on_contact_preference_change
        ).pack(anchor="w", padx=10, pady=2)

        phone_call_checkbox = tk.Checkbutton(
            parent, text="Phone Call", variable=form_data["phone_call"], state="disabled"
        )
        phone_call_checkbox.pack(anchor="w", padx=20, pady=2)
        phone_text_checkbox = tk.Checkbutton(
            parent, text="Text", variable=form_data["phone_text"], state="disabled"
        )
        phone_text_checkbox.pack(anchor="w", padx=20, pady=2)

        tk.Button(
            parent,
            text="Submit",
            command=lambda: submit_callback({key: var.get() for key, var in form_data.items()})
        ).pack(pady=10)

    def open_add_customer(self):
        """
        Open customer data entry window
        """
        popup = tk.Toplevel(self.parent)
        popup.title("Add Customer")
        self._customer_form(popup, self._submit_new_customer, customer_data={})

    def load_customers(self):
        """
        Load all customers and update the TreeView.
        """
        try:
            customers = CustomerManager.get_all_customers()
            self._update_treeview(customers)
        except (mariadb.Error, mysql.connector.Error) as db_error:
            messagebox.showerror("Database Error",
                    f"Failed to load customers from the database: {db_error}")
        except ValueError as ve:
            messagebox.showerror("Value Error", f"Data processing error: {ve}")
        except KeyError as ke:
            messagebox.showerror("Key Error", f"Unexpected data structure: {ke}")

    def validate_customer_id(self, customer_id):
        """
        Check if customer is on database.
        """
        if not validate_foreign_key("customers", "id", customer_id):
            if self.parent.winfo_exists():
                messagebox.showerror("Error", "Customer does not exist.")
            return False
        return True

    def delete_customer(self):
        """
        Delete customer, superuser and root only.
        """
        if not has_permission(self.user_role, ["superuser", "root"]):
            if self.parent.winfo_exists():
                messagebox.showerror("Permission Denied", "You do not have permission.")
            return

        selected_item = self.tree.selection()
        if not selected_item:
            if self.parent.winfo_exists():
                messagebox.showerror("Error", "No customer selected!")
            return

        customer_id = self.tree.item(selected_item)["values"][0]
        try:
            CustomerManager.delete_customer(customer_id)
            if self.parent.winfo_exists():
                messagebox.showinfo("Success", "Customer deleted successfully!")
            self.search_customers()
        except ValueError as ve:
            if self.parent.winfo_exists():
                messagebox.showerror("Error", f"Failed to delete customer: {ve}")

    def _submit_new_customer(self, form_fields):
        try:
            CustomerManager.add_customer(form_fields)
            if self.parent.winfo_exists():
                messagebox.showinfo("Success", "Customer added successfully!")
            self.load_customers()
        except ValueError as ve:
            if self.parent.winfo_exists():
                messagebox.showerror("Error", f"Failed to add customer: {ve}")

    def edit_customer(self):
        """
        Edit customers and update tree
        """
        selected_item = self.tree.selection()
        if not selected_item:
            if self.parent.winfo_exists():
                messagebox.showerror("Error", "No customer selected!")
            return

        customer_id = self.tree.item(selected_item)["values"][0]
        customer_data = CustomerManager.get_customer_details(customer_id)

        popup = tk.Toplevel(self.parent)
        popup.title("Edit Customer")
        self._customer_form(popup, lambda data:
        self._submit_edit_customer(customer_id, data), customer_data)

    def _submit_edit_customer(self, customer_id, form_data):
        try:
            CustomerManager.update_customer(customer_id, form_data)
            if self.parent.winfo_exists():
                messagebox.showinfo("Success", "Customer updated successfully!")
            self.search_customers()
        except ValueError as e:
            if self.parent.winfo_exists():
                messagebox.showerror("Error", f"Failed to update customer: {e}")

    def search_customers(self):
        """
        Search customers and update tree
        """
        search_term = self.search_entry.get()
        filter_field = self.search_filter.get()

        try:
            customers = CustomerManager.search_customers(search_term, filter_field=filter_field)
            self._update_treeview(customers)
        except ValueError as ve:
            messagebox.showerror("Error", f"Search failed: {ve}")

    def view_customer_notes(self):
        """
        View customer notes, when created, and by what user.
        """
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "No customer selected!")
            return

        customer_id = self.tree.item(selected_item)["values"][0]
        notes = CustomerManager.get_customer_notes(customer_id)

        popup = tk.Toplevel(self.parent)
        popup.title(f"Notes for Customer ID: {customer_id}")

        notes_frame = tk.Frame(popup)
        notes_frame.pack(fill="both", expand=True, padx=10, pady=10)

        for note in notes:
            tk.Label(notes_frame, text=f"{note['created_at']}: {note['note']}").pack(anchor="w")

        self.note_entry = tk.Entry(notes_frame, width=50)
        self.note_entry.pack(pady=5)
        tk.Button(
            notes_frame,
            text="Add Note",
            command=lambda: self.add_note(customer_id)
        ).pack()

    def add_note(self, customer_id):
        """
        Ensure note entry is not null or blank.
        """
        note = self.note_entry.get()
        if not note:
            messagebox.showerror("Error", "Note cannot be empty!")
            return

        try:
            CustomerManager.add_customer_note(customer_id, note)
            messagebox.showinfo("Success", "Note added successfully!")
        except ValueError as ve:
            messagebox.showerror("Error", f"Failed to add note: {ve}")

    def view_customer_history(self):
        """
        View the history for the selected customer.
        """
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "No customer selected!")
            return

        customer_id = self.tree.item(selected_item)["values"][0]

        try:
            # Fetch history using CustomerManager
            work_orders = CustomerManager.get_customer_history(customer_id)

            if not work_orders:
                messagebox.showinfo("Info", "No history found for this customer.")
                return

            # Create a popup window to display history
            popup = tk.Toplevel(self.parent)
            popup.title(f"History for Customer ID: {customer_id}")

            history_frame = tk.Frame(popup)
            history_frame.pack(fill="both", expand=True, padx=10, pady=10)

            # Add each work order to the popup
            for order in work_orders:
                order_details = (
                    f"ID: {order['id']}, Status: {order['status']}, "
                    f"Priority: {order['priority']}, Notes: {order['notes']}, "
                    f"Created At: {order['created_at']}"
                )
                tk.Label(history_frame, text=order_details, anchor="w",
                         justify="left").pack(fill="x", pady=2)

        except KeyError as ke:
            messagebox.showerror("Key Error",
                    f"Missing or unexpected data structure: {ke}")
        except ValueError as ve:
            messagebox.showerror("Value Error", f"Data processing error: {ve}")
        except (mariadb.Error, mysql.connector.Error) as db_error:
            messagebox.showerror("Database Error",
                     f"Failed to retrieve customer history: {db_error}")

    def view_audit_logs(self):
        """View audit logs (superuser/root only)."""
        if self.user_role not in ["superuser", "root"]:
            messagebox.showerror("Permission Denied",
                        "You do not have permission to view audit logs.")
            return

        logs = get_audit_logs()
        popup = tk.Toplevel(self.parent)
        popup.title("Audit Logs")

        log_frame = tk.Frame(popup)
        log_frame.pack(fill="both", expand=True, padx=10, pady=10)

        for log in logs:
            tk.Label(log_frame,
    text=f"{log['timestamp']}:{log['action']} on Customer {log['customer_id']}").pack(anchor="w")

    def export_customers(self):
        """
        Export and save customer data as CSV.
        """
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            title="Save Customer Data As"
        )
        if not file_path:
            return

        try:
            CustomerManager.export_customers_to_csv(file_path)
            messagebox.showinfo("Success", f"Customer data exported to {file_path}")
        except ValueError as ve:
            messagebox.showerror("Error", f"Failed to export customer data: {ve}")

    def import_customers(self):
        """
        Import customers
        """
        file_path = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv")],
            title="Select Customer Data File"
        )
        if not file_path:
            return

        try:
            CustomerManager.import_customers_from_csv(file_path)
            messagebox.showinfo("Success", "Customer data imported successfully!")
            self.search_customers()
        except ValueError as ve:
            messagebox.showerror("Error", f"Failed to import customer data: {ve}")

    def _update_treeview(self, customers):
        self.tree.delete(*self.tree.get_children())
        for customer in customers:
            print("Inserting customer:", customer)  # Debugging
            self.tree.insert(
                "", "end",
                values=(
                    customer[0],
                    customer[1],
                    customer[2],
                    customer[3],
                    customer[4],
                    customer[5],
                    customer[6],
                    customer[7],
                    customer[8],
                    customer[9],
                    customer[10],
                    customer[11],
                )
            )
