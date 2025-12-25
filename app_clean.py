from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response, jsonify
import psycopg2
from datetime import datetime, date, timedelta, timezone
from collections import defaultdict
from io import StringIO
import csv
import calendar
import hashlib
import secrets
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Flask Secret Key
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default-fallback-key')
app.secret_key = app.config['SECRET_KEY']

# PostgreSQL Connection Settings
DB_CONFIG = {
    'dbname': os.environ.get('DB_NAME'),
    'user': os.environ.get('DB_USER'),
    'password': os.environ.get('DB_PASSWORD'),
    'host': os.environ.get('DB_HOST'),
    'port': os.environ.get('DB_PORT', '5432')
}

# 8 HOURS REFERENCE
EIGHT_HOURS_SECONDS = 28800
PER_PAGE_ATTENDANCE = 50

# Helper dictionary for month names
EN_MONTHS = {
    1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June",
    7: "July", 8: "August", 9: "September", 10: "October", 11: "November", 12: "December"
}

def get_current_baku_time():
    """Returns the current time in Baku (UTC+4)."""
    utc_now = datetime.now(timezone.utc)
    baku_now = utc_now + timedelta(hours=4)
    return baku_now.replace(tzinfo=None)

def get_db_connection():
    """Tries to connect to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except psycopg2.Error as e:
        print(f"🚨 Database connection error: {e}")
        return None

def hash_password(password):
    """Hash a password for storing."""
    salt = secrets.token_hex(16)
    password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"sha256${salt}${password_hash}"

def verify_password(stored_password, provided_password):
    """Verify a stored password against one provided by user"""
    try:
        if stored_password.startswith('sha256$'):
            # Hashed password format: sha256$salt$hash
            _, salt, stored_hash = stored_password.split('$')
            provided_hash = hashlib.sha256((provided_password + salt).encode()).hexdigest()
            return provided_hash == stored_hash
        else:
            # Temporary support for plaintext passwords (SECURITY RISK - should be removed)
            return stored_password == provided_password
    except Exception as e:
        print(f"🚨 Password verification error: {e}")
        return False

def get_user_by_email(email):
    """Get user by email from database."""
    conn = get_db_connection()
    if conn is None: 
        return None

    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT id, email, password, full_name, user_role, is_active
            FROM public.system_users 
            WHERE email = %s AND is_active = true
        """, (email,))

        user = cur.fetchone()
        if user:
            return {
                'id': user[0],
                'email': user[1],
                'password': user[2],
                'full_name': user[3],
                'role': user[4],
                'is_active': user[5]
            }
        return None
    except psycopg2.Error as e:
        print(f"🚨 User Query Error: {e}")
        return None
    finally:
        if cur: cur.close()
        if conn: conn.close()

def require_login():
    """Checks if the user is logged in."""
    if 'user' not in session:
        flash("You must log in first.", 'warning')
        return redirect(url_for('login'))
    return None

@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash('Please enter both email and password.', 'danger')
            return render_template('login.html')

        user = get_user_by_email(email)

        # Password validation
        password_valid = False
        if user:
            password_valid = verify_password(user['password'], password)

        if user and password_valid:
            session['user'] = {
                'id': user['id'],
                'email': user['email'],
                'full_name': user['full_name'],
                'role': user['role']
            }

            flash(f'Welcome back, {user["full_name"]}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password!', 'danger')

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if (redirect_response := require_login()): 
        return redirect_response
    
    # Sample dashboard data
    dashboard_data = {
        'total_employees': 150,
        'total_departments': 8,
        'total_transactions': 45,
        'new_employees_this_month': 5,
        'present_employees': 120,
        'attendance_percentage': 80.0,
        'absent_employees': [],
        'late_employees': [],
        'birthdays_today': []
    }
    
    return render_template('dashboard.html', data=dashboard_data)

@app.route('/employees')
def employees():
    if (redirect_response := require_login()): 
        return redirect_response
    
    # Sample employees data
    employees_list = [
        {
            'id': 1,
            'name': 'John',
            'last_name': 'Doe',
            'mobile_phone': '+994501234567',
            'email': 'john.doe@company.com',
            'birthday': '15.03.1990',
            'position': 'Software Engineer',
            'hire_date': '01.01.2020'
        }
    ]
    
    return render_template('employees.html', employees=employees_list)

@app.route('/attendance')
def attendance():
    if (redirect_response := require_login()): 
        return redirect_response
    return render_template('attendance.html')

@app.route('/hours_tracked')
def hours_tracked():
    if (redirect_response := require_login()): 
        return redirect_response
    return render_template('hours_tracked.html')

@app.route('/employee_logs')
def employee_logs():
    if (redirect_response := require_login()): 
        return redirect_response
    return render_template('employee_logs.html')

@app.route('/salary')
def salary():
    if (redirect_response := require_login()): 
        return redirect_response
    
    # Sample salary data
    sample_salaries = [
        {
            'id': 1,
            'name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@company.com',
            'position': 'Software Engineer',
            'base_salary': 5000,
            'overtime_pay': 200,
            'bonuses': 300,
            'deductions': 100,
            'net_salary': 5400,
            'status': 'Paid',
            'status_class': 'success'
        }
    ]
    
    # Calculate summary statistics
    total_employees = len(sample_salaries)
    total_payroll = sum(s['net_salary'] for s in sample_salaries)
    avg_salary = total_payroll / total_employees if total_employees > 0 else 0
    current_month = get_current_baku_time().strftime('%B %Y')
    
    return render_template('salary.html', 
                         salaries=sample_salaries,
                         total_employees=total_employees,
                         total_payroll=total_payroll,
                         avg_salary=avg_salary,
                         current_month=current_month)

@app.route('/admin')
def admin():
    if (redirect_response := require_login()): 
        return redirect_response
    
    # Check admin role
    if session.get('user', {}).get('role') != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    return render_template('admin.html')

@app.route('/admin/users')
def admin_users():
    if (redirect_response := require_login()): 
        return redirect_response
    
    # Check admin role
    if session.get('user', {}).get('role') != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    return render_template('admin_users.html')

@app.route('/admin/employees')
def admin_employees():
    if (redirect_response := require_login()): 
        return redirect_response
    
    # Check admin role
    if session.get('user', {}).get('role') != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    return render_template('admin_employees.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash("Successfully logged out.", 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)