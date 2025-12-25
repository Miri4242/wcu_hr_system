from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response, jsonify
import psycopg2
from datetime import datetime, date, timedelta, timezone  # timezone eklendi
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


# --------------------------------------------------------------------------------------
# --- TIMEZONE HELPER (BAKU FIX) ---
# --------------------------------------------------------------------------------------

def get_current_baku_time():
    """
    Returns the current time in Baku (UTC+4).
    Removes timezone info at the end to match 'naive' database timestamps.
    """
    # UTC zamanını al
    utc_now = datetime.now(timezone.utc)
    # Bakü için 4 saat ekle (Azerbaycan'da DST/Yaz saati uygulaması yoktur, sabittir)
    baku_now = utc_now + timedelta(hours=4)
    # Veritabanı ile karşılaştırma yapabilmek için tzinfo'yu temizle (naive yap)
    return baku_now.replace(tzinfo=None)


def get_db_connection():
    """Tries to connect to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except psycopg2.Error as e:
        print(f"🚨 Database connection error: {e}")
        return None


# --------------------------------------------------------------------------------------
# --- AUTHENTICATION FUNCTIONS ---
# --------------------------------------------------------------------------------------

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
    except:
        return False$')
        provided_hash = hashlib.sha256((provided_password + salt).encode()).hexdigest()
        return provided_hash == stored_hash
    except:
        return False


def get_user_by_email(email):
    """Get user by email from database."""
    conn = get_db_connection()
    if conn is None: return None

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


def update_last_login(user_id):
    """Update user's last login timestamp."""
    conn = get_db_connection()
    if conn is None: return False

    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE public.system_users 
            SET last_login = CURRENT_TIMESTAMP 
            WHERE id = %s
        """, (user_id,))
        conn.commit()
        return True
    except psycopg2.Error as e:
        print(f"🚨 Update Last Login Error: {e}")
        return False
    finally:
        if cur: cur.close()
        if conn: conn.close()


# --------------------------------------------------------------------------------------
# --- CORE HELPER FUNCTIONS ---
# --------------------------------------------------------------------------------------

def format_seconds(seconds):
    """Converts seconds to HH:MM:SS format."""
    if seconds <= 0: return "00:00:00"
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours:02}:{minutes:02}:{secs:02}"


def normalize_name(name):
    """Converts name/surname to lowercase and strips whitespace, removing inner spaces."""
    if name is None:
        return ""
    return name.lower().strip().replace(' ', '')


def require_login():
    """
    Checks if the user is logged in.
    Returns a redirect response if not logged in, otherwise None.
    """
    if 'user' not in session:
        flash("You must log in first.", 'warning')
        return redirect(url_for('login'))
    return None


def get_available_months(num_months=12):
    """Prepares a list of the last X available months (value: YYYY-MM, label: Month YYYY)."""
    months = []
    # BAKU TIME FIX: datetime.now().date() -> get_current_baku_time().date()
    today = get_current_baku_time().date()
    current_month_start = today.replace(day=1)

    for i in range(num_months):
        if i > 0:
            target_date = (current_month_start - timedelta(days=1)).replace(day=1)
            current_month_start = target_date
        else:
            target_date = current_month_start

        value = target_date.strftime('%Y-%m')
        label = f"{EN_MONTHS[target_date.month]} {target_date.year}"

        months.append((value, label))

    return months[::-1]


# --------------------------------------------------------------------------------------
# --- EMPLOYEE MANAGEMENT FUNCTIONS (CRUD/LIST) ---
# --------------------------------------------------------------------------------------

def get_admin_employees_paginated(page=1, per_page=20, search_term=""):
    """Fetches employees with pagination and search for admin panel."""
    conn = get_db_connection()
    if conn is None: 
        return {
            'employees': [], 
            'pagination': {
                'current_page': 1, 
                'total_pages': 1, 
                'total_items': 0
            }
        }

    cur = conn.cursor()
    try:
        # Base query
        base_query = """
            FROM public.pers_person p
            LEFT JOIN public.pers_position pp ON p.position_id = pp.id
            WHERE (pp.name IS NULL
               OR (pp.name NOT ILIKE 'STUDENT' 
                   AND pp.name NOT ILIKE 'VISITOR'
                   AND pp.name NOT ILIKE 'MÜƏLLİM'))
        """
        
        # Search filter
        search_filter = ""
        search_params = []
        if search_term:
            search_filter = """
                AND (LOWER(p.name) LIKE %s 
                     OR LOWER(p.last_name) LIKE %s 
                     OR LOWER(p.email) LIKE %s 
                     OR LOWER(pp.name) LIKE %s
                     OR LOWER(p.name || ' ' || p.last_name) LIKE %s)
            """
            search_pattern = f'%{search_term.lower()}%'
            search_params = [search_pattern] * 5
        
        # Count total items
        count_query = f"SELECT COUNT(*) {base_query} {search_filter}"
        cur.execute(count_query, search_params)
        total_items = cur.fetchone()[0]
        
        # Calculate pagination
        total_pages = (total_items + per_page - 1) // per_page
        if page < 1: page = 1
        if page > total_pages and total_pages > 0: page = total_pages
        
        offset = (page - 1) * per_page
        
        # Fetch employees
        employees_query = f"""
            SELECT p.id,
                   p.name,
                   p.last_name,
                   p.mobile_phone,
                   p.email,
                   p.birthday,
                   p.photo_path,
                   pp.name AS position_name,
                   p.create_time AS hire_date
            {base_query} {search_filter}
            ORDER BY p.last_name, p.name
            LIMIT %s OFFSET %s
        """
        
        params = search_params + [per_page, offset]
        cur.execute(employees_query, params)
        
        employees_raw = cur.fetchall()
        employees = []

        for row in employees_raw:
            try:
                photo_path = row[6] if row[6] else url_for('static', filename='images/default_avatar.png')
            except RuntimeError:
                photo_path = row[6] if row[6] else '/static/images/default_avatar.png'

            employees.append({
                'id': row[0],
                'name': row[1],
                'last_name': row[2],
                'mobile_phone': row[3] or 'N/A',
                'email': row[4] or 'N/A',
                'birthday': row[5].strftime('%d.%m.%Y') if row[5] else 'N/A',
                'photo_path': photo_path,
                'position': row[7] or 'Undefined',
                'hire_date': row[8].strftime('%d.%m.%Y') if row[8] else 'N/A'
            })
        
        return {
            'employees': employees,
            'pagination': {
                'current_page': page,
                'total_pages': total_pages,
                'total_items': total_items
            }
        }
        
    except psycopg2.Error as e:
        print(f"🚨 Admin Employees Paginated Fetch Error: {e}")
        return {
            'employees': [], 
            'pagination': {
                'current_page': 1, 
                'total_pages': 1, 
                'total_items': 0
            }
        }
    finally:
        if cur: cur.close()
        if conn: conn.close()


def get_employee_list():
    """Fetches essential details and positions for all employees (excluding Students, Visitors and Teachers)."""
    conn = get_db_connection()
    if conn is None: return []

    cur = conn.cursor()
    try:
        cur.execute("""
                    SELECT p.id,
                           p.name,
                           p.last_name,
                           p.mobile_phone,
                           p.email,
                           p.birthday,
                           pp.name       AS position_name,
                           p.create_time AS hire_date
                    FROM public.pers_person p
                             LEFT JOIN public.pers_position pp ON p.position_id = pp.id
                    WHERE (pp.name IS NULL
                       OR (pp.name NOT ILIKE 'STUDENT' 
                           AND pp.name NOT ILIKE 'VISITOR'
                           AND pp.name NOT ILIKE 'MÜƏLLİM')) -- Student, Visitor ve Müəllim Filtresi
                    ORDER BY p.last_name, p.name;
                    """)

        employees_raw = cur.fetchall()
        employees = []

        for row in employees_raw:
            employees.append({
                'id': row[0],
                'name': row[1],
                'last_name': row[2],
                'mobile_phone': row[3] or 'N/A',
                'email': row[4] or 'N/A',
                'birthday': row[5].strftime('%d.%m.%Y') if row[5] else 'N/A',
                'position': row[6] or 'Undefined',
                'hire_date': row[7].strftime('%d.%m.%Y') if row[7] else 'N/A'
            })
        return employees
    except psycopg2.Error as e:
        print(f"🚨 Employee List Fetch Error: {e}")
        return []
    finally:
        if cur: cur.close()
        if conn: conn.close()


def get_employee_details(employee_id):
    """Fetches all details for a specific employee ID (excluding Students, Visitors and Teachers)."""
    conn = get_db_connection()
    if conn is None: return None

    cur = conn.cursor()
    try:
        cur.execute("""
                    SELECT p.id,
                           p.name,
                           p.last_name,
                           p.mobile_phone,
                           p.email,
                           p.birthday,
                           pp.name       AS position_name,
                           p.position_id,
                           p.create_time AS hire_date
                    FROM public.pers_person p
                             LEFT JOIN public.pers_position pp ON p.position_id = pp.id
                    WHERE (pp.name IS NULL 
                           OR (pp.name NOT ILIKE 'student' 
                               AND pp.name NOT ILIKE 'visitor'
                               AND pp.name NOT ILIKE 'müəllim')) -- Student, Visitor ve Müəllim Filtresi
                      AND p.id = %s;
                    """, (employee_id,))

        row = cur.fetchone()
        print(f"🔍 Query result: {row}")

        if row:
            return {
                'id': row[0],
                'name': row[1],
                'last_name': row[2],
                'mobile_phone': row[3] or '',
                'email': row[4] or '',
                'birthday_form': row[5].strftime('%Y-%m-%d') if row[5] else '',
                'birthday_display': row[5].strftime('%d.%m.%Y') if row[5] else 'N/A',
                'position_name': row[6] or 'Undefined',
                'position_id': row[7],
                'hire_date': row[8].strftime('%d.%m.%Y') if row[8] else 'N/A'
            }
        return None
    except psycopg2.Error as e:
        print(f"🚨 Employee Details Fetch Error: {e}")
        return None
    finally:
        if cur: cur.close()
        if conn: conn.close()


def get_all_positions():
    """Fetches all positions by ID and Name (for Dropdown)."""
    conn = get_db_connection()
    if conn is None: return []
    cur = conn.cursor()
    try:
        cur.execute("SELECT id, name FROM public.pers_position ORDER BY name;")
        return [{'id': row[0], 'name': row[1]} for row in cur.fetchall()]
    except psycopg2.Error as e:
        print(f"🚨 Position List Fetch Error: {e}")
        return []
    finally:
        if cur: cur.close()
        if conn: conn.close()


def update_employee_details(employee_id, data):
    """Updates employee information."""
    conn = get_db_connection()
    if conn is None:
        return False, "Database connection error."

    cur = conn.cursor()

    birthday_str = data.get('birthday')
    birthday_value = birthday_str if birthday_str else None

    try:
        cur.execute("""
                    UPDATE public.pers_person
                    SET name         = %s,
                        last_name    = %s,
                        mobile_phone = %s,
                        email        = %s,
                        birthday     = %s,
                        position_id  = %s
                    WHERE id = %s;
                    """, (
            data.get('name'),
            data.get('last_name'),
            data.get('mobile_phone'),
            data.get('email'),
            birthday_value,
            data.get('position_id'),
            employee_id
        ))
        conn.commit()
        return True, "Employee details successfully updated."
    except psycopg2.Error as e:
        conn.rollback()
        print(f"🚨 Employee Update Error: {e}")
        return False, f"Update error: {e}"
    finally:
        if cur: cur.close()
        if conn: conn.close()


# --------------------------------------------------------------------------------------
# --- TIME CALCULATION CORE LOGIC ---
# --------------------------------------------------------------------------------------

def calculate_times_from_transactions(transactions):
    """
    Processes the given log list and calculates the time spent inside/outside.
    If the last event is 'in' and it's not today, mark as invalid day.
    """
    transactions.sort(key=lambda x: x['time'])

    # BAKU TIME FIX: datetime.now().date() -> get_current_baku_time().date()
    today = get_current_baku_time().date()

    transaction_dates = set(t['time'].date() for t in transactions)
    is_today = today in transaction_dates

    first_in_time = None
    last_out_time = None

    # BAKU TIME FIX: datetime.now() -> get_current_baku_time()
    current_time = get_current_baku_time()

    # Find the first 'in' and last 'out'
    in_logs = [t['time'] for t in transactions if t['direction'] == 'in']
    out_logs = [t['time'] for t in transactions if t['direction'] == 'out']

    if in_logs:
        first_in_time = min(in_logs)
    if out_logs:
        last_out_time = max(out_logs)

    # Check if person is currently inside (last event is 'in')
    is_currently_inside = False
    if transactions:
        last_transaction = max(transactions, key=lambda x: x['time'])
        is_currently_inside = (last_transaction['direction'] == 'in')

    # Check if this is an invalid day (last event IN but not today)
    is_invalid_day = is_currently_inside and not is_today

    total_inside_seconds = 0
    total_span_seconds = 0

    if not is_invalid_day:
        # Calculate total span time only for valid days
        if first_in_time:
            if is_currently_inside and last_out_time:
                # Person came in, went out, and came back in (currently inside)
                total_span_seconds = (current_time - first_in_time).total_seconds()
            elif is_currently_inside and not last_out_time:
                # Person came in and never went out (currently inside)
                total_span_seconds = (current_time - first_in_time).total_seconds()
            elif last_out_time and last_out_time > first_in_time:
                # Person came in and went out (not currently inside)
                total_span_seconds = (last_out_time - first_in_time).total_seconds()

        is_inside = False
        last_event_time = None

        # Detailed calculation of inside time (only for valid days)
        for i, t in enumerate(transactions):
            current_time_point = t['time']
            current_direction = t['direction']

            if first_in_time and current_time_point < first_in_time:
                continue

            if last_event_time is None:
                if current_direction == 'in':
                    is_inside = True
                last_event_time = current_time_point
                continue

            time_diff_seconds = (current_time_point - last_event_time).total_seconds()

            if time_diff_seconds < 0:
                last_event_time = current_time_point
                continue

            if is_inside:
                total_inside_seconds += time_diff_seconds
                if current_direction == 'out':
                    is_inside = False
            else:
                if current_direction == 'in':
                    is_inside = True

            last_event_time = current_time_point

        # If currently inside, add time from last event to current time
        if is_inside and last_event_time:
            current_diff_seconds = (current_time - last_event_time).total_seconds()
            if current_diff_seconds > 0:
                total_inside_seconds += current_diff_seconds

    # Time spent outside = Total span time - Inside time
    total_outside_seconds = 0
    if total_span_seconds > 0 and not is_invalid_day:
        total_outside_seconds = total_span_seconds - total_inside_seconds
        if total_outside_seconds < 0:
            total_outside_seconds = 0

    return {
        'first_in': first_in_time,
        'last_out': last_out_time,
        'total_inside_seconds': total_inside_seconds if not is_invalid_day else 0,
        'total_outside_seconds': total_outside_seconds if not is_invalid_day else 0,
        'total_span_seconds': total_span_seconds if not is_invalid_day else 0,
        'is_currently_inside': is_currently_inside,
        'current_time_used': current_time if is_currently_inside else None,
        'is_invalid_day': is_invalid_day,
        'is_today': is_today
    }


# --------------------------------------------------------------------------------------
# --- HOURS TRACKED AND ATTENDANCE FUNCTIONS ---
# --------------------------------------------------------------------------------------

def get_employee_list_for_dropdown():
    """Returns employee full name and a normalized key for dropdowns (excluding Students, Visitors and Teachers)."""
    conn = get_db_connection()
    if conn is None: return []

    cur = conn.cursor()
    try:
        cur.execute("""
                    SELECT p.name, p.last_name
                    FROM public.pers_person p
                             LEFT JOIN public.pers_position pp ON p.position_id = pp.id
                    WHERE pp.name IS NULL
                       OR (pp.name NOT ILIKE 'STUDENT' 
                           AND pp.name NOT ILIKE 'VISITOR'
                           AND pp.name NOT ILIKE 'MÜƏLLİM') -- Student, Visitor ve Müəllim Filtresi
                    ORDER BY p.last_name, p.name
                    """)
        employees = []
        for name, last_name in cur.fetchall():
            full_name = f"{name} {last_name}"
            key = normalize_name(name) + normalize_name(last_name)
            employees.append({'key': key, 'name': full_name})

        return employees
    except psycopg2.Error as e:
        print(f"🚨 Employee List Query Error: {e}")
        return []
    finally:
        if cur: cur.close()
        if conn: conn.close()


def get_employee_logs(person_key=None, start_date=None, end_date=None):
    """
    Calculates the daily summary of time spent inside/outside for the given date range
    (all employees if person_key is None).
    """
    conn = get_db_connection()
    if conn is None: return []

    cur = conn.cursor()

    # BAKU TIME FIX: datetime.now() -> get_current_baku_time()
    current_baku = get_current_baku_time()

    # Date range handling
    if not start_date:
        start_date = current_baku - timedelta(days=365)
    else:
        start_date = datetime.combine(start_date, datetime.min.time())

    if not end_date:
        end_date = current_baku
    else:
        end_date = datetime.combine(end_date, datetime.max.time())

    daily_transactions = defaultdict(list)
    final_logs = []

    try:
        # 1. Fetch transaction logs (Filtered by date range)
        cur.execute("""
                    SELECT t.name, t.last_name, t.create_time, t.reader_name
                    FROM public.acc_transaction t
                             INNER JOIN public.pers_person p ON t.name = p.name AND t.last_name = p.last_name
                             LEFT JOIN public.pers_position pp ON p.position_id = pp.id
                    WHERE t.create_time BETWEEN %s AND %s
                      AND (pp.name IS NULL 
                           OR (pp.name NOT ILIKE 'student' 
                               AND pp.name NOT ILIKE 'visitor'
                               AND pp.name NOT ILIKE 'müəllim')) -- Student, Visitor ve Müəllim Filtresi
                    ORDER BY t.create_time;
                    """, (start_date, end_date))
        raw_transactions = cur.fetchall()

        # 2. Process transactions and Grouping (Person Name + Date)
        for t_name, t_last_name, create_time, reader_name in raw_transactions:
            if create_time is None or not t_name or not t_last_name:
                continue

            # Create and filter key
            t_key = normalize_name(t_name) + normalize_name(t_last_name)
            if person_key and t_key != person_key:
                continue

            log_date = create_time.date()

            # SADECE RAKAM KONTROLÜ - Building A-1 pattern'ine göre
            direction_type = None
            if reader_name:
                import re
                numbers = re.findall(r'\d+', reader_name)
                if numbers:
                    reader_number = int(numbers[0])
                    if reader_number in [1, 2]:
                        direction_type = 'in'
                    elif reader_number in [3, 4]:
                        direction_type = 'out'

            if not direction_type:
                # Eğer rakam bulunamadıysa veya 1-4 arasında değilse, bu kaydı yok say
                continue

            key = (log_date, t_key)
            daily_transactions[key].append({
                'name': t_name,
                'last_name': t_last_name,
                'time': create_time,
                'direction': direction_type
            })

        # 3. Calculate Time for each day/person
        employee_first_date = None
        employee_name = ""
        employee_last_name = ""

        for (log_date, person_key), transactions in daily_transactions.items():
            # Use the core calculation function
            times = calculate_times_from_transactions(transactions)

            # Track first date for this employee
            if employee_first_date is None or log_date < employee_first_date:
                employee_first_date = log_date
                employee_name = transactions[0]['name']
                employee_last_name = transactions[0]['last_name']

            # Status calculation
            status_display = ""
            status_color = ""
            status_class = ""

            if times['is_invalid_day']:
                status_display = "⚠ Invalid Data"
                status_color = "#dc3545"
                status_class = "invalid"
            else:
                total_inside_seconds = times['total_inside_seconds'] or 0

                if total_inside_seconds >= EIGHT_HOURS_SECONDS:
                    status_display = "✓ Full Day"
                    status_color = "#28a745"
                    status_class = "full-day"
                elif total_inside_seconds > 0:
                    status_display = "⚠ Short Hours"
                    status_color = "#ffc107"
                    status_class = "short-hours"
                else:
                    status_display = "✗ Absent"
                    status_color = "#dc3545"
                    status_class = "absent"

            # Prepare display values based on validity
            if times['is_invalid_day']:
                first_in_display = "N/A"
                last_out_display = "N/A"
                inside_time_display = "N/A"
                outside_time_display = "N/A"
                total_span_display = "N/A"
            else:
                first_in_display = times['first_in'].strftime('%H:%M:%S') if times['first_in'] else 'N/A'

                if times['is_currently_inside']:
                    last_out_display = "Still Inside"
                else:
                    last_out_display = times['last_out'].strftime('%H:%M:%S') if times['last_out'] else 'N/A'

                inside_time_display = format_seconds(times['total_inside_seconds']) if times[
                                                                                           'total_inside_seconds'] is not None else "00:00:00"
                outside_time_display = format_seconds(times['total_outside_seconds']) if times[
                                                                                             'total_outside_seconds'] is not None else "00:00:00"
                total_span_display = format_seconds(times['total_span_seconds']) if times[
                                                                                        'total_span_seconds'] is not None and \
                                                                                    times[
                                                                                        'total_span_seconds'] > 0 else "00:00:00"

            final_logs.append({
                'date': log_date.strftime('%d.%m.%Y'),
                'name': transactions[0]['name'],
                'last_name': transactions[0]['last_name'],
                'first_in': first_in_display,
                'last_out': last_out_display,
                'inside_time': inside_time_display,
                'outside_time': outside_time_display,
                'total_inside_seconds': times['total_inside_seconds'],
                'total_outside_seconds': times['total_outside_seconds'],
                'total_span_seconds': times['total_span_seconds'],
                'is_currently_inside': times['is_currently_inside'],
                'is_invalid_day': times['is_invalid_day'],
                'status_display': status_display,
                'status_color': status_color,
                'status_class': status_class
            })

        # 4. Add missing workdays from first data date to today
        if person_key and employee_first_date:
            # BAKU TIME FIX: datetime.now().date() -> get_current_baku_time().date()
            today = get_current_baku_time().date()
            current_date = employee_first_date

            while current_date <= today:
                # Check if it's a workday (Monday to Friday)
                if current_date.weekday() < 5:  # 0=Monday, 4=Friday
                    # Check if we already have data for this date
                    date_str = current_date.strftime('%d.%m.%Y')
                    existing_log = next((log for log in final_logs if log['date'] == date_str), None)

                    if not existing_log:
                        # Add missing workday with zero attendance
                        final_logs.append({
                            'date': date_str,
                            'name': employee_name,
                            'last_name': employee_last_name,
                            'first_in': 'N/A',
                            'last_out': 'N/A',
                            'inside_time': '00:00:00',
                            'outside_time': '00:00:00',
                            'total_inside_seconds': 0,
                            'total_outside_seconds': 0,
                            'total_span_seconds': 0,
                            'is_currently_inside': False,
                            'is_invalid_day': False,
                            'status_display': '✗ Absent',
                            'status_color': '#dc3545',
                            'status_class': 'absent'
                        })

                current_date += timedelta(days=1)

        # Sort from newest to oldest
        final_logs.sort(key=lambda x: datetime.strptime(x['date'], '%d.%m.%Y'), reverse=True)
        return final_logs

    except Exception as e:
        print(f"🚨 Employee Logs Processing Error: {e}")
        return []
    finally:
        if cur: cur.close()
        if conn: conn.close()


@app.context_processor
def utility_processor():
    return dict(format_seconds=format_seconds)


@app.template_filter('str_to_date')
def str_to_date_filter(date_str):
    """Convert string to date object for template"""
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None


@app.route('/api/employee_search')
def api_employee_search():
    """AJAX endpoint for employee search dropdown"""
    if (redirect_response := require_login()):
        return jsonify([])

    search_term = request.args.get('q', '').strip().lower()

    if not search_term or len(search_term) < 2:
        return jsonify([])

    conn = get_db_connection()
    if conn is None: return jsonify([])

    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT p.name, p.last_name 
            FROM public.pers_person p
            LEFT JOIN public.pers_position pp ON p.position_id = pp.id
            WHERE (pp.name IS NULL 
                   OR (pp.name NOT ILIKE 'STUDENT' 
                       AND pp.name NOT ILIKE 'VISITOR'
                       AND pp.name NOT ILIKE 'MÜƏLLİM')) -- Student, Visitor ve Müəllim Filtresi
            AND (LOWER(p.name) LIKE %s OR LOWER(p.last_name) LIKE %s OR LOWER(p.name || ' ' || p.last_name) LIKE %s)
            ORDER BY p.last_name, p.name
            LIMIT 20
        """, (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%'))

        results = []
        for name, last_name in cur.fetchall():
            full_name = f"{name} {last_name}"
            key = normalize_name(name) + normalize_name(last_name)
            results.append({'key': key, 'name': full_name})

        return jsonify(results)
    except Exception as e:
        print(f"🚨 Employee Search Error: {e}")
        return jsonify([])
    finally:
        if cur: cur.close()
        if conn: conn.close()


def get_tracked_hours_by_dates(person_key, start_date, end_date):
    """
    Calculates total worked time (time spent inside) and daily statuses
    for a specific employee within a specific date range, ignoring weekends.
    """
    conn = get_db_connection()
    if conn is None: return {'logs': [], 'total_time_str': '00:00:00'}

    cur = conn.cursor()

    global EIGHT_HOURS_SECONDS

    # Store daily data initially
    daily_data = defaultdict(lambda: {'total_inside_seconds': 0, 'status_code': 'D'})
    total_tracked_seconds = 0

    # Convert date objects to datetime objects for query, ensuring the full day is included.
    start_dt = datetime.combine(start_date, datetime.min.time())
    end_dt = datetime.combine(end_date, datetime.max.time())

    try:
        # Use the date range in the database query.
        cur.execute("""
                    SELECT t.name, t.last_name, t.create_time, t.reader_name
                    FROM public.acc_transaction t
                             INNER JOIN public.pers_person p ON t.name = p.name AND t.last_name = p.last_name
                             LEFT JOIN public.pers_position pp ON p.position_id = pp.id
                    WHERE t.create_time BETWEEN %s AND %s
                      AND (pp.name IS NULL 
                           OR (pp.name NOT ILIKE 'student' 
                               AND pp.name NOT ILIKE 'visitor'
                               AND pp.name NOT ILIKE 'müəllim')) -- Student, Visitor ve Müəllim Filtresi
                    ORDER BY t.create_time;
                    """, (start_dt, end_dt))

        raw_transactions = cur.fetchall()

        daily_transactions = defaultdict(list)
        for t_name, t_last_name, create_time, reader_name in raw_transactions:
            if create_time is None or not t_name or not t_last_name:
                continue

            t_key = normalize_name(t_name) + normalize_name(t_last_name)
            if t_key != person_key:
                continue

            log_date = create_time.date()

            # SADECE RAKAM KONTROLÜ - Building A-1 pattern'ine göre
            direction_type = None
            if reader_name:
                import re
                numbers = re.findall(r'\d+', reader_name)
                if numbers:
                    reader_number = int(numbers[0])
                    if reader_number in [1, 2]:
                        direction_type = 'in'
                    elif reader_number in [3, 4]:
                        direction_type = 'out'

            if not direction_type:
                # Eğer rakam bulunamadıysa veya 1-4 arasında değilse, bu kaydı yok say
                continue

            daily_transactions[log_date].append({'time': create_time, 'direction': direction_type})

        # Calculate working times and status for each day with logs
        for log_date, transactions in daily_transactions.items():
            if log_date.weekday() >= 5:
                continue

            times = calculate_times_from_transactions(transactions)
            total_inside_seconds = times['total_inside_seconds']

            if total_inside_seconds >= EIGHT_HOURS_SECONDS:
                status_code = 'T'  # Full Day (Green)
            elif total_inside_seconds > 0:
                status_code = 'E'  # Short Hours (Yellow/Orange)
            else:
                status_code = 'D'  # Absent (Red)

            daily_data[log_date]['total_inside_seconds'] = total_inside_seconds
            daily_data[log_date]['status_code'] = status_code

        # Prepare Results (Iterating over the entire date range)
        tracked_logs = []
        current_day = start_date

        while current_day <= end_date:
            day_data = daily_data.get(current_day, {'total_inside_seconds': 0, 'status_code': 'D'})

            if current_day.weekday() < 5:
                tracked_logs.append({
                    'date': current_day.strftime('%a, %b %d'),
                    'seconds': day_data['total_inside_seconds'],
                    'time_str': format_seconds(day_data['total_inside_seconds']),
                    'status': day_data['status_code']
                })
                total_tracked_seconds += day_data['total_inside_seconds']

            current_day += timedelta(days=1)

        # Sort from newest to oldest
        tracked_logs.reverse()

        return {
            'logs': tracked_logs,
            'total_time_str': format_seconds(total_tracked_seconds)
        }

    except Exception as e:
        print(f"🚨 Time Calculation Error: {e}")
        return {'logs': [], 'total_time_str': '00:00:00'}
    finally:
        if cur: cur.close()
        if conn: conn.close()


# --------------------------------------------------------------------------------------
# --- SYSTEM USER MANAGEMENT FUNCTIONS (ADMIN) ---
# --------------------------------------------------------------------------------------

def get_all_system_users():
    """Tüm sistem kullanıcılarını getirir."""
    conn = get_db_connection()
    if conn is None: return []

    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT id, email, full_name, user_role, is_active, created_at, last_login
            FROM public.system_users 
            ORDER BY full_name
        """)
        
        users = []
        for row in cur.fetchall():
            users.append({
                'id': row[0],
                'email': row[1],
                'full_name': row[2],
                'user_role': row[3],
                'is_active': row[4],
                'created_at': row[5].strftime('%d.%m.%Y %H:%M') if row[5] else 'N/A',
                'last_login': row[6].strftime('%d.%m.%Y %H:%M') if row[6] else 'Hiç giriş yapmamış'
            })
        return users
    except psycopg2.Error as e:
        print(f"🚨 System Users Fetch Error: {e}")
        return []
    finally:
        if cur: cur.close()
        if conn: conn.close()


def get_system_user_by_id(user_id):
    """ID'ye göre sistem kullanıcısını getirir."""
    conn = get_db_connection()
    if conn is None: return None

    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT id, email, full_name, user_role, is_active, created_at, last_login
            FROM public.system_users 
            WHERE id = %s
        """, (user_id,))
        
        row = cur.fetchone()
        if row:
            return {
                'id': row[0],
                'email': row[1],
                'full_name': row[2],
                'user_role': row[3],
                'is_active': row[4],
                'created_at': row[5].strftime('%d.%m.%Y %H:%M') if row[5] else 'N/A',
                'last_login': row[6].strftime('%d.%m.%Y %H:%M') if row[6] else 'Hiç giriş yapmamış'
            }
        return None
    except psycopg2.Error as e:
        print(f"🚨 System User Fetch Error: {e}")
        return None
    finally:
        if cur: cur.close()
        if conn: conn.close()


def update_system_user(user_id, data):
    """Updates system user."""
    conn = get_db_connection()
    if conn is None:
        return False, "Database connection error."

    cur = conn.cursor()
    try:
        # Şifre güncellemesi varsa
        if 'password' in data:
            cur.execute("""
                UPDATE public.system_users
                SET full_name = %s, email = %s, user_role = %s, is_active = %s, password = %s
                WHERE id = %s
            """, (
                data.get('full_name'),
                data.get('email'),
                data.get('user_role'),
                data.get('is_active'),
                data.get('password'),
                user_id
            ))
        else:
            cur.execute("""
                UPDATE public.system_users
                SET full_name = %s, email = %s, user_role = %s, is_active = %s
                WHERE id = %s
            """, (
                data.get('full_name'),
                data.get('email'),
                data.get('user_role'),
                data.get('is_active'),
                user_id
            ))
        
        conn.commit()
        return True, "User successfully updated."
    except psycopg2.Error as e:
        conn.rollback()
        print(f"🚨 System User Update Error: {e}")
        return False, f"Update error: {e}"
    finally:
        if cur: cur.close()
        if conn: conn.close()


def create_system_user(data):
    """Creates new system user."""
    conn = get_db_connection()
    if conn is None:
        return False, "Database connection error."

    cur = conn.cursor()
    try:
        # Email kontrolü
        cur.execute("SELECT id FROM public.system_users WHERE email = %s", (data.get('email'),))
        if cur.fetchone():
            return False, "This email address is already in use."
        
        # Şifreyi hash'le
        hashed_password = hash_password(data.get('password'))
        
        cur.execute("""
            INSERT INTO public.system_users (email, password, full_name, user_role, is_active, created_at)
            VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
        """, (
            data.get('email'),
            hashed_password,
            data.get('full_name'),
            data.get('user_role'),
            data.get('is_active', True)
        ))
        
        conn.commit()
        return True, "User successfully created."
    except psycopg2.Error as e:
        conn.rollback()
        print(f"🚨 System User Create Error: {e}")
        return False, f"Creation error: {e}"
    finally:
        if cur: cur.close()
        if conn: conn.close()


# --------------------------------------------------------------------------------------
# --- EMPLOYEE DAILY NOTES FUNCTIONS ---
# --------------------------------------------------------------------------------------

def get_employee_daily_note(employee_id, note_date):
    """Fetches daily note for a specific employee and date."""
    conn = get_db_connection()
    if conn is None: return None

    cur = conn.cursor()
    try:
        cur.execute("""
                    SELECT note_text
                    FROM public.employee_daily_notes
                    WHERE employee_id = %s
                      AND note_date = %s
                    """, (str(employee_id), note_date))

        result = cur.fetchone()
        return result[0] if result else ""
    except psycopg2.Error as e:
        print(f"🚨 Get Daily Note Error: {e}")
        return ""
    finally:
        if cur: cur.close()
        if conn: conn.close()


def save_employee_daily_note(employee_id, note_date, note_text, created_by='admin'):
    """Saves or updates daily note for an employee."""
    conn = get_db_connection()
    if conn is None: return False, "Database connection error."

    cur = conn.cursor()
    try:
        cur.execute("""
                    INSERT INTO public.employee_daily_notes
                        (employee_id, note_date, note_text, created_by, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP) ON CONFLICT (employee_id, note_date) 
            DO
                    UPDATE SET
                        note_text = EXCLUDED.note_text,
                        updated_at = CURRENT_TIMESTAMP
                    """, (str(employee_id), note_date, note_text, created_by))

        conn.commit()
        return True, "Note saved successfully."
    except psycopg2.Error as e:
        conn.rollback()
        print(f"🚨 Save Daily Note Error: {e}")
        return False, f"Save error: {e}"
    finally:
        if cur: cur.close()
        if conn: conn.close()


def get_employee_logs_monthly(selected_month, selected_year, search_term="", page=1, per_page=PER_PAGE_ATTENDANCE):
    conn = get_db_connection()
    if conn is None:
        return {'headers': [], 'logs': [], 'current_month': selected_month, 'current_year': selected_year,
                'month_name': 'Error', 'total_items': 0, 'total_pages': 1, 'current_page': page, 'per_page': per_page}

    cur = conn.cursor()

    global EIGHT_HOURS_SECONDS

    try:
        start_date = date(selected_year, selected_month, 1)

        if selected_month == 12:
            end_date = date(selected_year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(selected_year, selected_month + 1, 1) - timedelta(days=1)

        days_in_month = end_date.day

    except ValueError:
        # BAKU TIME FIX: date.today() -> get_current_baku_time().date()
        today = get_current_baku_time().date()
        selected_month = today.month
        selected_year = today.year
        start_date = date(selected_year, selected_month, 1)
        if selected_month == 12:
            end_date = date(selected_year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(selected_year, selected_month + 1, 1) - timedelta(days=1)
        days_in_month = end_date.day

    daily_transactions = defaultdict(list)
    employee_daily_status = defaultdict(lambda: defaultdict(str))
    employee_list = []

    try:
        # 1. Fetch all employees (FILTERED)
        if search_term:
            cur.execute("""
                        SELECT p.id, p.name, p.last_name, pp.name AS position_name
                        FROM public.pers_person p
                                 LEFT JOIN public.pers_position pp ON p.position_id = pp.id
                        WHERE (pp.name IS NULL 
                               OR (pp.name NOT ILIKE 'STUDENT' 
                                   AND pp.name NOT ILIKE 'VISITOR'
                                   AND pp.name NOT ILIKE 'MÜƏLLİM')) -- Student, Visitor ve Müəllim Filtresi
                          AND (LOWER(p.name) LIKE %s OR LOWER(p.last_name) LIKE %s OR
                               LOWER(p.name || ' ' || p.last_name) LIKE %s)
                        ORDER BY p.last_name, p.name
                        """, (f'%{search_term.lower()}%', f'%{search_term.lower()}%', f'%{search_term.lower()}%'))
        else:
            cur.execute("""
                        SELECT p.id, p.name, p.last_name, pp.name AS position_name
                        FROM public.pers_person p
                                 LEFT JOIN public.pers_position pp ON p.position_id = pp.id
                        WHERE pp.name IS NULL
                           OR (pp.name NOT ILIKE 'STUDENT' 
                               AND pp.name NOT ILIKE 'VISITOR'
                               AND pp.name NOT ILIKE 'MÜƏLLİM') -- Student, Visitor ve Müəllim Filtresi
                        ORDER BY p.last_name, p.name
                        """)

        person_data = cur.fetchall()

        for id_val, name, last_name, position_name in person_data:
            key = normalize_name(name) + normalize_name(last_name)
            full_name = f"{name} {last_name}"
            employee_list.append(
                {'key': key, 'id': id_val, 'name': name, 'last_name': last_name, 'full_name': full_name})

        # 2. Fetch all movements within the date range
        cur.execute("""
                    SELECT t.name, t.last_name, t.create_time, t.reader_name
                    FROM public.acc_transaction t
                             INNER JOIN public.pers_person p ON t.name = p.name AND t.last_name = p.last_name
                             LEFT JOIN public.pers_position pp ON p.position_id = pp.id
                    WHERE t.create_time >= %s
                      AND t.create_time <= %s
                      AND (pp.name IS NULL 
                           OR (pp.name NOT ILIKE 'student' 
                               AND pp.name NOT ILIKE 'visitor'
                               AND pp.name NOT ILIKE 'müəllim')) -- Student, Visitor ve Müəllim Filtresi
                    ORDER BY t.create_time;
                    """, (datetime.combine(start_date, datetime.min.time()),
                          datetime.combine(end_date, datetime.max.time())))

        raw_transactions = cur.fetchall()

        # 3. Process transactions and Grouping
        for t_name, t_last_name, create_time, reader_name in raw_transactions:
            if create_time is None or not t_name or not t_last_name:
                continue

            log_date = create_time.date()

            # YENİ GÜNCELLENMİŞ IN/OUT TESPİT ALGORİTMASI - SADECE RAKAMLAR
            direction_type = None
            if reader_name:
                import re
                # Sadece rakamları bul
                numbers = re.findall(r'\d+', reader_name)
                if numbers:
                    reader_number = int(numbers[0])
                    # 1 ve 2: GİRİŞ, 3 ve 4: ÇIKIŞ
                    if reader_number in [1, 2]:
                        direction_type = 'in'
                    elif reader_number in [3, 4]:
                        direction_type = 'out'

            if not direction_type:
                # Eğer rakam bulunamadıysa veya 1-4 arasında değilse, yok say
                continue

            t_key = normalize_name(t_name) + normalize_name(t_last_name)
            key = (log_date, t_key)
            daily_transactions[key].append({'time': create_time, 'direction': direction_type})

        # 4. Determine Daily Status
        for (log_date, person_key), transactions in daily_transactions.items():
            if not any(emp['key'] == person_key for emp in employee_list):
                continue

            day_number = log_date.day
            times = calculate_times_from_transactions(transactions)
            total_inside_seconds = times['total_inside_seconds']

            if total_inside_seconds is None:
                status_code = 'D'
            elif total_inside_seconds >= EIGHT_HOURS_SECONDS:
                status_code = 'T'
            elif total_inside_seconds > 0:
                status_code = 'E'
            else:
                status_code = 'D'

            employee_daily_status[person_key][day_number] = status_code

        # 5. Prepare Results for HTML
        day_headers = []
        current_day = start_date
        while current_day <= end_date:
            if current_day.weekday() < 5:
                day_headers.append(current_day.day)
            current_day += timedelta(days=1)

        final_logs = []
        # BAKU TIME FIX: date.today() -> get_current_baku_time().date()
        today = get_current_baku_time().date()

        for emp in employee_list:
            row = {
                'id': emp['id'],
                'name': emp['full_name'],
                'days': []
            }
            current_day = start_date
            while current_day <= end_date:
                if current_day.weekday() < 5:
                    day_number = current_day.day

                    if current_day > today:
                        status = 'N'
                    else:
                        status = employee_daily_status[emp['key']].get(day_number, 'D')

                    row['days'].append(status)
                current_day += timedelta(days=1)

            final_logs.append(row)

        # 6. Apply Pagination
        total_items = len(final_logs)
        total_pages = (total_items + per_page - 1) // per_page

        if page < 1:
            page = 1
        if page > total_pages and total_pages > 0:
            page = total_pages

        start_index = (page - 1) * per_page
        end_index = start_index + per_page
        paginated_logs = final_logs[start_index:end_index]

        return {
            'headers': day_headers,
            'logs': paginated_logs,
            'current_month': selected_month,
            'current_year': selected_year,
            'month_name': start_date.strftime('%B'),
            'total_items': total_items,
            'total_pages': total_pages,
            'current_page': page,
            'per_page': per_page
        }

    except Exception as e:
        print(f"🚨 Monthly Attendance Processing Error: {e}")
        return {'headers': [], 'logs': [], 'current_month': selected_month, 'current_year': selected_year,
                'month_name': 'Error', 'total_items': 0, 'total_pages': 1, 'current_page': page, 'per_page': per_page}
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def get_dashboard_data():
    conn = get_db_connection()
    data = {'total_employees': 0, 'total_departments': 0, 'total_transactions': 0,
            'new_employees_this_month': 0, 'today_birthdays': [],
            'present_employees_count': 0,
            'attendance_percentage': 0.0,
            'absent_employees': [],
            'late_employees': []}

    if conn is None: return data

    cur = conn.cursor()
    try:
        # BAKU TIME FIX: date.today() -> get_current_baku_time().date()
        today_date = get_current_baku_time().date()

        # 1. Total Employees
        cur.execute("""SELECT COUNT(*)
                       FROM public.pers_person p
                                LEFT JOIN public.pers_position pp ON p.position_id = pp.id
                       WHERE pp.name IS NULL
                          OR (pp.name NOT ILIKE 'STUDENT' 
                              AND pp.name NOT ILIKE 'VISITOR'
                              AND pp.name NOT ILIKE 'MÜƏLLİM')""")
        data['total_employees'] = cur.fetchone()[0]

        # 2. Total Departments
        cur.execute("SELECT COUNT(*) FROM public.auth_department")
        data['total_departments'] = cur.fetchone()[0]

        # 3. Today's Total Transactions
        cur.execute("""SELECT COUNT(t.*)
                       FROM public.acc_transaction t
                                INNER JOIN public.pers_person p ON t.name = p.name AND t.last_name = p.last_name
                                LEFT JOIN public.pers_position pp ON p.position_id = pp.id
                       WHERE DATE (t.create_time) = %s 
                         AND (pp.name IS NULL 
                              OR (pp.name NOT ILIKE 'student' 
                                  AND pp.name NOT ILIKE 'visitor'
                                  AND pp.name NOT ILIKE 'müəllim'))""",
                    (today_date,))
        data['total_transactions'] = cur.fetchone()[0]

        # 4. New Employees This Month
        cur.execute("""SELECT COUNT(p.*)
                       FROM public.pers_person p
                                LEFT JOIN public.pers_position pp ON p.position_id = pp.id
                       WHERE date_trunc('month', p.create_time) = date_trunc('month', NOW())
                         AND (pp.name IS NULL 
                              OR (pp.name NOT ILIKE 'student' 
                                  AND pp.name NOT ILIKE 'visitor'
                                  AND pp.name NOT ILIKE 'müəllim'))""")
        data['new_employees_this_month'] = cur.fetchone()[0]

        # 5. Employees Present Today
        cur.execute("""
                    SELECT COUNT(DISTINCT (t.name, t.last_name))
                    FROM public.acc_transaction t
                             INNER JOIN public.pers_person p ON t.name = p.name AND t.last_name = p.last_name
                             LEFT JOIN public.pers_position pp ON p.position_id = pp.id
                    WHERE DATE (t.create_time) = %s
                      AND t.reader_name ILIKE '%%-in%%'
                      AND (pp.name IS NULL
                       OR (pp.name NOT ILIKE 'student' 
                           AND pp.name NOT ILIKE 'visitor'
                           AND pp.name NOT ILIKE 'müəllim'))
                    """, (today_date,))
        data['present_employees_count'] = cur.fetchone()[0]

        # 6. ABSENT EMPLOYEES
        cur.execute("""
                    SELECT p.name, p.last_name, pp.name as position_name
                    FROM public.pers_person p
                    LEFT JOIN public.pers_position pp ON p.position_id = pp.id
                    WHERE (pp.name IS NULL 
                           OR (pp.name NOT ILIKE 'STUDENT' 
                               AND pp.name NOT ILIKE 'VISITOR'
                               AND pp.name NOT ILIKE 'MÜƏLLİM'))
                    AND NOT EXISTS (
                        SELECT 1 
                        FROM public.acc_transaction t 
                        WHERE t.name = p.name 
                        AND t.last_name = p.last_name 
                        AND DATE(t.create_time) = %s
                    )
                    ORDER BY p.last_name, p.name
                    """, (today_date,))

        absent_employees_raw = cur.fetchall()
        absent_list = []
        for name, last_name, position in absent_employees_raw:
            absent_list.append({
                'full_name': f"{name} {last_name}",
                'position': position or 'Undefined'
            })
        data['absent_employees'] = absent_list

        # 7. LATE EMPLOYEES
        cur.execute("""
            SELECT 
                p.name,
                p.last_name,
                p.id as person_id,
                MIN(t.create_time) as first_in_time,
                pae.attr_value4 as expected_time
            FROM public.pers_person p
            LEFT JOIN public.pers_attribute_ext pae ON p.id = pae.person_id
            INNER JOIN public.acc_transaction t ON t.name = p.name AND t.last_name = p.last_name
            LEFT JOIN public.pers_position pp ON p.position_id = pp.id
            WHERE DATE(t.create_time) = %s
              AND pae.attr_value4 IS NOT NULL
              AND t.reader_name ILIKE '%%-in%%'
              AND (pp.name IS NULL 
                   OR (pp.name NOT ILIKE 'student' 
                       AND pp.name NOT ILIKE 'visitor'
                       AND pp.name NOT ILIKE 'müəllim'))
            GROUP BY p.name, p.last_name, p.id, pae.attr_value4
            HAVING MIN(t.create_time) IS NOT NULL
            ORDER BY p.last_name, p.name
        """, (today_date,))

        late_employees_raw = cur.fetchall()
        late_list = []

        for name, last_name, person_id, first_in_time, expected_time_str in late_employees_raw:
            if expected_time_str:
                try:
                    time_parts = expected_time_str.strip().split()
                    if len(time_parts) >= 2:
                        expected_hour = int(time_parts[0])
                        expected_minute = int(time_parts[1])

                        expected_datetime = datetime.combine(today_date, datetime.min.time()).replace(
                            hour=expected_hour, minute=expected_minute
                        )

                        late_minutes = (first_in_time - expected_datetime).total_seconds() / 60

                        if late_minutes > 30:
                            expected_time_display = f"{expected_hour:02d}:{expected_minute:02d}"
                            late_list.append({
                                'full_name': f"{name} {last_name}",
                                'person_id': person_id,
                                'expected_time': expected_time_display,
                                'arrival_time': first_in_time.strftime('%H:%M'),
                                'late_minutes': int(late_minutes)
                            })
                except (ValueError, IndexError) as e:
                    print(f"⚠ Beklenen zaman format hatası: {expected_time_str} - {e}")
                    continue

        data['late_employees'] = late_list

        # Attendance Percentage
        total = data['total_employees']
        present = data['present_employees_count']

        if total > 0:
            percentage = (present / total) * 100
            data['attendance_percentage'] = round(percentage, 2)

        # 8. Birthdays Today
        # BAKU TIME FIX: datetime.now().strftime -> get_current_baku_time().strftime
        today_m_d = get_current_baku_time().strftime('%m-%d')
        cur.execute("""
                    SELECT p.id, p.name, p.last_name, p.birthday, pp.name as position_name
                    FROM public.pers_person p
                             LEFT JOIN public.pers_position pp ON p.position_id = pp.id
                    WHERE TO_CHAR(p.birthday, 'MM-DD') = %s
                      AND (pp.name IS NULL 
                           OR (pp.name NOT ILIKE 'student' 
                               AND pp.name NOT ILIKE 'visitor'
                               AND pp.name NOT ILIKE 'müəllim'))
                    ORDER BY p.last_name, p.name;
                    """, (today_m_d,))

        today_birthdays_raw = cur.fetchall()
        birthday_list = []
        for id_val, name, last_name_val, birthday_date, position_name in today_birthdays_raw:
            birth_date_str = birthday_date.strftime('%d.%m.%Y') if isinstance(birthday_date,
                                                                              (datetime, date)) else 'N/A'
            birthday_list.append(
                {'person_id': id_val, 'name': name, 'surname': last_name_val, 'position': position_name,
                 'birth_date_str': birth_date_str})
        data['today_birthdays'] = birthday_list

    except psycopg2.Error as e:
        print(f"🚨 Dashboard Query Error: {e}")
    finally:
        if cur: cur.close()
        if conn: conn.close()
    return data


# ***************************************************************
# --- FLASK ROUTES (ROUTES) ---
# ***************************************************************

@app.route('/', methods=['GET', 'POST'])
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

        # Geçici: Hem hash'li hem düz metin şifre kontrolü
        password_valid = False
        if user:
            if user['password'].startswith('sha256$'):
                # Hash'li şifre kontrolü
                password_valid = verify_password(user['password'], password)
            else:
                # Düz metin şifre kontrolü (geçici)
                password_valid = (user['password'] == password)

        if user and password_valid:
            session['user'] = {
                'id': user['id'],
                'email': user['email'],
                'full_name': user['full_name'],
                'role': user['role']
            }

            update_last_login(user['id'])

            flash(f'Welcome back, {user["full_name"]}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password!', 'danger')$'):
                # Hash'li şifre kontrolü
                password_valid = verify_password(user['password'], password)
            else:
                # Düz metin şifre kontrolü (geçici)
                password_valid = (user['password'] == password)

        if user and password_valid:
            session['user'] = {
                'id': user['id'],
                'email': user['email'],
                'full_name': user['full_name'],
                'role': user['role']
            }

            update_last_login(user['id'])

            flash(f'Welcome back, {user["full_name"]}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password!', 'danger')

    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    if (redirect_response := require_login()): return redirect_response
    dashboard_data = get_dashboard_data()
    return render_template('dashboard.html', data=dashboard_data)


@app.route('/employees')
def employees():
    if (redirect_response := require_login()): return redirect_response

    employees_list = get_employee_list()

    return render_template(
        'employees.html',
        employees=employees_list
    )


@app.route('/api/employees_list')
def api_employees_list():
    """AJAX endpoint for employees list with search"""
    if (redirect_response := require_login()):
        return jsonify([])

    search_term = request.args.get('search', '').strip().lower()

    # Azerbaycan harfleri için normalize etme
    def normalize_az(text):
        if not text:
            return ''
        replacements = {
            'ə': 'e', 'ü': 'u', 'ö': 'o', 'ğ': 'g',
            'ş': 's', 'ç': 'c', 'ı': 'i',
            'Ə': 'E', 'Ü': 'U', 'Ö': 'O', 'Ğ': 'G',
            'Ş': 'S', 'Ç': 'C', 'I': 'I'
        }
        for az_char, en_char in replacements.items():
            text = text.replace(az_char, en_char)
        return text

    employees_list = get_employee_list()

    if search_term:
        normalized_search = normalize_az(search_term)
        filtered_employees = []
        for emp in employees_list:
            search_data = normalize_az(
                emp['name'] + ' ' +
                emp['last_name'] + ' ' +
                emp['position'] + ' ' +
                emp['email'] + ' ' +
                emp['mobile_phone']
            ).lower()
            if normalized_search in search_data:
                filtered_employees.append(emp)
        return jsonify(filtered_employees)

    return jsonify(employees_list)


@app.route('/employees/edit/<employee_id>', methods=['GET', 'POST'])
def edit_employee(employee_id):
    if (redirect_response := require_login()): return redirect_response

    positions = get_all_positions()

    if request.method == 'POST':
        data = {
            'name': request.form.get('name'),
            'last_name': request.form.get('last_name'),
            'mobile_phone': request.form.get('mobile_phone'),
            'email': request.form.get('email'),
            'birthday': request.form.get('birthday'),
            'position_id': request.form.get('position_id')
        }

        success, message = update_employee_details(employee_id, data)

        if success:
            flash(message, 'success')
            return redirect(url_for('employees'))
        else:
            flash(message, 'danger')

    employee = get_employee_details(employee_id)

    if not employee:
        flash("Employee not found.", 'danger')
        return redirect(url_for('employees'))

    return render_template(
        'employee_edit.html',
        employee=employee,
        positions=positions
    )


@app.route('/employees/export')
def export_employees():
    if (redirect_response := require_login()): return redirect_response

    employees_list = get_employee_list()

    si = StringIO()
    cw = csv.writer(si)

    header = [
        'ID',
        'Name',
        'Last Name',
        'Position',
        'Email',
        'Mobile Phone',
        'Birthday',
        'Hire Date'
    ]
    cw.writerow(header)

    for emp in employees_list:
        cw.writerow([
            emp['id'],
            emp['name'],
            emp['last_name'],
            emp['position'],
            emp['email'],
            emp['mobile_phone'],
            emp['birthday'],
            emp['hire_date']
        ])

    output = si.getvalue()

    response = make_response(output)
    response.headers["Content-Disposition"] = "attachment; filename=employees_export.csv"
    response.headers["Content-type"] = "text/csv"

    return response


@app.route('/api/save_daily_note', methods=['POST'])
def api_save_daily_note():
    if (redirect_response := require_login()):
        return jsonify({'success': False, 'message': 'Login required'})

    try:
        data = request.get_json()
        employee_id = data.get('employee_id')
        note_date = data.get('note_date')
        note_text = data.get('note_text', '').strip()

        if not employee_id or not note_date:
            return jsonify({'success': False, 'message': 'Missing required fields'})

        try:
            note_date = datetime.strptime(note_date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid date format'})

        success, message = save_employee_daily_note(
            employee_id,
            note_date,
            note_text,
            created_by=session.get('user', 'admin')
        )

        return jsonify({'success': success, 'message': message})

    except Exception as e:
        print(f"🚨 API Save Note Error: {e}")
        return jsonify({'success': False, 'message': 'Server error'})


@app.route('/api/get_daily_note', methods=['GET'])
def api_get_daily_note():
    if (redirect_response := require_login()):
        return jsonify({'note': ''})

    try:
        employee_id = request.args.get('employee_id')
        note_date = request.args.get('note_date')

        if not employee_id or not note_date:
            return jsonify({'note': ''})

        try:
            note_date = datetime.strptime(note_date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'note': ''})

        note_text = get_employee_daily_note(employee_id, note_date)
        return jsonify({'note': note_text})

    except Exception as e:
        print(f"🚨 API Get Note Error: {e}")
        return jsonify({'note': ''})


@app.route('/employee_logs/export', methods=['GET'])
def export_employee_logs():
    if (redirect_response := require_login()): return redirect_response

    person_key = request.args.get('person_key', None)
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    # Date parsing for export
    start_date = None
    end_date = None

    try:
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except ValueError:
        pass

    logs_data = get_employee_logs(person_key=person_key, start_date=start_date, end_date=end_date)

    if not logs_data:
        return make_response("No data found for export.", 404)

    si = StringIO()
    cw = csv.writer(si)

    header = [
        'Date',
        'Employee First Name',
        'Employee Last Name',
        'First In',
        'Last Out',
        'Total INSIDE Time (HH:MM:SS)',
        'Total OUTSIDE Time (HH:MM:SS)',
        'Total INSIDE Time (Seconds)',
        'Total SPAN Time (Seconds)'
    ]
    cw.writerow(header)

    for log in logs_data:
        cw.writerow([
            log['date'],
            log['name'],
            log['last_name'],
            log['first_in'],
            log['last_out'],
            log['inside_time'],
            log['outside_time'],
            log['total_inside_seconds'],
            log.get('total_span_seconds', 0)
        ])

    output = si.getvalue()

    if person_key:
        if start_date and end_date:
            filename = f"log_export_{person_key}_{start_date_str}_to_{end_date_str}.csv"
        else:
            filename = f"log_export_{person_key}.csv"
    else:
        if start_date and end_date:
            filename = f"log_export_all_employees_{start_date_str}_to_{end_date_str}.csv"
        else:
            filename = "log_export_all_employees.csv"

    response = make_response(output)
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    response.headers["Content-type"] = "text/csv"

    return response


@app.route('/employee_logs', methods=['GET', 'POST'])
def employee_logs():
    if (redirect_response := require_login()): return redirect_response

    employee_list = get_employee_list_for_dropdown()
    selected_person_key = None
    selected_employee_name = "All Employees"
    start_date_str = None
    end_date_str = None

    # BAKU TIME FIX: datetime.now().date() -> get_current_baku_time().date()
    today = get_current_baku_time().date()

    if today.weekday() >= 5:
        days_back = (today.weekday() - 4) % 7
        if days_back == 0:
            days_back = 7
        last_workday = today - timedelta(days=days_back)
        start_date_str = last_workday.strftime('%Y-%m-%d')
        end_date_str = last_workday.strftime('%Y-%m-%d')
    else:
        start_date_str = today.strftime('%Y-%m-%d')
        end_date_str = today.strftime('%Y-%m-%d')

    if request.method == 'POST':
        selected_person_key = request.form.get('person_key')
        start_date_str = request.form.get('start_date') or start_date_str
        end_date_str = request.form.get('end_date') or end_date_str
    else:
        selected_person_key = request.args.get('person_key') or ''
        start_date_str = request.args.get('start_date') or start_date_str
        end_date_str = request.args.get('end_date') or end_date_str

    start_date = None
    end_date = None

    try:
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except ValueError:
        pass

    if selected_person_key:
        selected_employee = next((emp for emp in employee_list if emp['key'] == selected_person_key), None)
        if selected_employee:
            selected_employee_name = selected_employee['name']
    else:
        selected_employee_name = "All Employees"

    logs_data = get_employee_logs(person_key=selected_person_key, start_date=start_date, end_date=end_date)

    return render_template(
        'employee_logs.html',
        logs=logs_data,
        employees=employee_list,
        selected_person_key=selected_person_key,
        selected_employee_name=selected_employee_name,
        start_date=start_date_str,
        end_date=end_date_str
    )


@app.route('/attendance', methods=['GET', 'POST'])
def attendance():
    if (redirect_response := require_login()): return redirect_response

    # BAKU TIME FIX: date.today() -> get_current_baku_time().date()
    today = get_current_baku_time().date()
    selected_month = today.month
    selected_year = today.year
    page = int(request.args.get('page', 1))
    search_term = request.args.get('search', '').strip()

    try:
        selected_month = int(request.args.get('month', selected_month))
        selected_year = int(request.args.get('year', selected_year))
    except ValueError:
        pass

    if search_term and page > 1:
        page = 1

    attendance_data = get_employee_logs_monthly(selected_month, selected_year, search_term, page, PER_PAGE_ATTENDANCE)

    years = list(range(today.year - 2, today.year + 1))

    months = [
        (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
        (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
        (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')
    ]

    return render_template(
        'attendance.html',
        data=attendance_data,
        years=years,
        months=months,
        current_selection={'month': selected_month, 'year': selected_year, 'search': search_term, 'page': page}
    )


@app.route('/api/employees_search')
def api_employees_search():
    if (redirect_response := require_login()): return jsonify([])

    search_term = request.args.get('q', '').lower()

    conn = get_db_connection()
    if conn is None:
        return jsonify([])

    cur = conn.cursor()
    try:
        cur.execute("""
                    SELECT p.name, p.last_name
                    FROM public.pers_person p
                             LEFT JOIN public.pers_position pp ON p.position_id = pp.id
                    WHERE (pp.name IS NULL 
                           OR (pp.name NOT ILIKE 'student' 
                               AND pp.name NOT ILIKE 'visitor'
                               AND pp.name NOT ILIKE 'müəllim')) -- Student, Visitor ve Müəllim Filtresi
                      AND (LOWER(p.name) LIKE %s OR LOWER(p.last_name) LIKE %s)
                    ORDER BY p.last_name, p.name LIMIT 10;
                    """, (f'%{search_term}%', f'%{search_term}%'))

        results = []
        for name, last_name in cur.fetchall():
            full_name = f"{name} {last_name}"
            key = normalize_name(name) + normalize_name(last_name)
            results.append({'id': key, 'text': full_name})

        return jsonify(results)
    except psycopg2.Error as e:
        print(f"🚨 AJAX Search Error: {e}")
        return jsonify([])
    finally:
        if cur: cur.close()
        if conn: conn.close()


@app.route('/attendance/export', methods=['GET'])
def export_monthly_attendance():
    if (redirect_response := require_login()): return redirect_response

    # BAKU TIME FIX: date.today() -> get_current_baku_time().date()
    today = get_current_baku_time().date()
    try:
        selected_month = int(request.args.get('month', today.month))
        selected_year = int(request.args.get('year', today.year))
    except (ValueError, TypeError):
        selected_month = today.month
        selected_year = today.year

    data = get_employee_logs_monthly(selected_month, selected_year, search_term=request.args.get('search', '').strip(),
                                     page=1, per_page=999999)

    if not data or not data.get('logs'):
        return make_response("No monthly attendance data found for export.", 404)

    si = StringIO()
    cw = csv.writer(si)

    month_name = data.get('month_name', 'Month')
    year = data.get('current_year', 'Year')

    header = ['EMPLOYEE'] + [str(d) for d in data.get('headers', [])]
    cw.writerow(header)

    for log in data['logs']:
        row_data = [log['name']] + log['days']
        cw.writerow(row_data)

    output = si.getvalue()

    filename = f"attendance_export_{month_name}_{year}.csv"
    response = make_response(output)
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    response.headers["Content-type"] = "text/csv"

    return response


@app.route('/hours_tracked', methods=['GET'])
def hours_tracked():
    if (redirect_response := require_login()): return redirect_response

    employee_list = get_employee_list_for_dropdown()

    selected_person_key = request.args.get('person_key')
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    tracked_data = {'logs': [], 'total_time_str': '00:00:00'}

    start_date, end_date = None, None
    try:
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except ValueError:
        pass

    if not start_date or not end_date:
        # BAKU TIME FIX: date.today() -> get_current_baku_time().date()
        end_date = get_current_baku_time().date()
        start_date = end_date - timedelta(days=6)

    if start_date > end_date:
        start_date, end_date = end_date, start_date

    if selected_person_key and start_date <= end_date:
        try:
            tracked_data = get_tracked_hours_by_dates(selected_person_key, start_date, end_date)
        except Exception as e:
            flash(f"Data fetching error: {e}", 'danger')

    selected_employee_name = next((emp['name'] for emp in employee_list if emp['key'] == selected_person_key),
                                  "Select Employee")

    return render_template(
        'hours_tracked.html',
        employees=employee_list,
        selected_person_key=selected_person_key,
        start_date=start_date_str,
        end_date=end_date_str,
        selected_employee_name=selected_employee_name,
        tracked_data=tracked_data
    )


@app.route('/admin')
def admin():
    if (redirect_response := require_login()): return redirect_response
    
    # Admin yetkisi kontrolü
    if session.get('user', {}).get('role') != 'admin':
        flash("You don't have permission to access this page.", 'danger')
        return redirect(url_for('dashboard'))
    
    return render_template('admin.html')


@app.route('/admin/users')
def admin_users():
    if (redirect_response := require_login()): return redirect_response
    
    # Admin yetkisi kontrolü
    if session.get('user', {}).get('role') != 'admin':
        flash("You don't have permission to access this page.", 'danger')
        return redirect(url_for('dashboard'))
    
    users = get_all_system_users()
    return render_template('admin_users.html', users=users)


@app.route('/admin/users/edit/<int:user_id>', methods=['GET', 'POST'])
def admin_edit_user(user_id):
    if (redirect_response := require_login()): return redirect_response
    
    # Admin yetkisi kontrolü
    if session.get('user', {}).get('role') != 'admin':
        flash("You don't have permission to access this page.", 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        data = {
            'full_name': request.form.get('full_name'),
            'email': request.form.get('email'),
            'user_role': request.form.get('user_role'),
            'is_active': request.form.get('is_active') == 'on'
        }
        
        # Şifre değişikliği varsa
        new_password = request.form.get('new_password')
        if new_password:
            data['password'] = hash_password(new_password)
        
        success, message = update_system_user(user_id, data)
        
        if success:
            flash(message, 'success')
            return redirect(url_for('admin_users'))
        else:
            flash(message, 'danger')
    
    user = get_system_user_by_id(user_id)
    if not user:
        flash("User not found.", 'danger')
        return redirect(url_for('admin_users'))
    
    return render_template('admin_edit_user.html', user=user)


@app.route('/admin/employees')
def admin_employees():
    if (redirect_response := require_login()): return redirect_response
    
    # Admin yetkisi kontrolü
    if session.get('user', {}).get('role') != 'admin':
        flash("You don't have permission to access this page.", 'danger')
        return redirect(url_for('dashboard'))
    
    # Pagination ve search parametreleri
    page = int(request.args.get('page', 1))
    per_page = 20
    search_term = request.args.get('search', '').strip()
    
    # Çalışanları getir (pagination ve search ile)
    employees_data = get_admin_employees_paginated(page=page, per_page=per_page, search_term=search_term)
    
    return render_template('admin_employees.html', 
                         employees=employees_data['employees'],
                         pagination=employees_data['pagination'])


@app.route('/admin/employees/edit/<employee_id>', methods=['GET', 'POST'])
def admin_edit_employee(employee_id):
    if (redirect_response := require_login()): return redirect_response
    
    # Admin yetkisi kontrolü
    if session.get('user', {}).get('role') != 'admin':
        flash("You don't have permission to access this page.", 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        data = {
            'name': request.form.get('name'),
            'last_name': request.form.get('last_name'),
            'mobile_phone': request.form.get('mobile_phone'),
            'email': request.form.get('email'),
            'birthday': request.form.get('birthday'),
            'position_id': request.form.get('position_id')
        }
        
        success, message = update_employee_details(employee_id, data)
        
        if success:
            flash(message, 'success')
            return redirect(url_for('admin_employees'))
        else:
            flash(message, 'danger')
    
    employee = get_employee_details(employee_id)
    positions = get_all_positions()
    
    if not employee:
        flash("Employee not found.", 'danger')
        return redirect(url_for('admin_employees'))
    
    return render_template('admin_edit_employee.html', employee=employee, positions=positions)


@app.route('/admin/users/add', methods=['GET', 'POST'])
def admin_add_user():
    if (redirect_response := require_login()): return redirect_response
    
    # Admin yetkisi kontrolü
    if session.get('user', {}).get('role') != 'admin':
        flash("You don't have permission to access this page.", 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        data = {
            'full_name': request.form.get('full_name'),
            'email': request.form.get('email'),
            'password': request.form.get('password'),
            'user_role': request.form.get('user_role'),
            'is_active': request.form.get('is_active') == 'on'
        }
        
        success, message = create_system_user(data)
        
        if success:
            flash(message, 'success')
            return redirect(url_for('admin_users'))
        else:
            flash(message, 'danger')
    
    return render_template('admin_add_user.html')


@app.route('/salary')
def salary():
    if (redirect_response := require_login()): return redirect_response
    
    # Sample salary data - in real implementation, fetch from database
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


@app.route('/logout')
def logout():
    session.pop('user', None)
    flash("Successfully logged out.", 'success')
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)