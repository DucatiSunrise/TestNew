"""
workorder_tab.py

This module defines the WorkOrderTab class for managing the Work Order tab in a GUI application.
It provides functionality for creating, editing, and managing work orders, including support
for file attachments, parts, notifications, and a manager workbench for reviewing and closing
work orders.

Classes:
    WorkOrderTab - A GUI interface for work order management.

Dependencies:
    - tkinter for GUI components.
    - mysql.connector for database connectivity.
    - database module for executing database operations and handling notifications.

Author: McClure, M.T.
Date: 2024-12-02
"""

import os
import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import mysql.connector

from database import (
    insert_file_metadata,
    get_notifications,
    execute_query,
    DatabaseError,
    add_work_order as db_add_work_order,
    fetch_one,
    fetch_all,
)

# ---------------------------------------------------------------------------
# Shared constants to avoid “Open” vs “Active” mismatches across the UI/DB.
# Keep these aligned with whatever your DB actually uses.
# ---------------------------------------------------------------------------
STATUSES = ["Open", "On Hold", "Completed", "Closed", "Pending"]
PRIORITIES = ["Low", "Medium", "High", "Critical"]
WORK_ORDER_TYPES = ["Troubleshoot", "Upgrade", "Maintenance"]
DEVICE_TYPES = ["Laptop", "Tablet", "Desktop"]


class WorkOrderTab:
    """
    Generate Work Orders tab layout and GUIs.
    """

    def __init__(self, parent_frame, user_role="technician"):
        self.parent_frame = parent_frame
        self.user_role = user_role

        # Create Notebook for Tabs within the work order section
        self.notebook = ttk.Notebook(parent_frame)
        self.notebook.pack(fill="both", expand=True)

        # Search Tab
        self.search_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.search_tab, text="Search")
        self.setup_search_tab()

        # Work Order Details Tab
        self.details_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.details_tab, text="Work Order Details")
        self.setup_details_tab()

        # Parts Tab
        self.parts_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.parts_tab, text="Parts")
        self.setup_parts_tab()

        # Attachments Tab
        self.attachments_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.attachments_tab, text="Attachments")
        self.setup_attachments_tab()

        # Actions Tab
        self.actions_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.actions_tab, text="Actions")
        self.setup_actions_tab()

        # Manager Workbench Tab
        self.workbench_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.workbench_tab, text="Manager Workbench")
        self.setup_workbench_tab()

    # -----------------------------------------------------------------------
    # Search
    # -----------------------------------------------------------------------
    def setup_search_tab(self):
        """Setup search tab GUI."""
        ttk.Label(self.search_tab, text="Status:").grid(row=0, column=0, padx=10, pady=10)
        self.status_filter = ttk.Combobox(self.search_tab, values=STATUSES, state="readonly")
        self.status_filter.grid(row=0, column=1, padx=10, pady=10)

        ttk.Label(self.search_tab, text="Search By:").grid(row=0, column=2, padx=10, pady=10)
        self.search_filter = ttk.Combobox(
            self.search_tab,
            values=["Technician", "Priority", "Date Range"],
            state="readonly",
        )
        self.search_filter.grid(row=0, column=3, padx=10, pady=10)

        self.search_entry = ttk.Entry(self.search_tab)
        self.search_entry.grid(row=0, column=4, padx=10, pady=10)

        self.search_button = ttk.Button(self.search_tab, text="Search", command=self.perform_search)
        self.search_button.grid(row=0, column=5, padx=10, pady=10)

        # Search results
        self.search_results = ttk.Treeview(
            self.search_tab,
            columns=("ID", "Customer ID", "Status", "Technician"),
            show="headings",
        )
        self.search_results.heading("ID", text="ID")
        self.search_results.heading("Customer ID", text="Customer ID")
        self.search_results.heading("Status", text="Status")
        self.search_results.heading("Technician", text="Technician")
        self.search_results.grid(row=1, column=0, columnspan=6, padx=10, pady=10, sticky="nsew")
        self.search_results.bind("<Double-1>", self._on_search_row_open)

        # Make result area stretch
        self.search_tab.rowconfigure(1, weight=1)
        for c in range(6):
            self.search_tab.columnconfigure(c, weight=1)

    def perform_search(self):
        """Perform a search based on the selected filters and populate the Treeview with results."""
        try:
            status = self.status_filter.get().strip()
            search_by = self.search_filter.get().strip()
            search_value = self.search_entry.get().strip()

            query = "SELECT id, customer_id, status, technician FROM work_orders WHERE 1=1"
            params = []

            if status:
                query += " AND status = %s"
                params.append(status)

            if search_by == "Technician" and search_value:
                query += " AND technician LIKE %s"
                params.append(f"%{search_value}%")
            elif search_by == "Priority" and search_value:
                query += " AND priority = %s"
                params.append(search_value)
            elif search_by == "Date Range" and "to" in search_value:
                start_date, end_date = map(str.strip, search_value.split("to", 1))
                query += " AND created_at BETWEEN %s AND %s"
                params.extend([start_date, end_date])

            results = execute_query(query, tuple(params))

            # Clear and repopulate
            self.search_results.delete(*self.search_results.get_children())
            for row in results:
                self.search_results.insert("", "end", values=row)

            messagebox.showinfo("Search", f"Found {len(results)} result(s).")
        except ValueError as ve:
            messagebox.showerror("Validation Error", str(ve))
        except DatabaseError as de:
            messagebox.showerror("Database Error", f"An error occurred while searching: {de}")

    # -----------------------------------------------------------------------
    # Details
    # -----------------------------------------------------------------------
    def setup_details_tab(self):
        """Setup tab to show work order details (no duplication)."""
        row = 0

        # Quick find by ID
        ttk.Label(self.details_tab, text="Find WO ID:").grid(row=row, column=0, padx=10, pady=10, sticky="e")
        self.quick_wid_entry = ttk.Entry(self.details_tab, width=12)
        self.quick_wid_entry.grid(row=row, column=1, padx=10, pady=10, sticky="w")
        ttk.Button(self.details_tab, text="Load", command=self._quick_load_wo).grid(row=row, column=2, padx=10, pady=10)
        row += 1

        # Work order details fields (use the running row)
        ttk.Label(self.details_tab, text="Work Order Number:").grid(row=row, column=0, padx=10, pady=10, sticky="e")
        self.work_order_number = ttk.Entry(self.details_tab, state="readonly")
        self.work_order_number.grid(row=row, column=1, padx=10, pady=10, sticky="w")
        row += 1

        ttk.Label(self.details_tab, text="Assigned Technician:").grid(row=row, column=0, padx=10, pady=10, sticky="e")
        self.assigned_technician = ttk.Entry(self.details_tab)
        self.assigned_technician.grid(row=row, column=1, padx=10, pady=10, sticky="w")
        row += 1

        ttk.Label(self.details_tab, text="Work Order Type:").grid(row=row, column=0, padx=10, pady=10, sticky="e")
        self.work_order_type = ttk.Combobox(self.details_tab, values=WORK_ORDER_TYPES, state="readonly")
        self.work_order_type.grid(row=row, column=1, padx=10, pady=10, sticky="w")
        row += 1

        ttk.Label(self.details_tab, text="Priority:").grid(row=row, column=0, padx=10, pady=10, sticky="e")
        self.priority = ttk.Combobox(self.details_tab, values=PRIORITIES, state="readonly")
        self.priority.grid(row=row, column=1, padx=10, pady=10, sticky="w")
        row += 1

        # Device information
        ttk.Label(self.details_tab, text="Device Type:").grid(row=row, column=0, padx=10, pady=10, sticky="e")
        self.device_type = ttk.Combobox(self.details_tab, values=DEVICE_TYPES, state="readonly")
        self.device_type.grid(row=row, column=1, padx=10, pady=10, sticky="w")
        row += 1

        ttk.Label(self.details_tab, text="Manufacturer:").grid(row=row, column=0, padx=10, pady=10, sticky="e")
        self.manufacturer = ttk.Entry(self.details_tab)
        self.manufacturer.grid(row=row, column=1, padx=10, pady=10, sticky="w")
        row += 1

        ttk.Label(self.details_tab, text="Model:").grid(row=row, column=0, padx=10, pady=10, sticky="e")
        self.model = ttk.Entry(self.details_tab)
        self.model.grid(row=row, column=1, padx=10, pady=10, sticky="w")
        row += 1

        ttk.Label(self.details_tab, text="Serial Number (S/N):").grid(row=row, column=0, padx=10, pady=10, sticky="e")
        self.serial_number = ttk.Entry(self.details_tab)
        self.serial_number.grid(row=row, column=1, padx=10, pady=10, sticky="w")
        row += 1

        ttk.Label(self.details_tab, text="Customer ID:").grid(row=row, column=0, padx=10, pady=10, sticky="e")
        self.customer_id_entry = ttk.Entry(self.details_tab)
        self.customer_id_entry.grid(row=row, column=1, padx=10, pady=10, sticky="w")
        row += 1

        ttk.Label(self.details_tab, text="Status:").grid(row=row, column=0, padx=10, pady=10, sticky="e")
        self.status_combobox = ttk.Combobox(self.details_tab, values=STATUSES, state="readonly")
        self.status_combobox.grid(row=row, column=1, padx=10, pady=10, sticky="w")
        row += 1

        ttk.Label(self.details_tab, text="Notes:").grid(row=row, column=0, padx=10, pady=10, sticky="ne")
        self.notes_text = tk.Text(self.details_tab, height=4, width=40)
        self.notes_text.grid(row=row, column=1, padx=10, pady=10, sticky="nsew")
        row += 1

        # Layout stretch
        for r in range(row):
            self.details_tab.rowconfigure(r, weight=0)
        self.details_tab.rowconfigure(row - 1, weight=1)  # notes area expands
        self.details_tab.columnconfigure(1, weight=1)

    def _quick_load_wo(self):
        try:
            wid = int(self.quick_wid_entry.get().strip())
        except Exception:
            messagebox.showerror("Find", "Enter a numeric Work Order ID.")
            return
        self.load_work_order_by_id(wid)

    # -----------------------------------------------------------------------
    # Parts
    # -----------------------------------------------------------------------
    def setup_parts_tab(self):
        ttk.Label(self.parts_tab, text="Part Name:").grid(row=0, column=0, padx=10, pady=10, sticky="e")
        self.part_name = ttk.Entry(self.parts_tab)
        self.part_name.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        ttk.Label(self.parts_tab, text="Manufacturer:").grid(row=1, column=0, padx=10, pady=10, sticky="e")
        self.part_manufacturer = ttk.Entry(self.parts_tab)
        self.part_manufacturer.grid(row=1, column=1, padx=10, pady=10, sticky="w")

        ttk.Label(self.parts_tab, text="Model:").grid(row=2, column=0, padx=10, pady=10, sticky="e")
        self.part_model = ttk.Entry(self.parts_tab)
        self.part_model.grid(row=2, column=1, padx=10, pady=10, sticky="w")

        ttk.Label(self.parts_tab, text="Serial Number (S/N) or Part Number:").grid(row=3, column=0, padx=10, pady=10, sticky="e")
        self.part_serial_number = ttk.Entry(self.parts_tab)
        self.part_serial_number.grid(row=3, column=1, padx=10, pady=10, sticky="w")

        ttk.Label(self.parts_tab, text="Quantity:").grid(row=4, column=0, padx=10, pady=10, sticky="e")
        self.part_quantity = ttk.Entry(self.parts_tab)
        self.part_quantity.grid(row=4, column=1, padx=10, pady=10, sticky="w")

    # -----------------------------------------------------------------------
    # Manager Workbench
    # -----------------------------------------------------------------------
    def setup_workbench_tab(self):
        ttk.Label(self.workbench_tab, text="Manager Workbench").grid(row=0, column=0, padx=10, pady=10)

        self.workbench_list = ttk.Treeview(
            self.workbench_tab,
            columns=("ID", "Customer", "Status", "Technician"),
            show="headings",
        )
        self.workbench_list.heading("ID", text="ID")
        self.workbench_list.heading("Customer", text="Customer")
        self.workbench_list.heading("Status", text="Status")
        self.workbench_list.heading("Technician", text="Technician")
        self.workbench_list.grid(row=1, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")

        # Placeholder data
        sample_data = [
            (101, "Customer A", "Completed by Technician", "Technician A"),
            (102, "Customer B", "Completed by Technician", "Technician B"),
        ]
        for item in sample_data:
            self.workbench_list.insert("", "end", values=item)

        self.review_button = ttk.Button(self.workbench_tab, text="Review Work Order", command=self.review_work_order)
        self.review_button.grid(row=2, column=0, padx=10, pady=10)

        self.close_button = ttk.Button(self.workbench_tab, text="Close Work Order", command=self.close_work_order)
        self.close_button.grid(row=2, column=1, padx=10, pady=10)

        # stretch
        self.workbench_tab.rowconfigure(1, weight=1)
        self.workbench_tab.columnconfigure(0, weight=1)
        self.workbench_tab.columnconfigure(1, weight=1)

    def refresh_notifications(self):
        try:
            self.workbench_list.delete(*self.workbench_list.get_children())

            twenty_four_hours_ago = datetime.datetime.now() - datetime.timedelta(hours=24)
            excluded_days = [4, 5, 6]  # Fri, Sat, Sun (Mon=0)

            notifications = get_notifications(twenty_four_hours_ago, excluded_days)
            for notification in notifications:
                self.workbench_list.insert("", "end", values=notification)

            messagebox.showinfo("Refresh", "Notifications refreshed.")
        except mysql.connector.Error:
            messagebox.showerror("Database Error", "An error occurred while accessing the database.")
        except TimeoutError as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")

    def review_work_order(self):
        sel = self.workbench_list.selection()
        if sel:
            messagebox.showinfo("Review", "Reviewing selected work order...")
        else:
            messagebox.showwarning("Warning", "Please select a work order to review.")

    def close_work_order(self):
        sel = self.workbench_list.selection()
        if sel:
            work_order_id = self.workbench_list.item(sel[0], "values")[0]
            messagebox.showinfo(
                "Close Work Order",
                f"Work Order {work_order_id} closed. Customer contact alert set for 24 hours.",
            )
        else:
            messagebox.showwarning("Warning", "Please select a work order to close.")

    # -----------------------------------------------------------------------
    # Attachments
    # -----------------------------------------------------------------------
    def setup_attachments_tab(self):
        self.upload_button = ttk.Button(self.attachments_tab, text="Upload File", command=self.upload_file)
        self.upload_button.grid(row=0, column=0, padx=10, pady=10)

        self.attachments_list = ttk.Treeview(
            self.attachments_tab,
            columns=("File Name", "File Type", "Uploaded At"),
            show="headings",
        )
        self.attachments_list.heading("File Name", text="File Name")
        self.attachments_list.heading("File Type", text="File Type")
        self.attachments_list.heading("Uploaded At", text="Uploaded At")
        self.attachments_list.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

        self.attachments_tab.rowconfigure(1, weight=1)
        self.attachments_tab.columnconfigure(0, weight=1)

    def upload_file(self):
        file_path = filedialog.askopenfilename()
        if not file_path:
            return

        file_name = os.path.basename(file_path)
        file_type = file_name.split(".")[-1] if "." in file_name else ""

        work_order_id_text = self.work_order_number.get().strip()
        if not work_order_id_text:
            messagebox.showerror("Error", "Work Order ID is required to attach files.")
            return
        try:
            work_order_id = int(work_order_id_text)
        except Exception:
            messagebox.showerror("Error", "Work Order ID must be numeric.")
            return

        insert_file_metadata(work_order_id, file_name, file_path, file_type)
        messagebox.showinfo("Success", f"File '{file_name}' uploaded successfully!")

        # Optional: show in list with current timestamp
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.attachments_list.insert("", "end", values=(file_name, file_type, now_str))

    # -----------------------------------------------------------------------
    # Actions
    # -----------------------------------------------------------------------
    def setup_actions_tab(self):
        self.add_work_order_button = ttk.Button(self.actions_tab, text="Add Work Order", command=self.handle_add_work_order)
        self.add_work_order_button.grid(row=0, column=0, padx=10, pady=10)

        self.edit_work_order_button = ttk.Button(self.actions_tab, text="Edit Work Order", command=self.handle_edit_current)
        self.edit_work_order_button.grid(row=0, column=1, padx=10, pady=10)

        self.delete_work_order_button = ttk.Button(self.actions_tab, text="Delete Work Order", command=self.handle_delete_current)
        self.delete_work_order_button.grid(row=0, column=2, padx=10, pady=10)

        # IMPORTANT: bind to a handler that reads fields, not the DB method directly
        self.save_note_button = ttk.Button(self.actions_tab, text="Save/Edit Note", command=self.handle_save_note)
        self.save_note_button.grid(row=0, column=3, padx=10, pady=10)

    def validate_work_order_data(self, data):
        """Validate collected work order data."""
        if not data.get("customer_id"):
            raise ValueError("Customer ID is required.")
        if not data.get("status"):
            raise ValueError("Status is required.")
        if not data.get("priority"):
            raise ValueError("Priority is required.")
        if not data.get("technician"):
            raise ValueError("Technician is required.")

    def handle_add_work_order(self):
        """Handle the process of adding a work order with validation."""
        try:
            data = self.collect_work_order_data()
            self.validate_work_order_data(data)
            self.add_work_order(data)
        except ValueError as ve:
            messagebox.showerror("Validation Error", str(ve))

    def add_work_order(self, data):
        """Add a new work order, then load it into the form."""
        try:
            db_add_work_order(data)
            # NOTE: LAST_INSERT_ID() is connection-specific. Ensure the same connection is used.
            row = fetch_one("SELECT LAST_INSERT_ID()")
            new_id = row[0] if row else None
            messagebox.showinfo("Add Work Order", f"Work order added successfully. ID: {new_id or 'Unknown'}")
            if new_id:
                self.load_work_order_by_id(new_id)
        except DatabaseError as e:
            messagebox.showerror("Database Error", f"Failed to add work order: {e}")

    def edit_work_order(self, work_order_id, data):
        """Edit an existing work order and notify the user."""
        try:
            query = """
                UPDATE work_orders
                SET status = %s, priority = %s, technician = %s, notes = %s
                WHERE id = %s
            """
            execute_query(
                query,
                (data["status"], data["priority"], data["technician"], data["notes"], work_order_id),
                commit=True,
            )
            messagebox.showinfo("Edit Work Order", "Work order updated successfully.")
        except DatabaseError as e:
            messagebox.showerror("Database Error", f"Failed to edit work order: {e}")

    def delete_work_order(self, work_order_id):
        """Delete a work order from the database and notify the user."""
        try:
            query = "DELETE FROM work_orders WHERE id = %s"
            execute_query(query, (work_order_id,), commit=True)
            messagebox.showinfo("Delete Work Order", "Work order deleted successfully.")
        except DatabaseError as e:
            messagebox.showerror("Database Error", f"Failed to delete work order: {e}")

    # --- Notes helpers ------------------------------------------------------
    def handle_save_note(self):
        """Read current form values and save a customer note."""
        customer_id = self.customer_id_entry.get().strip() if hasattr(self, "customer_id_entry") else ""
        note = self.notes_text.get("1.0", "end-1c").strip() if hasattr(self, "notes_text") else ""
        if not customer_id:
            messagebox.showerror("Save Note", "Customer ID is required.")
            return
        if not note:
            messagebox.showerror("Save Note", "Note text is empty.")
            return
        try:
            cid_int = int(customer_id)
        except Exception:
            messagebox.showerror("Save Note", "Customer ID must be numeric.")
            return
        self._save_note_to_db(cid_int, note)

    def _save_note_to_db(self, customer_id, note):
        """Persist a note to the DB."""
        try:
            query = """
                INSERT INTO customer_notes (customer_id, note, created_at)
                VALUES (%s, %s, NOW())
            """
            execute_query(query, (customer_id, note), commit=True)
            messagebox.showinfo("Save Note", "Note saved successfully.")
        except DatabaseError as e:
            messagebox.showerror("Database Error", f"Failed to save note: {e}")

    # -----------------------------------------------------------------------
    # Data collection / loading
    # -----------------------------------------------------------------------
    def collect_work_order_data(self):
        """Collect work order details from the input fields in the tab."""
        try:
            return {
                "customer_id": self.customer_id_entry.get().strip(),
                "status": self.status_combobox.get().strip(),
                "priority": self.priority.get().strip(),
                "technician": self.assigned_technician.get().strip(),
                "notes": self.notes_text.get("1.0", "end-1c").strip(),
            }
        except AttributeError as e:
            raise ValueError(f"Failed to collect data: {e}") from e

    def _on_search_row_open(self, _event=None):
        """Double-click handler: open the selected work order into the Details tab."""
        sel = self.search_results.selection()
        if not sel:
            return
        values = self.search_results.item(sel[0], "values")
        try:
            work_order_id = int(values[0])  # first column is ID
        except Exception:
            messagebox.showerror("Open", "Could not read Work Order ID from selection.")
            return
        self.load_work_order_by_id(work_order_id)

    def load_work_order_by_id(self, work_order_id: int):
        """
        Populate all Details fields for a given Work Order ID.
        Tries extended columns first; falls back to minimal set if missing.
        """
        def _populate_from_tuple(t, extended=False):
            if extended:
                (wid, customer_id, tech, status, priority, notes,
                 wotype, dev_type, manu, mdl, serial) = t
            else:
                (wid, customer_id, tech, status, priority, notes) = t
                wotype = dev_type = manu = mdl = serial = None

            # Work order number (readonly)
            self.work_order_number.config(state="normal")
            self.work_order_number.delete(0, "end")
            self.work_order_number.insert(0, str(wid))
            self.work_order_number.config(state="readonly")

            # Core fields
            self.customer_id_entry.delete(0, "end")
            self.customer_id_entry.insert(0, str(customer_id) if customer_id is not None else "")

            self.assigned_technician.delete(0, "end")
            self.assigned_technician.insert(0, tech or "")

            self.status_combobox.set(status or "")
            self.priority.set(priority or "")

            self.notes_text.delete("1.0", "end")
            self.notes_text.insert("1.0", notes or "")

            # Extended (best-effort)
            try:
                if hasattr(self, "work_order_type"):
                    self.work_order_type.set(wotype or "")
            except Exception:
                pass
            try:
                if hasattr(self, "device_type"):
                    self.device_type.set(dev_type or "")
            except Exception:
                pass
            try:
                self.manufacturer.delete(0, "end")
                self.manufacturer.insert(0, manu or "")
            except Exception:
                pass
            try:
                self.model.delete(0, "end")
                self.model.insert(0, mdl or "")
            except Exception:
                pass
            try:
                self.serial_number.delete(0, "end")
                self.serial_number.insert(0, serial or "")
            except Exception:
                pass

            self.notebook.select(self.details_tab)

        try:
            # Try extended columns first
            row = fetch_one(
                """
                SELECT id, customer_id, technician, status, priority, notes,
                       work_order_type, device_type, manufacturer, model, serial_number
                FROM work_orders
                WHERE id = %s
                """,
                (work_order_id,),
            )
            if row:
                _populate_from_tuple(row, extended=True)
                return
            messagebox.showerror("Work Order", f"Work order {work_order_id} not found.")
        except Exception:
            # Fallback to minimal set
            try:
                row = fetch_one(
                    """
                    SELECT id, customer_id, technician, status, priority, notes
                    FROM work_orders
                    WHERE id = %s
                    """,
                    (work_order_id,),
                )
                if row:
                    _populate_from_tuple(row, extended=False)
                    return
                messagebox.showerror("Work Order", f"Work order {work_order_id} not found.")
            except Exception as e:
                messagebox.showerror("Work Order", f"Failed to load work order {work_order_id}: {e}")

    def show_work_order_list_for_customer(self, customer_id: int):
        """Populate the Search tab with this customer's work orders and switch to it."""
        try:
            rows = fetch_all(
                """
                SELECT id, customer_id, status, technician
                FROM work_orders
                WHERE customer_id = %s
                ORDER BY created_at DESC
                """,
                (customer_id,),
            )
            if hasattr(self, "search_results"):
                self.search_results.delete(*self.search_results.get_children())
                for r in rows:
                    self.search_results.insert("", "end", values=r)

            if hasattr(self, "notebook") and hasattr(self, "search_tab"):
                self.notebook.select(self.search_tab)
        except Exception as e:
            messagebox.showerror("Work Orders", f"Failed to load list for customer {customer_id}: {e}")

    def load_work_order(self, work_order_id: int):
        """Load a single work order into the Details tab. Fills the widgets that exist."""
        try:
            row = fetch_one(
                """
                SELECT id, technician, status, priority, notes
                FROM work_orders
                WHERE id = %s
                """,
                (work_order_id,),
            )
            if not row:
                messagebox.showerror("Work Order", f"Work order {work_order_id} not found.")
                return

            wid, tech, status, priority, notes = row

            if hasattr(self, "work_order_number"):
                self.work_order_number.config(state="normal")
                self.work_order_number.delete(0, "end")
                self.work_order_number.insert(0, str(wid))
                self.work_order_number.config(state="readonly")

            if hasattr(self, "assigned_technician"):
                self.assigned_technician.delete(0, "end")
                self.assigned_technician.insert(0, tech or "")

            if hasattr(self, "priority"):
                try:
                    self.priority.set(priority or "")
                except Exception:
                    pass

            if hasattr(self, "notes_text"):
                try:
                    self.notes_text.delete("1.0", "end")
                    self.notes_text.insert("1.0", notes or "")
                except Exception:
                    pass

            if hasattr(self, "notebook") and hasattr(self, "details_tab"):
                self.notebook.select(self.details_tab)
        except Exception as e:
            messagebox.showerror("Work Order", f"Failed to load work order {work_order_id}: {e}")
