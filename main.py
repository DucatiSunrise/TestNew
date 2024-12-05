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

import tkinter as tk
from tkinter import ttk
from tabs.customer_tab import CustomerTab
from tabs.workorder_tab import WorkOrderTab
from database import get_work_order_metrics

class MainGUI:
    """Main GUI interface call"""
    def __init__(self, window):
        self.root = window
        self.root.title("Repair Shop Management")
        self.root.geometry("1200x800")

        # Dashboard
        self.dashboard_frame = tk.Frame(self.root)
        self.dashboard_frame.pack(side="top", fill="x")
        self.load_dashboard()

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
        """Initialize GUI tabs."""
        # Create tab frames
        customer_tab_frame = tk.Frame(self.notebook)
        workorder_tab_frame = tk.Frame(self.notebook)

        # Add frames to notebook
        self.notebook.add(customer_tab_frame, text="Customers")
        self.notebook.add(workorder_tab_frame, text="Work Orders")

        # Initialize tab logic
        self.customer_tab = CustomerTab(customer_tab_frame, user_role="root")
        self.workorder_tab = WorkOrderTab(workorder_tab_frame)
        # self.workorder_tab = WorkOrderTab(workorder_tab_frame, user_role="root")


if __name__ == "__main__":
    root = tk.Tk()
    app = MainGUI(root)
    root.mainloop()
