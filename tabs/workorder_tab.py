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
Date: 12-2-24
"""
import os
import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import mysql.connector
from database import (
insert_file_metadata,
get_notifications,
execute_query,DatabaseError,
add_work_order as db_add_work_order,
fetch_one, fetch_all,
)
class WorkOrderTab:
    """
    Generate workorder tab layout and GUIS
    """
    def __init__(self, parent_frame, user_role="technician"):
        self.parent_frame = parent_frame
        self.user_role = user_role

        # Create Notebook for Tabs within the work order section
        self.notebook = ttk.Notebook(parent_frame)
        self.notebook.pack(fill='both', expand=True)

        # Search Tab
        self.search_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.search_tab, text='Search')
        self.setup_search_tab()

        # Work Order Details Tab
        self.details_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.details_tab, text='Work Order Details')
        self.setup_details_tab()

        # Parts Tab
        self.parts_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.parts_tab, text='Parts')
        self.setup_parts_tab()

        # Attachments Tab
        self.attachments_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.attachments_tab, text='Attachments')
        self.setup_attachments_tab()

        # Actions Tab
        self.actions_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.actions_tab, text='Actions')
        self.setup_actions_tab()

        # Manager Workbench Tab
        self.workbench_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.workbench_tab, text='Manager Workbench')
        self.setup_workbench_tab()

    def setup_search_tab(self):
        """
        Setup search tab GUI.
        """
        # Search filters
        ttk.Label(self.search_tab, text="Status:").grid(row=0, column=0, padx=10, pady=10)
        self.status_filter = ttk.Combobox(self.search_tab, values=["Open", "Closed", "On Hold"])
        self.status_filter.grid(row=0, column=1, padx=10, pady=10)

        ttk.Label(self.search_tab, text="Search By:").grid(row=0, column=2, padx=10, pady=10)
        self.search_filter = ttk.Combobox(self.search_tab,
                values=["Technician", "Priority", "Date Range"])
        self.search_filter.grid(row=0, column=3, padx=10, pady=10)

        self.search_entry = ttk.Entry(self.search_tab)
        self.search_entry.grid(row=0, column=4, padx=10, pady=10)

        self.search_button = ttk.Button(self.search_tab, text="Search", command=self.perform_search)
        self.search_button.grid(row=0, column=5, padx=10, pady=10)

        # Search results
        self.search_results = ttk.Treeview(self.search_tab,
                columns=("ID", "Customer", "Status", "Technician"), show="headings")
        self.search_results.heading("ID", text="ID")
        self.search_results.heading("Customer", text="Customer")
        self.search_results.heading("Status", text="Status")
        self.search_results.heading("Technician", text="Technician")
        self.search_results.grid(row=1, column=0, columnspan=6, padx=10, pady=10)
        self.search_results.bind("<Double-1>", self._on_search_row_open)

    def perform_search(self):
        """
        Perform a search based on the selected filters and populate the Treeview with results.
        """
        try:
            # Collect filter values
            status = self.status_filter.get()
            search_by = self.search_filter.get()
            search_value = self.search_entry.get().strip()

            # Build the query dynamically based on user input
            query = "SELECT id, customer_id, status, technician FROM work_orders WHERE 1=1"
            params = []

            # Add filters to the query
            if status:
                query += " AND status = %s"
                params.append(status)

            if search_by == "Technician":
                query += " AND technician LIKE %s"
                params.append(f"%{search_value}%")
            elif search_by == "Priority":
                query += " AND priority = %s"
                params.append(search_value)
            elif search_by == "Date Range":
                # Assuming date range input in a specific format (e.g., "YYYY-MM-DD to YYYY-MM-DD")
                if "to" in search_value:
                    start_date, end_date = map(str.strip, search_value.split("to"))
                    query += " AND created_at BETWEEN %s AND %s"
                    params.extend([start_date, end_date])

            # Execute the query
            results = execute_query(query, tuple(params))

            # Clear existing Treeview entries
            self.search_results.delete(*self.search_results.get_children())

            # Populate the Treeview with search results
            for row in results:
                self.search_results.insert("", "end", values=row)

            # Show a success message
            messagebox.showinfo("Search", f"Found {len(results)} results.")

        except ValueError as ve:
            # Handle validation issues
            messagebox.showerror("Validation Error", str(ve))
        except DatabaseError as de:
            # Handle database-related errors
            messagebox.showerror("Database Error", f"An error occurred while searching: {de}")

    def setup_details_tab(self):
        # Quick find by ID
        row = 0
        ttk.Label(self.details_tab, text="Find WO ID:").grid(row=row, column=0, padx=10, pady=10, sticky="e")
        self.quick_wid_entry = ttk.Entry(self.details_tab, width=12)
        self.quick_wid_entry.grid(row=row, column=1, padx=10, pady=10, sticky="w")
        ttk.Button(self.details_tab, text="Load", command=lambda: self._quick_load_wo()).grid(row=row, column=2, padx=10, pady=10)
        row += 1  # shift starting row for the rest

        # then shift all your existing rows down by using 'row' variable
        ttk.Label(self.details_tab, text="Work Order Number:").grid(row=row, column=0, padx=10, pady=10)
        self.work_order_number = ttk.Entry(self.details_tab, state='readonly')
        self.work_order_number.grid(row=row, column=1, padx=10, pady=10); row += 1
        # ...and continue replacing your hard-coded row numbers with 'row += 1'

        """
        Setup tab to show work order details.
        """
        # Work order details fields
        ttk.Label(self.details_tab, text="Work Order Number:").grid(row=0, column=0, padx=10, pady=10)
        self.work_order_number = ttk.Entry(self.details_tab, state='readonly')
        self.work_order_number.grid(row=0, column=1, padx=10, pady=10)

        ttk.Label(self.details_tab, text="Assigned Technician:").grid(row=1, column=0, padx=10, pady=10)
        self.assigned_technician = ttk.Entry(self.details_tab)
        self.assigned_technician.grid(row=1, column=1, padx=10, pady=10)

        ttk.Label(self.details_tab, text="Work Order Type:").grid(row=2, column=0, padx=10, pady=10)
        self.work_order_type = ttk.Combobox(self.details_tab, values=["Troubleshoot", "Upgrade", "Maintenance"])
        self.work_order_type.grid(row=2, column=1, padx=10, pady=10)

        ttk.Label(self.details_tab, text="Priority:").grid(row=3, column=0, padx=10, pady=10)
        self.priority = ttk.Combobox(self.details_tab, values=["Low", "Medium", "High", "Critical"])
        self.priority.grid(row=3, column=1, padx=10, pady=10)

        # Device information
        ttk.Label(self.details_tab, text="Device Type:").grid(row=4, column=0, padx=10, pady=10)
        self.device_type = ttk.Combobox(self.details_tab, values=["Laptop", "Tablet", "Desktop"])
        self.device_type.grid(row=4, column=1, padx=10, pady=10)

        ttk.Label(self.details_tab, text="Manufacturer:").grid(row=5, column=0, padx=10, pady=10)
        self.manufacturer = ttk.Entry(self.details_tab)
        self.manufacturer.grid(row=5, column=1, padx=10, pady=10)

        ttk.Label(self.details_tab, text="Model:").grid(row=6, column=0, padx=10, pady=10)
        self.model = ttk.Entry(self.details_tab)
        self.model.grid(row=6, column=1, padx=10, pady=10)

        ttk.Label(self.details_tab, text="Serial Number (S/N):").grid(row=7, column=0, padx=10, pady=10)
        self.serial_number = ttk.Entry(self.details_tab)
        self.serial_number.grid(row=7, column=1, padx=10, pady=10)
        # Customer ID
        ttk.Label(self.details_tab, text="Customer ID:").grid(row=8, column=0, padx=10, pady=10)
        self.customer_id_entry = ttk.Entry(self.details_tab)
        self.customer_id_entry.grid(row=8, column=1, padx=10, pady=10)

        # Status
        ttk.Label(self.details_tab, text="Status:").grid(row=9, column=0, padx=10, pady=10)
        self.status_combobox = ttk.Combobox(
            self.details_tab,
            values=["Active", "On Hold", "Completed", "Closed", "Pending"]
        )
        self.status_combobox.grid(row=9, column=1, padx=10, pady=10)

        # Notes
        ttk.Label(self.details_tab, text="Notes:").grid(row=10, column=0, padx=10, pady=10)
        self.notes_text = tk.Text(self.details_tab, height=4, width=40)
        self.notes_text.grid(row=10, column=1, padx=10, pady=10, sticky="w")
        for i in range(0, 11):
            self.details_tab.rowconfigure(i, weight=1)
        self.details_tab.columnconfigure(1, weight=1)

        # Quick find by Work Order ID (on the Details tab itself)
        ttk.Label(self.details_tab, text="Find WO ID:").grid(row=0, column=0, padx=10, pady=10, sticky="e")
        self.quick_wid_entry = ttk.Entry(self.details_tab, width=12)
        self.quick_wid_entry.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        ttk.Button(self.details_tab, text="Load", command=self._quick_load_wo)\
        .grid(row=0, column=2, padx=10, pady=10)

    def _quick_load_wo(self):
        try:
            wid = int(self.quick_wid_entry.get().strip())
        except Exception:
            messagebox.showerror("Find", "Enter a numeric Work Order ID.")
            return
        self.load_work_order_by_id(wid)

    def setup_parts_tab(self):
        # Parts fields
        ttk.Label(self.parts_tab, text="Part Name:").grid(row=0, column=0, padx=10, pady=10)
        self.part_name = ttk.Entry(self.parts_tab)
        self.part_name.grid(row=0, column=1, padx=10, pady=10)

        ttk.Label(self.parts_tab, text="Manufacturer:").grid(row=1, column=0, padx=10, pady=10)
        self.part_manufacturer = ttk.Entry(self.parts_tab)
        self.part_manufacturer.grid(row=1, column=1, padx=10, pady=10)

        ttk.Label(self.parts_tab, text="Model:").grid(row=2, column=0, padx=10, pady=10)
        self.part_model = ttk.Entry(self.parts_tab)
        self.part_model.grid(row=2, column=1, padx=10, pady=10)

        ttk.Label(self.parts_tab, text="Serial Number (S/N) or Part Number:").grid(row=3, column=0, padx=10, pady=10)
        self.part_serial_number = ttk.Entry(self.parts_tab)
        self.part_serial_number.grid(row=3, column=1, padx=10, pady=10)

        ttk.Label(self.parts_tab, text="Quantity:").grid(row=4, column=0, padx=10, pady=10)
        self.part_quantity = ttk.Entry(self.parts_tab)
        self.part_quantity.grid(row=4, column=1, padx=10, pady=10)

    def setup_workbench_tab(self):
        # Label for manager workbench section
        ttk.Label(self.workbench_tab, text="Manager Workbench").grid(row=0, column=0, padx=10, pady=10)

        # TreeView for displaying work orders awaiting managerial closure
        self.workbench_list = ttk.Treeview(self.workbench_tab, columns=("ID", "Customer", "Status", "Technician"), show="headings")
        self.workbench_list.heading("ID", text="ID")
        self.workbench_list.heading("Customer", text="Customer")
        self.workbench_list.heading("Status", text="Status")
        self.workbench_list.heading("Technician", text="Technician")
        self.workbench_list.grid(row=1, column=0, columnspan=3, padx=10, pady=10)

        # Populate with pending work orders (placeholder)
        sample_data = [
            (101, "Customer A", "Completed by Technician", "Technician A"),
            (102, "Customer B", "Completed by Technician", "Technician B"),
        ]
        for item in sample_data:
            self.workbench_list.insert("", "end", values=item)

        # Action Buttons for Managers
        self.review_button = ttk.Button(self.workbench_tab, text="Review Work Order", command=self.review_work_order)
        self.review_button.grid(row=2, column=0, padx=10, pady=10)

        self.close_button = ttk.Button(self.workbench_tab, text="Close Work Order", command=self.close_work_order)
        self.close_button.grid(row=2, column=1, padx=10, pady=10)

    def refresh_notifications(self):
        try:
            # Clear existing entries
            self.workbench_list.delete(*self.workbench_list.get_children())

            # Define the 24-hour threshold and days to exclude
            twenty_four_hours_ago = datetime.datetime.now() - datetime.timedelta(hours=24)
            excluded_days = [4, 5, 6]  # Friday, Saturday, Sunday

            # Fetch notifications using the function from database.py
            notifications = get_notifications(twenty_four_hours_ago, excluded_days)

            # Populate the workbench list in the GUI
            for notification in notifications:
                self.workbench_list.insert("", "end", values=notification)

            # Show info message
            messagebox.showinfo("Refresh", "Notifications refreshed.")

        except mysql.connector.Error:
            # Handle database errors
            messagebox.showerror("Database Error", "An error occurred while accessing the database.")
        except TimeoutError as e:
            # Handle other exceptions
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")

    def review_work_order(self):
        # Placeholder function to review selected work order
        selected_item = self.workbench_list.selection()
        if selected_item:
            messagebox.showinfo("Review", "Reviewing selected work order...")
        else:
            messagebox.showwarning("Warning", "Please select a work order to review.")

    def close_work_order(self):
        # Placeholder function to close selected work order
        selected_item = self.workbench_list.selection()
        if selected_item:
            # Start 24-hour timer for customer contact alert
            work_order_id = self.workbench_list.item(selected_item, "values")[0]
            # Implement logic to set a timer for customer contact alert
            messagebox.showinfo("Close Work Order", f"Work Order {work_order_id} closed. Customer contact alert set for 24 hours.")
        else:
            messagebox.showwarning("Warning", "Please select a work order to close.")
            
    def setup_attachments_tab(self):
        # Attachments fields
        self.upload_button = ttk.Button(self.attachments_tab, text="Upload File", command=self.upload_file)
        self.upload_button.grid(row=0, column=0, padx=10, pady=10)

        self.attachments_list = ttk.Treeview(self.attachments_tab, columns=("File Name", "File Type", "Uploaded At"), show="headings")
        self.attachments_list.heading("File Name", text="File Name")
        self.attachments_list.heading("File Type", text="File Type")
        self.attachments_list.heading("Uploaded At", text="Uploaded At")
        self.attachments_list.grid(row=1, column=0, columnspan=2, padx=10, pady=10)

    def upload_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            file_name = os.path.basename(file_path)
            file_type = file_name.split('.')[-1]
            work_order_id = self.work_order_number.get()
            if work_order_id:
                # Save metadata in the database
                insert_file_metadata(work_order_id, file_name, file_path, file_type)
                messagebox.showinfo("Success", f"File '{file_name}' uploaded successfully!")
            else:
                messagebox.showerror("Error", "Work Order ID is required to attach files.")

    def setup_actions_tab(self):
        # Action buttons
        self.add_work_order_button = ttk.Button(
            self.actions_tab,
            text="Add Work Order",
            command=self.handle_add_work_order  # Directly reference the method
        )
        self.add_work_order_button.grid(row=0, column=0, padx=10, pady=10)

        self.edit_work_order_button = ttk.Button(self.actions_tab, text="Edit Work Order", command=self.handle_edit_current)
        self.edit_work_order_button.grid(row=0, column=1, padx=10, pady=10)

        self.delete_work_order_button = ttk.Button(self.actions_tab, text="Delete Work Order", command=self.handle_delete_current)
        self.delete_work_order_button.grid(row=0, column=2, padx=10, pady=10)

        self.save_note_button = ttk.Button(self.actions_tab, text="Save/Edit Note", command=self.save_note)
        self.save_note_button.grid(row=0, column=3, padx=10, pady=10)

    def validate_work_order_data(self, data):
        """
        Validate collected work order data.
        """
        if not data.get("customer_id"):
            raise ValueError("Customer ID is required.")
        if not data.get("status"):
            raise ValueError("Status is required.")
        if not data.get("priority"):
            raise ValueError("Priority is required.")
        if not data.get("technician"):
            raise ValueError("Technician is required.")
        # Add additional checks as necessary

    def handle_add_work_order(self):
        """
        Handle the process of adding a work order with validation.
        """
        try:
            data = self.collect_work_order_data()  # Collect data from the form
            self.validate_work_order_data(data)    # Validate the collected data
            self.add_work_order(data)              # Pass the data to the add_work_order method
        except ValueError as ve:
            messagebox.showerror("Validation Error", str(ve))

    def add_work_order(self, data):
        """
        Add a new work order, then load it into the form.
        """
        try:
            db_add_work_order(data)
            # fetch the new id
            row = fetch_one("SELECT LAST_INSERT_ID()")
            new_id = row[0] if row else None
            messagebox.showinfo("Add Work Order", f"Work order added successfully. ID: {new_id or 'Unknown'}")
            if new_id:
                self.load_work_order_by_id(new_id)
            # optionally refresh search results
            # self.perform_search()
        except DatabaseError as e:
            messagebox.showerror("Database Error", f"Failed to add work order: {e}")

    def edit_work_order(self, work_order_id, data):
        """
        Edit an existing work order and notify the user.
        """
        try:
            query = """
            UPDATE work_orders 
            SET status = %s, priority = %s, technician = %s, notes = %s 
            WHERE id = %s
            """
            execute_query(query, (
                data["status"], data["priority"], data["technician"],
                data["notes"], work_order_id
            ), commit=True)
            messagebox.showinfo("Edit Work Order", "Work order updated successfully.")
        except DatabaseError as e:
            messagebox.showerror("Database Error", f"Failed to edit work order: {e}")

    def delete_work_order(self, work_order_id):
        """
        Delete a work order from the database and notify the user.
        """
        try:
            query = "DELETE FROM work_orders WHERE id = %s"
            execute_query(query, (work_order_id,), commit=True)
            messagebox.showinfo("Delete Work Order", "Work order deleted successfully.")
        except DatabaseError as e:
            messagebox.showerror("Database Error", f"Failed to delete work order: {e}")

    def save_note(self, customer_id, note):
        """
        Save a note for a customer and notify the user.
        """
        try:
            query = """
            INSERT INTO customer_notes (customer_id, note, created_at)
            VALUES (%s, %s, NOW())
            """
            execute_query(query, (customer_id, note), commit=True)
            messagebox.showinfo("Save Note", "Note saved successfully.")
        except DatabaseError as e:
            messagebox.showerror("Database Error", f"Failed to save note: {e}")

    def collect_work_order_data(self):
        """
        Collect work order details from the input fields in the tab.
        """
        try:
            return {
                "customer_id": self.customer_id_entry.get().strip(),
                "status": self.status_combobox.get().strip(),
                "priority": self.priority.get().strip(),                 # you already have self.priority
                "technician": self.assigned_technician.get().strip(),    # you already have self.assigned_technician
                "notes": self.notes_text.get("1.0", "end-1c").strip()
            }
        except AttributeError as e:
            raise ValueError(f"Failed to collect data: {e}") from e

    def _on_search_row_open(self, event=None):
        """Double-click handler: open the selected work order into the Details tab."""
        sel = self.search_results.selection()
        if not sel:
            return
        values = self.search_results.item(sel[0], "values")
        # Treeview columns: ("ID", "Customer", "Status", "Technician")
        try:
            work_order_id = int(values[0])
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
                self.manufacturer.delete(0, "end"); self.manufacturer.insert(0, manu or "")
            except Exception:
                pass
            try:
                self.model.delete(0, "end"); self.model.insert(0, mdl or "")
            except Exception:
                pass
            try:
                self.serial_number.delete(0, "end"); self.serial_number.insert(0, serial or "")
            except Exception:
                pass

            # Show the tab
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
                (work_order_id,)
            )
            if row:
                _populate_from_tuple(row, extended=True)
                return
            messagebox.showerror("Work Order", f"Work order {work_order_id} not found.")
        except Exception:
            # If extended columns don’t exist yet, fall back to minimal set
            try:
                row = fetch_one(
                    """
                    SELECT id, customer_id, technician, status, priority, notes
                    FROM work_orders
                    WHERE id = %s
                    """,
                    (work_order_id,)
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
            # Clear & refill the search Treeview
            if hasattr(self, "search_results"):
                self.search_results.delete(*self.search_results.get_children())
                for r in rows:
                    self.search_results.insert("", "end", values=r)

            # Flip to Search tab if you keep a handle to it
            if hasattr(self, "notebook") and hasattr(self, "search_tab"):
                self.notebook.select(self.search_tab)
        except Exception as e:
            messagebox.showerror(
                "Work Orders",
                f"Failed to load list for customer {customer_id}: {e}",
            )

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
            messagebox.showerror(
                "Work Order",
                f"Failed to load work order {work_order_id}: {e}",
            )

    def prefill_from_payload(self, p: dict):
        """Best-effort prefill from scan payload."""
        try:
            if p.get("dt") and hasattr(self, "work_order_type"):
                try:
                    self.work_order_type.set(p["dt"])
                except Exception:
                    pass

            if p.get("dm") and hasattr(self, "manufacturer"):
                try:
                    self.manufacturer.delete(0, "end")
                    self.manufacturer.insert(0, p["dm"])
                except Exception:
                    pass

            if p.get("wo") and hasattr(self, "work_order_number"):
                try:
                    self.work_order_number.config(state="normal")
                    self.work_order_number.delete(0, "end")
                    self.work_order_number.insert(0, p["wo"])
                    self.work_order_number.config(state="readonly")
                except Exception:
                    pass
        except Exception:
            # prefill is best-effort
            pass

    # Optional: keep a dict-based loader for future use
    def load_work_order_from_dict(self, work_order: dict):
        """Populate Details from a dict payload (used by other parts of the app)."""
        self.work_order_number.config(state="normal")
        self.work_order_number.delete(0, "end")
        self.work_order_number.insert(0, work_order.get("id", ""))
        self.work_order_number.config(state="readonly")

        self.customer_id_entry.delete(0, "end")
        self.customer_id_entry.insert(0, work_order.get("customer_id", ""))

        self.status_combobox.set(work_order.get("status", ""))
        self.priority.set(work_order.get("priority", ""))
        self.assigned_technician.delete(0, "end")
        self.assigned_technician.insert(0, work_order.get("technician", ""))

        self.notes_text.delete("1.0", "end")
        self.notes_text.insert("1.0", work_order.get("notes", ""))

    def _current_work_order_id(self):
        try:
            wid = self.work_order_number.get().strip()
            return int(wid) if wid else None
        except Exception:
            return None

    def handle_edit_current(self):
        wid = self._current_work_order_id()
        if not wid:
            messagebox.showwarning("Edit", "No Work Order loaded.")
            return
        try:
            data = self.collect_work_order_data()
            self.validate_work_order_data(data)
            # reuse your existing edit_work_order(...)
            self.edit_work_order(wid, data)
        except ValueError as ve:
            messagebox.showerror("Validation", str(ve))

    def handle_delete_current(self):
        wid = self._current_work_order_id()
        if not wid:
            messagebox.showwarning("Delete", "No Work Order loaded.")
            return
        if not messagebox.askyesno("Confirm", f"Delete Work Order {wid}?"):
            return
        self.delete_work_order(wid)
        # clear the form a bit
        try:
            self.work_order_number.config(state="normal")
            self.work_order_number.delete(0, "end")
            self.work_order_number.config(state="readonly")
            self.customer_id_entry.delete(0, "end")
            self.assigned_technician.delete(0, "end")
            self.status_combobox.set("")
            self.priority.set("")
            self.notes_text.delete("1.0", "end")
        except Exception:
            pass
