"""
main.py

This is the entry point for the application. It initializes the main GUI
and integrates different tabs, such as Customer Management and Work Orders.

Modules:
    - tkinter: For GUI components.
    - tabs.customer_tab: Manages the Customer Management Tab.
    - tabs.workorder_tab: Manages the Work Orders Tab.
    - database: Provides database utility functions like fetching work order metrics.

Classes:
    - None in this file; serves as the main application controller.

Usage:
    Run this file to start the application.

Author: McClure, M.T.
Date: 12-2-24
"""

# ---- ensure project root is importable ----
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
# -------------------------------------------

import tkinter as tk
from tkinter import ttk, messagebox
from tabs.customer_tab import CustomerTab
from tabs.workorder_tab import WorkOrderTab
from tabs.employee_tab import EmployeeTab
# from tabs.employee_tab import EmployeeTab  # (we'll create this next)
from database import get_work_order_metrics
from utils.scanning import parse_scan_payload
from database import (
    fetch_all, fetch_one,
    find_customer_by_barcode, find_customer_by_contact, find_customer_by_name,
    find_work_order_by_code_or_number
)

class MainGUI:
    """Main GUI interface call"""
    def __init__(self, window, user_role="root", username="Admin"):
        self.root = window
        self.user_role = user_role
        self.username = username

        self.root.title(f"Repair Shop Management - Logged in as {self.username} ({self.user_role})")
        self.root.geometry("1200x800")

        # Dashboard
        self.dashboard_frame = tk.Frame(self.root)
        self.dashboard_frame.pack(side="top", fill="x")
        self.load_dashboard()

        # ----- Global Scan box (right side of the dashboard) -----
        scan_frame = tk.Frame(self.dashboard_frame)
        scan_frame.pack(side="right", padx=8, pady=8)

        tk.Label(scan_frame, text="Scan:").pack(side="left")
        self.global_scan_entry = tk.Entry(scan_frame, width=28)
        self.global_scan_entry.pack(side="left")
        self.global_scan_entry.bind("<Return>", self.handle_global_scan)

        # QoL: focus scan box after startup + F9 hotkey to focus anytime
        self.root.after(200, lambda: self.global_scan_entry.focus_set())
        self.root.bind("<F9>", lambda e: self.global_scan_entry.focus_set())
        # ---------------------------------------------------------

        # Notebook for Tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)
        self.init_tabs()

    def load_dashboard(self):
        """Load dashboard metrics."""
        metrics = get_work_order_metrics()

        tk.Label(self.dashboard_frame,
                 text=f"Total Work Orders: {metrics['total']}").pack()
        tk.Label(self.dashboard_frame,
                 text=f"Active Work Orders: {metrics['active']}").pack()
        tk.Label(self.dashboard_frame,
                 text=f"New in Last 24 Hours: {metrics['new_last_24_hours']}").pack()

    def init_tabs(self):
        """Initialize GUI tabs based on user role."""
        # Customers
        customer_tab_frame = tk.Frame(self.notebook)
        self.notebook.add(customer_tab_frame, text="Customers")
        self.customer_tab = CustomerTab(customer_tab_frame, user_role=self.user_role)

        # Work Orders
        workorder_tab_frame = tk.Frame(self.notebook)
        self.notebook.add(workorder_tab_frame, text="Work Orders")
        self.workorder_tab = WorkOrderTab(workorder_tab_frame, user_role=self.user_role)

        # Employees (Only for superuser)
        if self.user_role == "superuser":
            employee_tab_frame = tk.Frame(self.notebook)
            self.notebook.add(employee_tab_frame, text="Employees")
            self.employee_tab = EmployeeTab(employee_tab_frame)

    def handle_global_scan(self, _evt=None):
        raw = self.global_scan_entry.get().strip()
        if not raw:
            return
        data = parse_scan_payload(raw)

        # 1) Work order direct?
        if data["kind"] == "work_order":
            code = data["wo"] or raw
            row = find_work_order_by_code_or_number(code)
            if row:
                wid, cid = row
                self.show_work_order_by_id(wid)
                if cid:
                    self.show_customer_by_id(cid)
                return

        # 2) Customer direct? (CUST- barcode)
        if data["kind"] == "customer":
            r = find_customer_by_barcode(raw)
            if r:
                cid = r[0]
                self.show_customer_by_id(cid)
                return

        # 3) Full payload (multi-field)
        if data["kind"] == "payload":
            cid = None
            if data["cp"] or data["ce"]:
                r = find_customer_by_contact(data["cp"], data["ce"])
                if r: cid = r[0]
            if not cid and data["cf"] and data["cl"]:
                r = find_customer_by_name(data["cf"], data["cl"])
                if r: cid = r[0]

            wid = None
            if data["wo"]:
                r = find_work_order_by_code_or_number(data["wo"])
                if r: wid = r[0]

            if wid:
                self.show_work_order_by_id(wid)
                if cid:
                    self.show_customer_by_id(cid)
                return

            if cid:
                self.show_customer_by_id(cid)
                if hasattr(self.workorder_tab, "prefill_from_payload"):
                    self.workorder_tab.prefill_from_payload(data)
                return

            if messagebox.askyesno("Create", "No match found. Create new customer/work order from scan?"):
                self.notebook.select(0)
                if hasattr(self.customer_tab, "prefill_from_payload"):
                    self.customer_tab.prefill_from_payload(data)
                self.notebook.select(1)
                if hasattr(self.workorder_tab, "prefill_from_payload"):
                    self.workorder_tab.prefill_from_payload(data)
            return

        # 4) Last-chance fallback
        r = find_work_order_by_code_or_number(raw)
        if r:
            wid, cid = r
            self.show_work_order_by_id(wid)
            if cid: self.show_customer_by_id(cid)
            return

        r = find_customer_by_barcode(raw)
        if r:
            self.show_customer_by_id(r[0])
            return

        messagebox.showinfo("Scan", f"No match for: {raw}")

    def show_customer_by_id(self, customer_id: int):
        self.notebook.select(0)
        if hasattr(self.customer_tab, "load_customer"):
            self.customer_tab.load_customer(customer_id)
        else:
            messagebox.showinfo("Customer", f"Loaded Customer ID: {customer_id}")

        # Optional: show that customer's work orders list on the Work Orders tab
        try:
            rows = fetch_all(
                "SELECT id FROM work_orders WHERE customer_id=%s ORDER BY created_at DESC",
                (customer_id,)
            )
            if rows and hasattr(self.workorder_tab, "show_work_order_list_for_customer"):
                self.workorder_tab.show_work_order_list_for_customer(customer_id)
        except Exception:
            pass


    def show_work_order_by_id(self, work_order_id: int):
        """Switch to Work Orders tab and load the WO (if the tab exposes a loader)."""
        # Tab index 1 is "Work Orders"
        self.notebook.select(1)
        if hasattr(self.workorder_tab, "load_work_order"):
            self.workorder_tab.load_work_order(work_order_id)
        else:
            messagebox.showinfo("Work Order", f"Loaded Work Order ID: {work_order_id}")

    # --- Add near top of file with other imports ---
        from database import fetch_all, fetch_one

    # --- Add inside class WorkOrderTab ---
    def show_work_order_list_for_customer(self, customer_id: int):
        """
        Populate the Search tab with this customer's work orders and switch to it.
        """
        try:
            rows = fetch_all(
                """
                SELECT id, customer_id, status, technician
                FROM work_orders
                WHERE customer_id = %s
                ORDER BY created_at DESC
                """,
                (customer_id,)
            )
            # Clear & refill the search Treeview
            self.search_results.delete(*self.search_results.get_children())
            for r in rows:
                self.search_results.insert("", "end", values=r)
            self.notebook.select(self.search_tab)
        except Exception as e:
            messagebox.showerror("Work Orders", f"Failed to load list for customer {customer_id}: {e}")

    def load_work_order(self, work_order_id: int):
        """
        Load a single work order into the Details tab. Fills the widgets that exist.
        """
        try:
            row = fetch_one(
                """
                SELECT id, technician, status, priority, notes
                FROM work_orders
                WHERE id = %s
                """,
                (work_order_id,)
            )
            if not row:
                messagebox.showerror("Work Order", f"Work order {work_order_id} not found.")
                return

            wid, tech, status, priority, notes = row

            # Work order number (readonly Entry)
            self.work_order_number.config(state="normal")
            self.work_order_number.delete(0, "end")
            self.work_order_number.insert(0, str(wid))
            self.work_order_number.config(state="readonly")

            # Assigned technician (Entry)
            self.assigned_technician.delete(0, "end")
            self.assigned_technician.insert(0, tech or "")

            # Priority (Combobox)
            try:
                self.priority.set(priority or "")
            except Exception:
                pass

            # If you have a notes Text widget, uncomment:
            # self.notes_text.delete("1.0", "end")
            # self.notes_text.insert("1.0", notes or "")

            # Flip to Details tab
            self.notebook.select(self.details_tab)
        except Exception as e:
            messagebox.showerror("Work Order", f"Failed to load work order {work_order_id}: {e}")

    def prefill_from_payload(self, p: dict):
        """
        Pre-fill fields from a parsed scan payload (device type/manufacturer, etc.).
        Safe to call even if some widgets/keys aren't present.
        """
        try:
            if p.get("dt"):      # device type
                try:
                    self.work_order_type.set(p["dt"])
                except Exception:
                    pass
            if p.get("dm"):      # manufacturer
                try:
                    self.manufacturer.delete(0, "end")
                    self.manufacturer.insert(0, p["dm"])
                except Exception:
                    pass
            if p.get("wo"):      # show WO code if you want it visible
                try:
                    self.work_order_number.config(state="normal")
                    self.work_order_number.delete(0, "end")
                    self.work_order_number.insert(0, p["wo"])
                    self.work_order_number.config(state="readonly")
                except Exception:
                    pass
        except Exception:
            # keep silent; prefill is best-effort
            pass

if __name__ == "__main__":
    root = tk.Tk()
    app = MainGUI(root)
    root.mainloop()
