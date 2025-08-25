"""
main.py

Entry point for the application. Initializes the main GUI and integrates tabs
such as Customer Management and Work Orders.

Modules:
    - tkinter: For GUI components.
    - tabs.customer_tab: Customer Management tab.
    - tabs.workorder_tab: Work Orders tab.
    - database: DB utilities (work order metrics, lookups).
    - utils.scanning: Barcode / scan payload parsing.

Author: McClure, M.T.
Date: 2024-12-02
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
# NOTE: EmployeeTab import is deferred in init_tabs() for safety.

from database import get_work_order_metrics
from utils.scanning import parse_scan_payload
from database import (
    fetch_all,
    find_customer_by_barcode, find_customer_by_contact, find_customer_by_name,
    find_work_order_by_code_or_number,
)


class MainGUI:
    """Main GUI interface controller."""
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
        try:
            metrics = get_work_order_metrics()
        except Exception as e:
            messagebox.showerror("Dashboard", f"Failed to fetch metrics: {e}")
            return

        # If you later refresh, consider clearing children or reusing StringVars.
        tk.Label(self.dashboard_frame, text=f"Total Work Orders: {metrics.get('total', 0)}").pack()
        tk.Label(self.dashboard_frame, text=f"Active Work Orders: {metrics.get('active', 0)}").pack()
        tk.Label(
            self.dashboard_frame,
            text=f"New in Last 24 Hours: {metrics.get('new_last_24_hours', 0)}"
        ).pack()

    def init_tabs(self):
        """Initialize GUI tabs based on user role."""
        # Customers
        self.customer_tab_frame = tk.Frame(self.notebook)
        self.notebook.add(self.customer_tab_frame, text="Customers")
        self.customer_tab = CustomerTab(self.customer_tab_frame, user_role=self.user_role)

        # Work Orders
        self.workorder_tab_frame = tk.Frame(self.notebook)
        self.notebook.add(self.workorder_tab_frame, text="Work Orders")
        self.workorder_tab = WorkOrderTab(self.workorder_tab_frame, user_role=self.user_role)

        # Employees (Only for superuser) — defer import for safety
        if self.user_role == "superuser":
            try:
                from tabs.employee_tab import EmployeeTab  # deferred import
            except Exception:
                messagebox.showwarning(
                    "Employees", "Employee tab not available (module missing)."
                )
            else:
                self.employee_tab_frame = tk.Frame(self.notebook)
                self.notebook.add(self.employee_tab_frame, text="Employees")
                self.employee_tab = EmployeeTab(self.employee_tab_frame)

    def handle_global_scan(self, _evt=None):
        raw = self.global_scan_entry.get().strip()
        if not raw:
            return

        # Clear input for better UX
        self.global_scan_entry.delete(0, "end")

        try:
            data = parse_scan_payload(raw)
        except Exception as e:
            messagebox.showerror("Scan", f"Failed to parse scan: {e}")
            return

        # 1) Work order direct?
        if data.get("kind") == "work_order":
            code = data.get("wo") or raw
            row = find_work_order_by_code_or_number(code)
            if row:
                wid, cid = row
                self.show_work_order_by_id(wid)
                if cid:
                    self.show_customer_by_id(cid)
                return

        # 2) Customer direct? (CUST- barcode)
        if data.get("kind") == "customer":
            r = find_customer_by_barcode(raw)
            if r:
                cid = r[0]
                self.show_customer_by_id(cid)
                return

        # 3) Full payload (multi-field)
        if data.get("kind") == "payload":
            cid = None
            cp, ce = data.get("cp"), data.get("ce")
            if cp or ce:
                r = find_customer_by_contact(cp, ce)
                if r:
                    cid = r[0]
            if not cid and data.get("cf") and data.get("cl"):
                r = find_customer_by_name(data["cf"], data["cl"])
                if r:
                    cid = r[0]

            wid = None
            if data.get("wo"):
                r = find_work_order_by_code_or_number(data["wo"])
                if r:
                    wid = r[0]

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
                self.notebook.select(self.customer_tab_frame)
                if hasattr(self.customer_tab, "prefill_from_payload"):
                    self.customer_tab.prefill_from_payload(data)
                self.notebook.select(self.workorder_tab_frame)
                if hasattr(self.workorder_tab, "prefill_from_payload"):
                    self.workorder_tab.prefill_from_payload(data)
            return

        # 4) Last-chance fallback
        r = find_work_order_by_code_or_number(raw)
        if r:
            wid, cid = r
            self.show_work_order_by_id(wid)
            if cid:
                self.show_customer_by_id(cid)
            return

        r = find_customer_by_barcode(raw)
        if r:
            self.show_customer_by_id(r[0])
            return

        messagebox.showinfo("Scan", f"No match for: {raw}")

    def show_customer_by_id(self, customer_id: int):
        self.notebook.select(self.customer_tab_frame)
        if hasattr(self.customer_tab, "load_customer"):
            self.customer_tab.load_customer(customer_id)
        else:
            messagebox.showinfo("Customer", f"Loaded Customer ID: {customer_id}")

        # Optional: show that customer's work orders list on the Work Orders tab
        try:
            rows = fetch_all(
                "SELECT id FROM work_orders WHERE customer_id=%s ORDER BY created_at DESC",
                (customer_id,),
            )
            if rows and hasattr(self.workorder_tab, "show_work_order_list_for_customer"):
                self.workorder_tab.show_work_order_list_for_customer(customer_id)
        except Exception:
            pass

    def show_work_order_by_id(self, work_order_id: int):
        """Switch to Work Orders tab and load the WO (if the tab exposes a loader)."""
        self.notebook.select(self.workorder_tab_frame)
        if hasattr(self.workorder_tab, "load_work_order"):
            self.workorder_tab.load_work_order(work_order_id)
        else:
            messagebox.showinfo("Work Order", f"Loaded Work Order ID: {work_order_id}")


if __name__ == "__main__":
    root = tk.Tk()
    app = MainGUI(root)
    root.mainloop()
