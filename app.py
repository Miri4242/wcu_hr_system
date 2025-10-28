from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response, jsonify
import psycopg2
from datetime import datetime, date, timedelta
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
        _, salt, stored_hash = stored_password.split('$')
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
    today = datetime.now().date()
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

def get_employee_list():
    """Fetches essential details and positions for all employees (excluding Students and Visitors)."""
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
                           p.photo_path,
                           pp.name       AS position_name,
                           p.create_time AS hire_date
                    FROM public.pers_person p
                             LEFT JOIN public.pers_position pp ON p.position_id = pp.id
                    WHERE (pp.name IS NULL
                       OR (pp.name NOT ILIKE 'STUDENT' AND pp.name NOT ILIKE 'VISITOR')) -- Student ve Visitor Filtresi
                    ORDER BY p.last_name, p.name;
                    """)

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
        return employees
    except psycopg2.Error as e:
        print(f"🚨 Employee List Fetch Error: {e}")
        return []
    finally:
        if cur: cur.close()
        if conn: conn.close()

def get_employee_details(employee_id):
    """Fetches all details for a specific employee ID (excluding Students and Visitors)."""
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
                           p.photo_path,
                           pp.name       AS position_name,
                           p.position_id,
                           p.create_time AS hire_date
                    FROM public.pers_person p
                             LEFT JOIN public.pers_position pp ON p.position_id = pp.id
                    WHERE (pp.name IS NULL OR (pp.name NOT ILIKE 'student' AND pp.name NOT ILIKE 'visitor')) -- Student ve Visitor Filtresi
                      AND p.id = %s;
                    """, (employee_id,))

        row = cur.fetchone()

        if row:
            try:
                photo_path = row[6] if row[6] else url_for('static', filename='images/default_avatar.png')
            except RuntimeError:
                photo_path = row[6] if row[6] else '/static/images/default_avatar.png'

            return {
                'id': row[0],
                'name': row[1],
                'last_name': row[2],
                'mobile_phone': row[3] or '',
                'email': row[4] or '',
                'birthday_form': row[5].strftime('%Y-%m-%d') if row[5] else '',
                'birthday_display': row[5].strftime('%d.%m.%Y') if row[5] else 'N/A',
                'photo_path': photo_path,
                'position_name': row[7] or 'Undefined',
                'position_id': row[8],
                'hire_date': row[9].strftime('%d.%m.%Y') if row[9] else 'N/A'
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

    # Check if all transactions are from today
    today = datetime.now().date()
    transaction_dates = set(t['time'].date() for t in transactions)
    is_today = today in transaction_dates

    first_in_time = None
    last_out_time = None
    current_time = datetime.now()

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

    # Check if this is an invalid day (last event is IN but not today)
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
        'total_inside_seconds': total_inside_seconds if not is_invalid_day else None,
        'total_outside_seconds': total_outside_seconds if not is_invalid_day else None,
        'total_span_seconds': total_span_seconds if not is_invalid_day else None,
        'is_currently_inside': is_currently_inside,
        'current_time_used': current_time if is_currently_inside else None,
        'is_invalid_day': is_invalid_day,
        'is_today': is_today
    }

# --------------------------------------------------------------------------------------
# --- HOURS TRACKED AND ATTENDANCE FUNCTIONS ---
# --------------------------------------------------------------------------------------

def get_employee_list_for_dropdown():
    """Returns employee full name and a normalized key for dropdowns (excluding Students and Visitors)."""
    conn = get_db_connection()
    if conn is None: return []

    cur = conn.cursor()
    try:
        cur.execute("""
                    SELECT p.name, p.last_name
                    FROM public.pers_person p
                             LEFT JOIN public.pers_position pp ON p.position_id = pp.id
                    WHERE pp.name IS NULL
                       OR (pp.name NOT ILIKE 'STUDENT' AND pp.name NOT ILIKE 'VISITOR') -- Student ve Visitor Filtresi
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


def get_employee_logs(person_key=None, days=365):
    """
    Calculates the daily summary of time spent inside/outside for the last X days
    (all employees if person_key is None).
    """
    conn = get_db_connection()
    if conn is None: return []

    cur = conn.cursor()
    start_date = datetime.now() - timedelta(days=days)

    daily_transactions = defaultdict(list)
    final_logs = []

    try:
        # 1. Fetch transaction logs (Filtered by date)
        cur.execute("""
                    SELECT t.name, t.last_name, t.create_time, t.reader_name
                    FROM public.acc_transaction t
                             INNER JOIN public.pers_person p ON t.name = p.name AND t.last_name = p.last_name
                             LEFT JOIN public.pers_position pp ON p.position_id = pp.id
                    WHERE t.create_time >= %s
                      AND (pp.name IS NULL OR (pp.name NOT ILIKE 'student' AND pp.name NOT ILIKE 'visitor')) -- Student ve Visitor Filtresi
                    ORDER BY t.create_time;
                    """, (start_date,))
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

            # YENİ IN/OUT TESPİT ALGORİTMASI - Building A-1 pattern'ine göre
            direction_type = None
            if reader_name:
                # Reader name'i lowercase'e çevir
                reader_lower = reader_name.lower()

                # Building pattern'ini kontrol et
                if 'building' in reader_lower:
                    # Reader numarasını çıkar (1, 2, 3, 4 gibi)
                    import re
                    numbers = re.findall(r'\d+', reader_name)
                    if numbers:
                        reader_number = int(numbers[0])

                        # 1 ve 2 numaralı reader'lar IN, 3 ve 4 numaralı reader'lar OUT
                        if reader_number in [1, 2]:
                            direction_type = 'in'
                        elif reader_number in [3, 4]:
                            direction_type = 'out'

            if not direction_type:
                continue  # Direction tespit edilemezse atla

            # Key: (Log Date, Normalized Name Surname)
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

            # Status calculation based on inside time
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
                # For invalid days (last event IN but not today), show N/A for all time fields
                first_in_display = "N/A"
                last_out_display = "N/A"
                inside_time_display = "N/A"
                outside_time_display = "N/A"
                total_span_display = "N/A"
            else:
                # For valid days
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
            today = datetime.now().date()
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
            WHERE (pp.name IS NULL OR (pp.name NOT ILIKE 'STUDENT' AND pp.name NOT ILIKE 'VISITOR'))
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
        # Filter for non-student and non-visitor transactions.
        cur.execute("""
                    SELECT t.name, t.last_name, t.create_time, t.reader_name
                    FROM public.acc_transaction t
                             INNER JOIN public.pers_person p ON t.name = p.name AND t.last_name = p.last_name
                             LEFT JOIN public.pers_position pp ON p.position_id = pp.id
                    WHERE t.create_time BETWEEN %s AND %s
                      AND (pp.name IS NULL OR (pp.name NOT ILIKE 'student' AND pp.name NOT ILIKE 'visitor')) -- Student ve Visitor Filtresi
                    ORDER BY t.create_time;
                    """, (start_dt, end_dt))

        raw_transactions = cur.fetchall()

        daily_transactions = defaultdict(list)
        for t_name, t_last_name, create_time, reader_name in raw_transactions:
            if create_time is None or not t_name or not t_last_name: continue

            # Filter by the exact person_key here (Python filtering is safer)
            t_key = normalize_name(t_name) + normalize_name(t_last_name)
            if t_key != person_key:
                continue

            log_date = create_time.date()

            # YENİ IN/OUT TESPİT ALGORİTMASI - Building A-1 pattern'ine göre
            direction_type = None
            if reader_name:
                reader_lower = reader_name.lower()

                if 'building' in reader_lower:
                    import re
                    numbers = re.findall(r'\d+', reader_name)
                    if numbers:
                        reader_number = int(numbers[0])

                        if reader_number in [1, 2]:
                            direction_type = 'in'
                        elif reader_number in [3, 4]:
                            direction_type = 'out'

            if direction_type:
                daily_transactions[log_date].append({'time': create_time, 'direction': direction_type})

        # Calculate working times and status for each day with logs
        for log_date, transactions in daily_transactions.items():
            # Skip weekend calculation if log date is a Saturday (5) or Sunday (6)
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

        # Process all days from start_date up to end_date
        while current_day <= end_date:
            day_data = daily_data.get(current_day, {'total_inside_seconds': 0,
                                                    'status_code': 'D'})

            # Only include weekdays (Monday=0 to Friday=4)
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
        today = date.today()
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
        # 1. Fetch all employees (FILTERED: No Students/Visitors + Apply Search)
        if search_term:
            cur.execute("""
                        SELECT p.id, p.name, p.last_name, pp.name AS position_name
                        FROM public.pers_person p
                                 LEFT JOIN public.pers_position pp ON p.position_id = pp.id
                        WHERE (pp.name IS NULL OR (pp.name NOT ILIKE 'STUDENT' AND pp.name NOT ILIKE 'VISITOR')) -- Student ve Visitor Filtresi
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
                           OR (pp.name NOT ILIKE 'STUDENT' AND pp.name NOT ILIKE 'VISITOR') -- Student ve Visitor Filtresi
                        ORDER BY p.last_name, p.name
                        """)

        person_data = cur.fetchall()

        for id_val, name, last_name, position_name in person_data:
            key = normalize_name(name) + normalize_name(last_name)
            full_name = f"{name} {last_name}"
            employee_list.append(
                {'key': key, 'id': id_val, 'name': name, 'last_name': last_name, 'full_name': full_name})

        # 2. Fetch all movements within the date range (Only for Non-Students/Non-Visitors)
        cur.execute("""
                    SELECT t.name, t.last_name, t.create_time, t.reader_name
                    FROM public.acc_transaction t
                             INNER JOIN public.pers_person p ON t.name = p.name AND t.last_name = p.last_name
                             LEFT JOIN public.pers_position pp ON p.position_id = pp.id
                    WHERE t.create_time >= %s
                      AND t.create_time <= %s
                      AND (pp.name IS NULL OR (pp.name NOT ILIKE 'student' AND pp.name NOT ILIKE 'visitor')) -- Student ve Visitor Filtresi
                    ORDER BY t.create_time;
                    """, (datetime.combine(start_date, datetime.min.time()),
                          datetime.combine(end_date, datetime.max.time())))

        raw_transactions = cur.fetchall()

        # 3. Process transactions and Grouping
        for t_name, t_last_name, create_time, reader_name in raw_transactions:
            if create_time is None or not t_name or not t_last_name: continue

            log_date = create_time.date()

            # YENİ IN/OUT TESPİT ALGORİTMASI - Building A-1 pattern'ine göre
            direction_type = None
            if reader_name:
                # Reader name'i lowercase'e çevir
                reader_lower = reader_name.lower()

                # Building pattern'ini kontrol et
                if 'building' in reader_lower:
                    # Reader numarasını çıkar (1, 2, 3, 4 gibi)
                    import re
                    numbers = re.findall(r'\d+', reader_name)
                    if numbers:
                        reader_number = int(numbers[0])

                        # 1 ve 2 numaralı reader'lar IN, 3 ve 4 numaralı reader'lar OUT
                        if reader_number in [1, 2]:
                            direction_type = 'in'
                        elif reader_number in [3, 4]:
                            direction_type = 'out'

            if direction_type:
                t_key = normalize_name(t_name) + normalize_name(t_last_name)
                key = (log_date, t_key)
                daily_transactions[key].append({'time': create_time, 'direction': direction_type})

        # 4. Determine Daily Status (for employees in employee_list)
        for (log_date, person_key), transactions in daily_transactions.items():
            # Check if this log belongs to an employee in the list
            if not any(emp['key'] == person_key for emp in employee_list):
                continue

            # Use the core calculation function
            times = calculate_times_from_transactions(transactions)
            total_inside_seconds = times['total_inside_seconds']

            # Assign Status Code (T: Full Day, E: Short Hours, D: Absent, N: No Log)
            day_number = log_date.day
            if total_inside_seconds >= EIGHT_HOURS_SECONDS:
                status_code = 'T'  # Full Day (GREEN)
            elif total_inside_seconds > 0:
                status_code = 'E'  # Short Hours/Partial Day (YELLOW)
            else:
                status_code = 'D'  # Absent (RED)

            employee_daily_status[person_key][day_number] = status_code

        # 5. Prepare Results for HTML
        day_headers = list(range(1, days_in_month + 1))

        final_logs = []
        for emp in employee_list:
            row = {
                'id': emp['id'],
                'name': emp['full_name'],
                'days': []
            }
            for day in day_headers:
                status = employee_daily_status[emp['key']].get(day, 'N')  # N: Not Logged (RED/NO LOG)
                row['days'].append(status)

            final_logs.append(row)

        # 6. Apply Pagination
        total_items = len(final_logs)
        total_pages = (total_items + per_page - 1) // per_page

        # Ensure page number is valid
        if page < 1: page = 1
        if page > total_pages and total_pages > 0: page = total_pages

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
        if cur: cur.close()
        if conn: conn.close()

def get_dashboard_data():
    conn = get_db_connection()
    data = {'total_employees': 0, 'total_departments': 0, 'total_transactions': 0,
            'new_employees_this_month': 0, 'today_birthdays': [],
            'present_employees_count': 0,
            'attendance_percentage': 0.0}

    if conn is None: return data

    cur = conn.cursor()
    try:
        # 1. Total Employees (Non-Student, Non-Visitor)
        cur.execute("""SELECT COUNT(*)
                       FROM public.pers_person p
                                LEFT JOIN public.pers_position pp ON p.position_id = pp.id
                       WHERE pp.name IS NULL
                          OR (pp.name NOT ILIKE 'STUDENT' AND pp.name NOT ILIKE 'VISITOR')""")  # Student ve Visitor Filtresi
        data['total_employees'] = cur.fetchone()[0]

        # 2. Total Departments
        cur.execute("SELECT COUNT(*) FROM public.auth_department")
        data['total_departments'] = cur.fetchone()[0]

        # 3. Today's Total Transactions (Non-Student, Non-Visitor)
        today_date = date.today()
        cur.execute("""SELECT COUNT(t.*)
                       FROM public.acc_transaction t
                                INNER JOIN public.pers_person p ON t.name = p.name AND t.last_name = p.last_name
                                LEFT JOIN public.pers_position pp ON p.position_id = pp.id
                       WHERE DATE (t.create_time) = %s AND (pp.name IS NULL OR (pp.name NOT ILIKE 'student' AND pp.name NOT ILIKE 'visitor'))""",  # Student ve Visitor Filtresi
                    (today_date,))
        data['total_transactions'] = cur.fetchone()[0]

        # 4. New Employees This Month (Non-Student, Non-Visitor)
        cur.execute("""SELECT COUNT(p.*)
                       FROM public.pers_person p
                                LEFT JOIN public.pers_position pp ON p.position_id = pp.id
                       WHERE date_trunc('month', p.create_time) = date_trunc('month', NOW())
                         AND (pp.name IS NULL OR (pp.name NOT ILIKE 'student' AND pp.name NOT ILIKE 'visitor'))""")  # Student ve Visitor Filtresi
        data['new_employees_this_month'] = cur.fetchone()[0]

        # 5. Employees Present Today (Non-Student, Non-Visitor)
        cur.execute("""
                    SELECT COUNT(DISTINCT (t.name, t.last_name))
                    FROM public.acc_transaction t
                             INNER JOIN public.pers_person p ON t.name = p.name AND t.last_name = p.last_name
                             LEFT JOIN public.pers_position pp ON p.position_id = pp.id
                    WHERE DATE (t.create_time) = %s
                      AND t.reader_name ILIKE '%%-in%%'
                      AND (pp.name IS NULL
                       OR (pp.name NOT ILIKE 'student' AND pp.name NOT ILIKE 'visitor'))
                    """, (today_date,))  # Student ve Visitor Filtresi
        data['present_employees_count'] = cur.fetchone()[0]

        # Attendance Percentage Calculation
        total = data['total_employees']
        present = data['present_employees_count']

        if total > 0:
            percentage = (present / total) * 100
            data['attendance_percentage'] = round(percentage, 2)

        # 6. Birthdays Today (Non-Student, Non-Visitor)
        today_m_d = datetime.now().strftime('%m-%d')
        cur.execute("""
                    SELECT p.id, p.name, p.last_name, p.birthday
                    FROM public.pers_person p
                             LEFT JOIN public.pers_position pp ON p.position_id = pp.id
                    WHERE TO_CHAR(p.birthday, 'MM-DD') = %s
                      AND (pp.name IS NULL OR (pp.name NOT ILIKE 'student' AND pp.name NOT ILIKE 'visitor')) -- Student ve Visitor Filtresi
                    ORDER BY p.last_name, p.name;
                    """, (today_m_d,))

        today_birthdays_raw = cur.fetchall()
        birthday_list = []
        for id_val, name, last_name_val, birthday_date in today_birthdays_raw:
            birth_date_str = birthday_date.strftime('%d.%m.%Y') if isinstance(birthday_date,
                                                                              (datetime, date)) else 'N/A'
            birthday_list.append(
                {'person_id': id_val, 'name': name, 'surname': last_name_val, 'birth_date_str': birth_date_str})
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

        if user and user['password'] == password:
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

    logs_data = get_employee_logs(person_key=person_key, days=365)

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
        filename = f"log_export_{person_key}.csv"
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

    if request.method == 'POST':
        selected_person_key = request.form.get('person_key')
    else:
        selected_person_key = request.args.get('person_key') or ''

    # Get selected employee name
    if selected_person_key:
        selected_employee = next((emp for emp in employee_list if emp['key'] == selected_person_key), None)
        if selected_employee:
            selected_employee_name = selected_employee['name']
    else:
        selected_employee_name = "All Employees"

    logs_data = get_employee_logs(person_key=selected_person_key, days=365)

    return render_template(
        'employee_logs.html',
        logs=logs_data,
        employees=employee_list,
        selected_person_key=selected_person_key,
        selected_employee_name=selected_employee_name
    )

@app.route('/attendance', methods=['GET', 'POST'])
def attendance():
    if (redirect_response := require_login()): return redirect_response

    today = date.today()
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
                    WHERE (pp.name IS NULL OR (pp.name NOT ILIKE 'student' AND pp.name NOT ILIKE 'visitor')) -- Student ve Visitor Filtresi
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

    today = date.today()
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
        end_date = date.today()
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

@app.route('/salary')
def salary():
    if (redirect_response := require_login()): return redirect_response
    return render_template('salary.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash("Successfully logged out.", 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)