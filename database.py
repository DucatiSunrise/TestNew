"""
database.py

This module provides database utilities and helpers for the application.
It handles database connections, query execution, and data fetching.

Modules:
    - mariadb and mysql.connector: Database connectivity.
    - dotenv: Environment variable management.

Functions:
    - fetch_all(query, params): Fetch all records for a query.
    - batch_insert(query, data): Insert multiple records in one batch.
    - get_db_connection(): Context manager for database connection.

Author: McClure, M.T.
Date: 12-4-2024
"""

import os
import csv
import logging
from contextlib import contextmanager
import mariadb
import mysql.connector

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DB_TYPE = os.getenv("DB_TYPE", "mariadb")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))  # Convert default to string for os.getenv
DB_NAME = os.getenv("DB_NAME", "shop")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "RepairShop")

logging.basicConfig(filename='app.log',level=logging.INFO)

class DatabaseError(Exception):
    """Custom exception for database errors."""

@contextmanager
def get_db_connection():
    """Connection to database"""
    real_connection = None
    try:
        real_connection = mariadb.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
        )
        yield real_connection
    except mariadb.Error as e:
        logging.error("Database connection error: %s", e)
        raise DatabaseError("Failed to connect to the database.") from e
    finally:
        if real_connection:
            real_connection.close()

def execute_query(query, params=(), commit=False):
    """Execute a query on the database."""
    try:
        with get_db_connection() as ex_connection:
            cursor = ex_connection.cursor()
            print("Executing query:", query)  # Debugging
            print("Parameters:", params)  # Debugging
            cursor.execute(query, params)
            if commit:  # Commit for INSERT/UPDATE/DELETE queries
                ex_connection.commit()
                return None  # These queries don't return rows
            return cursor.fetchall()  # Fetch results for SELECT queries
    except mariadb.Error as e:
        logging.error("Query execution failed: %s", e)
        raise DatabaseError(f"Query execution failed: {e}") from e  # Explicit re-raise

# Database queries
def find_customer_by_barcode(barcode):
    return fetch_one("SELECT id FROM customers WHERE barcode=%s", (barcode,))

def find_customer_by_contact(phone_digits=None, email=None):
    # phone stored as digits-only recommended; adjust if you store formatted
    if phone_digits:
        r = fetch_one("SELECT id FROM customers WHERE REPLACE(REPLACE(REPLACE(phone,'-',''),'(',''),')','') REGEXP %s LIMIT 1",
                      (phone_digits,))
        if r: return r
    if email:
        r = fetch_one("SELECT id FROM customers WHERE email=%s LIMIT 1", (email,))
        if r: return r
    return None

def find_customer_by_name(first, last):
    return fetch_one("SELECT id FROM customers WHERE first_name=%s AND last_name=%s LIMIT 1",
                     (first, last))

def find_work_order_by_code_or_number(code_or_no):
    # support either explicit scan_code or an order number text like WO-1042
    r = fetch_one("SELECT id, customer_id FROM work_orders WHERE scan_code=%s LIMIT 1", (code_or_no,))
    if r: return r
    r = fetch_one("SELECT id, customer_id FROM work_orders WHERE id=%s LIMIT 1", (code_or_no,))
    return r

def fetch_one(query, params=()):
    """Fetch one record from the database."""
    try:
        with get_db_connection() as db_connection:
            cursor = db_connection.cursor()
            cursor.execute(query, params)
            return cursor.fetchone()
    except mariadb.Error as e:
        logging.error("Error fetching one record: %s", e)
        raise DatabaseError("Fetch one query failed.") from e

def fetch_all(query, params=()):
    """
    Fetch all records from the database.
    
    Args:
        query (str): The SQL query to execute.
        params (tuple): Parameters for the SQL query.

    Returns:
        list: A list of all records returned by the query.

    Raises:
        DatabaseError: If the query execution fails.
    """
    try:
        with get_db_connection() as fetch_connection:
            cursor = fetch_connection.cursor()
            logging.debug("Executing query: %s with params: %s", query, params)  # Debugging info
            cursor.execute(query, params)
            results = cursor.fetchall()
            logging.debug("Query returned %d records.", len(results))  # Debugging info
            return results
    except mariadb.Error as e:
        logging.error("Database error during fetch_all: %s", e)
        raise DatabaseError("Fetch all query failed.") from e

def batch_insert(query, data):
    """Insert multiple records into the database."""
    try:
        with get_db_connection() as batch_connection:
            cursor = batch_connection.cursor()
            cursor.executemany(query, data)
            batch_connection.commit()
    except mariadb.Error as e:
        logging.error("Error during batch insert: %s", e)
        raise DatabaseError("Batch insert failed.") from e

def insert_file_metadata(work_order_id, file_name, file_path, file_type):
    """
    Inserts metadata into the database for file attachments.
    """
    try:
        with get_db_connection() as db_connection:  # Use descriptive variable
            cursor = db_connection.cursor()
            query = """
                INSERT INTO file_attachments (work_order_id, file_name, file_path, file_type)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(query, (work_order_id, file_name, file_path, file_type))
            db_connection.commit()

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        logging.error("Failed to insert file metadata: %s", err)
    except Exception as e:
        logging.error("Unexpected error: %s", e)
        raise

def get_notifications(twenty_four_hours_ago, excluded_days):
    """Notification email"""
    try:
        # Database connection setup
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )
        cursor = conn.cursor()

        # Fetch notifications from the database
        query = """
            SELECT id, customer, status, technician
            FROM work_orders
            WHERE (
                (status = 'Pending Follow-Up' AND created_at <= %s) OR
                (status = 'Overdue' AND created_at <= %s AND DAYOFWEEK(created_at) NOT IN (%s, %s, %s))
            )
        """
        cursor.execute(query, (twenty_four_hours_ago, twenty_four_hours_ago, *excluded_days))
        notifications = cursor.fetchall()
        return notifications

    except mysql.connector.Error as dberr:
        logging.error("Database connection error: %s", dberr)
        raise
    except ValueError as val_err:
        logging.error("Query execution failed: %s", val_err)
        raise
    except TypeError as type_err:
        logging.error("Error fetching one record: %s", type_err)
        raise
    except AttributeError as attr_err:
        logging.error("Error fetching all records: %s", attr_err)
        raise
    except Exception as e:
        logging.error("Error during batch insert: %s", e)
        raise
    finally:
        if conn.is_connected():
            conn.close()

# User Management
def create_user(username, password, role):
    """
    Create user in database
    """
    query = """
    INSERT INTO users (username, password, role)
    VALUES (%s, %s, %s)
    """
    execute_query(query, (username, password, role), commit=True)

def authenticate_user(username, password):
    """
    Authenticate a user by username and password.
    """
    query = "SELECT password, role FROM users WHERE username = %s"
    result = execute_query(query, (username,))
    if not result:
        return None
    db_password, role = result[0]
    return role if db_password == password else None

def has_permission(user_role, required_roles):
    """
    Check user permissions.
    """
    if user_role not in required_roles:
        logging.warning(
            "Permission denied: User role '%s' lacks access to roles %s", 
            user_role, required_roles
        )
        return False
    return True

def get_all_users():
    query = "SELECT id, username, role FROM users"
    return fetch_all(query)

def update_user_role(user_id, new_role):
    query = "UPDATE users SET role = %s WHERE id = %s"
    execute_query(query, (new_role, user_id), commit=True)

def reset_user_password(user_id, new_password):
    query = "UPDATE users SET password = %s WHERE id = %s"
    execute_query(query, (new_password, user_id), commit=True)

def delete_user(user_id):
    query = "DELETE FROM users WHERE id = %s"
    execute_query(query, (user_id,), commit=True)


# Customer Management
class CustomerManager:
    """
    Class to manage customer-related database operations.
    """

    @staticmethod
    def add_customer(data):
        """
        Add customer to database.
        """
        method_of_contact = (
            "Phone" if data["contact_phone"] else
            "Email" if data["contact_email"] else
            "N/A"
        )
        query = """
        INSERT INTO customers 
        (first_name, last_name, street, city, state, zip_code, customer_type, student_id, method_of_contact, phone, email) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        execute_query(query, (
            data["first_name"], data["last_name"], data["street"], data["city"],
            data["state"], data["zip_code"], data["customer_type"], data["student_id"],
            method_of_contact, data["phone"], data["email"]
        ), commit=True)

    @staticmethod
    def load_customers():
        """
        Load customer from database.
        """
        query = """
        SELECT id, first_name, last_name, street, city, state, zip_code, customer_type, student_id, method_of_contact, phone, email 
        FROM customers
        """
        return fetch_all(query)

    @staticmethod
    def delete_customer(customer_id):
        """
        Delete customer from database.
        """
        work_order_query = "SELECT COUNT(*) FROM work_orders WHERE customer_id = %s AND status != 'Closed'"
        active_work_orders = fetch_one(work_order_query, (customer_id,))
        if active_work_orders and active_work_orders[0] > 0:
            raise ValueError("Cannot delete customer with active work orders.")

        delete_query = "DELETE FROM customers WHERE id = %s"
        execute_query(delete_query, (customer_id,), commit=True)

    @staticmethod
    def update_customer(customer_id, data):
        """
        Update customer in database.
        """
        query = """
        UPDATE customers
        SET 
            first_name = %s, last_name = %s, street = %s, city = %s, state = %s, zip_code = %s, 
            customer_type = %s, student_id = %s, method_of_contact = %s, phone = %s, email = %s
        WHERE id = %s
        """
        execute_query(query, (
            data["first_name"], data["last_name"], data["street"], data["city"],
            data["state"], data["zip_code"], data["customer_type"], data["student_id"],
            data.get("method_of_contact", "Email"), data["phone"], data["email"], customer_id
        ), commit=True)

    @staticmethod
    def get_customer_details(customer_id):
        """
        Retireve customer details.
        """
        query = "SELECT * FROM customers WHERE id = %s"
        return fetch_one(query, (customer_id,))

    @staticmethod
    def get_customer_history(customer_id):
        """
        Retrieve customer shop historical from database.
        """
        query = """
        SELECT wo.id, wo.status, wo.priority, wo.notes, wo.created_at
        FROM work_orders wo
        WHERE wo.customer_id = %s
        ORDER BY wo.created_at DESC
        """
        return fetch_all(query, (customer_id,))

    @staticmethod
    def add_customer_note(customer_id, note):
        """
        Add customer note to database.
        """
        query = """
        INSERT INTO customer_notes (customer_id, note, created_at)
        VALUES (%s, %s, NOW())
        """
        execute_query(query, (customer_id, note), commit=True)

    @staticmethod
    def get_customer_notes(customer_id):
        """
        Retrieve customer notes from database.
        """
        query = "SELECT note, created_at FROM customer_notes WHERE customer_id = %s ORDER BY created_at DESC"
        return fetch_all(query, (customer_id,))

    @staticmethod
    def search_customers(search_term, filter_field=None):
        """
        Search customers and format address if queried.
        """
        filter_field_map = {
            "First Name": "first_name",
            "Last Name": "last_name",
            "Street": "street",
            "City": "city",
            "State": "state",
            "Zip Code": "zip_code",
            "Customer Type": "customer_type",
            "Student/School ID": "student_id",
            "Phone": "phone",
            "Email": "email",
            # Combine all address fields for "Address"
            "Address": ["street", "city", "state", "zip_code"],
        }

        if filter_field == "All" or not filter_field:
            query = """
            SELECT * FROM customers
            WHERE first_name LIKE %s OR last_name LIKE %s OR street LIKE %s OR city LIKE %s
            OR state LIKE %s OR zip_code LIKE %s OR customer_type LIKE %s OR student_id LIKE %s
            OR phone LIKE %s OR email LIKE %s
            """
            term = f"%{search_term}%"
            return fetch_all(query, (term,) * 10)
        else:
            column = filter_field_map.get(filter_field)
            if not column:
                raise ValueError(f"Invalid filter field: {filter_field}")

            if isinstance(column, list):  # Handle combined fields like "Address"
                query = "SELECT * FROM customers WHERE " + " OR ".join(
                    f"{col} LIKE %s" for col in column
                )
                return fetch_all(query, tuple(f"%{search_term}%" for _ in column))
            else:
                query = f"SELECT * FROM customers WHERE {column} LIKE %s"
                return fetch_all(query, (f"%{search_term}%",))

    @staticmethod
    def export_customers_to_csv(file_path):
        """
        Export customer data to a CSV file.
        """
        query = """
        SELECT id, first_name, last_name, street, city, state, zip_code, customer_type, student_id, method_of_contact, phone, email
        FROM customers
        """
        customers = fetch_all(query)
        with open(file_path, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow([
                "ID", "First Name", "Last Name", "Street", "City", "State", "Zip Code", 
                "Customer Type", "Student ID", "Method of Contact", "Phone", "Email"
            ])
            for customer in customers:
                writer.writerow(customer)

    @staticmethod
    def import_customers_from_csv(file_path):
        """
        Import customer data from a CSV file into the database.
        """
        query = """
        INSERT INTO customers 
        (first_name, last_name, street, city, state, zip_code, customer_type, student_id, method_of_contact, phone, email)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        with open(file_path, mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            data = [
                (
                    row["First Name"], row["Last Name"], row["Street"], row["City"],
                    row["State"], row["Zip Code"], row["Customer Type"], row["Student ID"],
                    row["Method of Contact"], row["Phone"], row["Email"]
                )
                for row in reader
            ]
            batch_insert(query, data)

    @staticmethod
    def get_all_customers():
        """
        Fetch all customers from the database.
        """
        query = """
        SELECT id, first_name, last_name, street, city, state, zip_code, customer_type, student_id, method_of_contact, phone, email
        FROM customers
        """
        return fetch_all(query)

# Work Order Management
def search_work_orders(search_term=None, filters=None):
    """
    Search work orders based on term and filters.
    """
    query = """
    SELECT id, customer_id, status, priority, technician, created_at 
    FROM work_orders 
    WHERE 1=1 
    """
    params = []
    if search_term:
        query += " AND (technician LIKE %s OR notes LIKE %s)"
        term = f"%{search_term}%"
        params.extend([term, term])
    if filters:
        if "status" in filters:
            query += " AND status = %s"
            params.append(filters["status"])
        if "priority" in filters:
            query += " AND priority = %s"
            params.append(filters["priority"])
        if "date_range" in filters:
            query += " AND created_at BETWEEN %s AND %s"
            params.extend(filters["date_range"])
    return fetch_all(query, params)


def add_work_order(data):
    """
    Add a new work order to the database.
    """
    query = """
    INSERT INTO work_orders (customer_id, status, priority, technician, notes) 
    VALUES (%s, %s, %s, %s, %s)
    """
    execute_query(query, (
        data["customer_id"], data["status"], data["priority"],
        data["technician"], data["notes"]
    ), commit=True)

def update_work_order(work_order_id, data):
    """
    Update an existing work order.
    """
    query = """
    UPDATE work_orders 
    SET status = %s, priority = %s, technician = %s, notes = %s 
    WHERE id = %s
    """
    execute_query(query, (
        data["status"], data["priority"], data["technician"],
        data["notes"], work_order_id
    ), commit=True)

def delete_work_order(work_order_id):
    """
    Delete a work order from the database.
    """
    query = "DELETE FROM work_orders WHERE id = %s"
    execute_query(query, (work_order_id,), commit=True)

def get_active_work_orders():
    """
    Active work order query.
    """
    query = "SELECT * FROM work_orders WHERE status != 'Closed'"
    return execute_query(query)

def get_new_work_orders_since(timestamp):
    """
    Request new work orders from database.
    """
    query = "SELECT * FROM work_orders WHERE created_at >= %s"
    return execute_query(query, (timestamp,))

# Messaging
def add_message(user_id, role, message):
    """
    Send internal user messages.
    """
    query = """
    INSERT INTO messages (user_id, role, message, created_at)
    VALUES (%s, %s, %s, NOW())
    """
    execute_query(query, (user_id, role, message), commit=True)

def get_messages_for_user(user_id, role):
    """
    Request internal user messages.
    """
    query = """
    SELECT message FROM messages
    WHERE role = %s OR user_id = %s
    ORDER BY created_at DESC
    """
    return execute_query(query, (role, user_id))

# Statistics for cool people
def get_work_order_metrics():
    """
    Get work order statistics.
    """
    query = """
    SELECT 
        COUNT(*) AS total_work_orders,
        SUM(CASE WHEN status = 'Active' THEN 1 ELSE 0 END) AS active_work_orders,
        SUM(CASE WHEN created_at >= NOW() - INTERVAL 1 DAY THEN 1 ELSE 0 END) AS new_in_last_24_hours
    FROM work_orders
    """
    result = fetch_one(query)
    if result:
        return {
            "total": result[0],
            "active": result[1],
            "new_last_24_hours": result[2]
        }
    return {"total": 0, "active": 0, "new_last_24_hours": 0}

def get_customer_metrics():
    """
    Get customer statistics.
    """
    query = """
    SELECT 
        COUNT(*) AS total_customers,
        SUM(CASE WHEN created_at >= NOW() - INTERVAL 1 DAY THEN 1 ELSE 0 END) AS new_in_last_24_hours
    FROM customers
    """
    return fetch_one(query)

def get_table_statistics():
    """
    Retrieve general table statistics for dashboard display.
    """
    query = """
    SELECT 
        (SELECT COUNT(*) FROM customers) AS total_customers,
        (SELECT COUNT(*) FROM work_orders) AS total_work_orders
    """
    return fetch_one(query)

def fetch_user_data_by_role(
                            role, resource,
                            current_user_id=None,
                            current_team_id=None
                            ):
    """
   Get user data metrics by role. 
    """

    if role == "technician":
        # Technicians see limited data
        query = f"SELECT * FROM {resource} WHERE assigned_to = %s"
        return fetch_all(query, (current_user_id,))
    elif role == "manager":
        # Managers see all their team's data
        query = f"SELECT * FROM {resource} WHERE team_id = %s"
        return fetch_all(query, (current_team_id,))
    elif role == "superuser":
        # Superusers see everything
        query = f"SELECT * FROM {resource}"
        return fetch_all(query)
    else:
        raise DatabaseError("Invalid role or resource access.")

# Generic search
def search_table(table_name, search_term, columns):
    """
    Search table generic.
    """
    like_clauses = " OR ".join([f"{col} LIKE %s" for col in columns])
    query = f"SELECT * FROM {table_name} WHERE {like_clauses}"
    params = [f"%{search_term}%"] * len(columns)
    return fetch_all(query, params)

# Pagination
def fetch_with_pagination(table_name, offset=0, limit=10):
    """
    Table pagination for large data queries.
    """
    query = f"SELECT * FROM {table_name} LIMIT %s OFFSET %s"
    return fetch_all(query, (limit, offset))

# Bulk operations
def bulk_insert(table_name, data, columns):
    """
    Bulk insert into database
    """
    placeholders = ", ".join(["%s"] * len(columns))
    columns_str = ", ".join(columns)
    query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
    batch_insert(query, data)

# Audit logging
def get_audit_logs():
    """
    Get audit logs.
    """
    query = """
    SELECT 
        id, user_id, action, table_name, record_id, details, timestamp
    FROM 
        audit_log
    ORDER BY 
        timestamp DESC
    """
    return fetch_all(query)

def log_audit_entry(user_id, action, table_name, record_id, details):
    """
    Get audit entry log.
    """
    query = """
    INSERT INTO audit_log (user_id, action, table_name, record_id, details, timestamp)
    VALUES (%s, %s, %s, %s, %s, NOW())
    """
    execute_query(query, (user_id, action, table_name, record_id, details), commit=True)

def validate_foreign_key(table_name, column_name, value):
    """
    Get validate foreign key.
    """
    query = f"SELECT 1 FROM {table_name} WHERE {column_name} = %s"
    return fetch_one(query, (value,)) is not None

if __name__ == "__main__":
    try:
        with get_db_connection() as connection:
            print("Successfully connected to the database!")
    except DatabaseError as e:
        print(f"Error: {e}")
