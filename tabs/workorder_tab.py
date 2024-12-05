import os
import datetime
from tkinter import ttk, filedialog, messagebox
import mysql.connector
from database import (
                        insert_file_metadata,
                        get_notifications,
                        execute_query,
                        DatabaseError,
                        add_work_order as db_add_work_order
                    )
class WorkOrderTab:
    """
    Generate workorder tab layout and GUIS
    """
    def __init__(self, parent_frame):
        self.parent_frame = parent_frame

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
        # Search filters
        ttk.Label(self.search_tab, text="Status:").grid(row=0, column=0, padx=10, pady=10)
        self.status_filter = ttk.Combobox(self.search_tab, values=["Open", "Closed", "On Hold"])
        self.status_filter.grid(row=0, column=1, padx=10, pady=10)

        ttk.Label(self.search_tab, text="Search By:").grid(row=0, column=2, padx=10, pady=10)
        self.search_filter = ttk.Combobox(self.search_tab, values=["Technician", "Priority", "Date Range"])
        self.search_filter.grid(row=0, column=3, padx=10, pady=10)

        self.search_entry = ttk.Entry(self.search_tab)
        self.search_entry.grid(row=0, column=4, padx=10, pady=10)

        self.search_button = ttk.Button(self.search_tab, text="Search", command=self.perform_search)
        self.search_button.grid(row=0, column=5, padx=10, pady=10)

        # Search results
        self.search_results = ttk.Treeview(self.search_tab, columns=("ID", "Customer", "Status", "Technician"), show="headings")
        self.search_results.heading("ID", text="ID")
        self.search_results.heading("Customer", text="Customer")
        self.search_results.heading("Status", text="Status")
        self.search_results.heading("Technician", text="Technician")
        self.search_results.grid(row=1, column=0, columnspan=6, padx=10, pady=10)

    def perform_search(self):
        # Placeholder for search functionality
        messagebox.showinfo("Search", "Performing search...")

    def setup_details_tab(self):
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


        self.edit_work_order_button = ttk.Button(self.actions_tab, text="Edit Work Order", command=self.edit_work_order)
        self.edit_work_order_button.grid(row=0, column=1, padx=10, pady=10)

        self.delete_work_order_button = ttk.Button(self.actions_tab, text="Delete Work Order", command=self.delete_work_order)
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
        Add a new work order to the database and notify the user.
        """
        try:
            # Call the database function
            db_add_work_order(data)
            # Notify the user of success
            messagebox.showinfo("Add Work Order", "Work order added successfully.")
        except DatabaseError as e:
            # Notify the user of any database errors
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
                "customer_id": self.customer_id_entry.get().strip(),  # Assume you have an entry field for Customer ID
                "status": self.status_combobox.get(),                # Assume you have a combobox for status
                "priority": self.priority_combobox.get(),            # Assume you have a combobox for priority
                "technician": self.technician_combobox.get(),        # Assume you have a combobox for technician
                "notes": self.notes_text.get("1.0", "end-1c").strip()  # Text widget for notes
            }
        except AttributeError as e:
            raise ValueError(f"Failed to collect data: {e}") from e
