from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response
import psycopg2
from datetime import datetime, date, timedelta
from collections import defaultdict
from io import StringIO
import csv

app = Flask(__name__)
# Change your secret key
app.config['SECRET_KEY'] = 'super-secret-key'
app.secret_key = app.config['SECRET_KEY']  # Session için secret_key'i de atayın

# PostgreSQL Connection Settings
DB_CONFIG = {
    # 🚨 Lütfen Kontrol Edin: Doğru veritabanı bilgilerinizi girin
    'dbname': 'tuniket.db',
    'user': 'postgres',
    'password': '7963686',  # Şifrenizi kontrol edin!
    'host': '127.0.0.1',
    'port': '5432'
}


def get_db_connection():
    """Tries to connect to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except psycopg2.Error as e:
        print(f"🚨 Database connection error: {e}")
        return None


# --- HELPER FUNCTIONS ---

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


# --------------------------------------------------------------------------------------
# --- ÇALIŞAN YÖNETİMİ FONKSİYONLARI (EMPLOYEES) ---
# --------------------------------------------------------------------------------------

def get_employee_list():
    """
    pers_person ve pers_position tablolarını birleştirerek tüm çalışanların
    temel bilgilerini ve pozisyonlarını çeker.
    """
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
                             LEFT JOIN
                         public.pers_position pp ON p.position_id = pp.id
                    ORDER BY p.last_name, p.name;
                    """)

        employees_raw = cur.fetchall()
        employees = []

        for row in employees_raw:
            # photo_path için varsayılan değeri ayarlamak için url_for kullanın
            # (Bu kısım, statik dosyalara erişim için Flask bağlamını gerektirir)
            try:
                photo_path = row[6] if row[6] else url_for('static', filename='images/default_avatar.png')
            except RuntimeError:
                # Eğer kod uygulama bağlamı dışında çalışıyorsa (örn: test)
                photo_path = row[6] if row[6] else '/static/images/default_avatar.png'

            employees.append({
                'id': row[0],
                'name': row[1],
                'last_name': row[2],
                'mobile_phone': row[3] or 'N/A',
                'email': row[4] or 'N/A',
                'birthday': row[5].strftime('%d.%m.%Y') if row[5] else 'N/A',
                'photo_path': photo_path,
                'position': row[7] or 'Undefined',  # Çeviri: Belirtilmemiş -> Undefined
                'hire_date': row[8].strftime('%d.%m.%Y') if row[8] else 'N/A'
            })
        return employees
    except psycopg2.Error as e:
        print(f"🚨 Çalışan Listesi Çekme Hatası: {e}")
        return []
    finally:
        if cur: cur.close()
        if conn: conn.close()


def get_employee_details(employee_id):
    """Belirtilen ID'ye sahip çalışanın tüm detaylarını çeker."""
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
                             LEFT JOIN
                         public.pers_position pp ON p.position_id = pp.id
                    WHERE p.id = %s;
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
                'position_name': row[7] or 'Undefined',  # Çeviri: Belirtilmemiş -> Undefined
                'position_id': row[8],
                'hire_date': row[9].strftime('%d.%m.%Y') if row[9] else 'N/A'
            }
        return None
    except psycopg2.Error as e:
        print(f"🚨 Çalışan Detayları Çekme Hatası: {e}")
        return None
    finally:
        if cur: cur.close()
        if conn: conn.close()


def get_all_positions():
    """Tüm pozisyonları ID ve İsim olarak çeker (Dropdown için)."""
    conn = get_db_connection()
    if conn is None: return []
    cur = conn.cursor()
    try:
        cur.execute("SELECT id, name FROM public.pers_position ORDER BY name;")
        return [{'id': row[0], 'name': row[1]} for row in cur.fetchall()]
    except psycopg2.Error as e:
        print(f"🚨 Pozisyon Listesi Çekme Hatası: {e}")
        return []
    finally:
        if cur: cur.close()
        if conn: conn.close()


def update_employee_details(employee_id, data):
    """Çalışan bilgilerini günceller."""
    conn = get_db_connection()
    if conn is None:
        return False, "Database connection error."  # Çeviri: Veritabanı bağlantı hatası.

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
        return True, "Employee details successfully updated."  # Çeviri: Çalışan bilgileri başarıyla güncellendi.
    except psycopg2.Error as e:
        conn.rollback()
        print(f"🚨 Çalışan Güncelleme Hatası: {e}")
        return False, f"Update error: {e}"  # Çeviri: Güncelleme hatası
    finally:
        if cur: cur.close()
        if conn: conn.close()


# --------------------------------------------------------------------------------------
# --- SÜRE VE LOG HESAPLAMA ÇEKİRDEK MANTIĞI ---
# --------------------------------------------------------------------------------------

def calculate_times_from_transactions(transactions):
    """
    Verilen log listesini işler ve içeride/dışarıda geçirilen süreyi hesaplar.
    """
    transactions.sort(key=lambda x: x['time'])

    first_in_time = None
    last_out_time = None

    # İlk giriş ve son çıkışı bul
    in_logs = [t['time'] for t in transactions if t['direction'] == 'in']
    out_logs = [t['time'] for t in transactions if t['direction'] == 'out']

    if in_logs:
        first_in_time = min(in_logs)
    if out_logs:
        last_out_time = max(out_logs)

    total_inside_seconds = 0

    # İlk giriş ve son çıkış arasındaki toplam zaman dilimi
    total_span_seconds = 0
    if first_in_time and last_out_time and last_out_time > first_in_time:
        total_span_seconds = (last_out_time - first_in_time).total_seconds()

    is_inside = False
    last_event_time = None

    # Detaylı iç süreyi hesapla
    for t in transactions:
        current_time = t['time']
        current_direction = t['direction']

        # Eğer ilk girişten önce bir hareket varsa dikkate alma
        if first_in_time and current_time < first_in_time:
            continue

        if last_event_time is None:
            if current_direction == 'in':
                is_inside = True
            last_event_time = current_time
            continue

        time_diff_seconds = (current_time - last_event_time).total_seconds()

        if time_diff_seconds < 0:
            last_event_time = current_time
            continue

        if is_inside:
            total_inside_seconds += time_diff_seconds
            if current_direction == 'out':
                is_inside = False
        else:
            if current_direction == 'in':
                is_inside = True

        last_event_time = current_time

    # Dışarıda geçirilen süre: (İlk giriş-Son çıkış arasındaki toplam süre) - İçeride geçirilen süre
    total_outside_seconds = 0
    if total_span_seconds > 0:
        total_outside_seconds = total_span_seconds - total_inside_seconds
        if total_outside_seconds < 0: total_outside_seconds = 0

    return {
        'first_in': first_in_time,
        'last_out': last_out_time,
        'total_inside_seconds': total_inside_seconds,
        'total_outside_seconds': total_outside_seconds
    }


# --------------------------------------------------------------------------------------
# --- EMPLOYEE LOGS VE HOURS TRACKED HELPER'LARI ---
# --------------------------------------------------------------------------------------

def get_employee_list_for_dropdown():
    """Dropdown için çalışanın adını ve soyadını birleştirip key olarak döndürür."""
    conn = get_db_connection()
    if conn is None: return []

    cur = conn.cursor()
    try:
        cur.execute("SELECT name, last_name FROM public.pers_person ORDER BY last_name, name")
        employees = []
        for name, last_name in cur.fetchall():
            full_name = f"{name} {last_name}"
            key = normalize_name(name) + normalize_name(last_name)
            employees.append({'key': key, 'name': full_name})

        return employees
    except psycopg2.Error as e:
        print(f"🚨 Çalışan Listesi Sorgu Hatası: {e}")
        return []
    finally:
        if cur: cur.close()
        if conn: conn.close()


def get_employee_logs(person_key=None, days=365):
    """
    Verilen person_key'e göre (person_key=None ise tüm çalışanlar) son X günün
    günlük içeride/dışarıda geçirilen süre özetini hesaplar.
    """
    conn = get_db_connection()
    if conn is None: return []

    cur = conn.cursor()
    start_date = datetime.now() - timedelta(days=days)

    daily_transactions = defaultdict(list)
    final_logs = []

    try:
        # 1. Fetch transaction logs (Tarih filtreli)
        cur.execute("""
                    SELECT name, last_name, create_time, reader_name
                    FROM public.acc_transaction
                    WHERE create_time >= %s
                    ORDER BY create_time;
                    """, (start_date,))
        raw_transactions = cur.fetchall()

        # 2. Process transactions and Grouping (Person Name + Date)
        for t_name, t_last_name, create_time, reader_name in raw_transactions:
            if create_time is None or not t_name or not t_last_name: continue

            # Key oluştur ve filtrele
            t_key = normalize_name(t_name) + normalize_name(t_last_name)
            if person_key and t_key != person_key:
                continue

            log_date = create_time.date()

            # Direction detection
            direction_lower = (reader_name or '').lower()
            direction_type = None
            if '-in' in direction_lower and '-out' not in direction_lower:
                direction_type = 'in'
            elif '-out' in direction_lower and '-in' not in direction_lower:
                direction_type = 'out'

            if not direction_type:
                continue

            # Key: (Log Tarihi, Normalize İsim Soyisim)
            key = (log_date, t_key)
            daily_transactions[key].append({
                'name': t_name, 'last_name': t_last_name,
                'time': create_time, 'direction': direction_type
            })

        # 3. Calculate Time for each day/person
        for (log_date, person_key), transactions in daily_transactions.items():
            # Hesaplama çekirdek fonksiyonunu kullan
            times = calculate_times_from_transactions(transactions)

            final_logs.append({
                'date': log_date.strftime('%d.%m.%Y'),
                'name': transactions[0]['name'],
                'last_name': transactions[0]['last_name'],
                'first_in': times['first_in'].strftime('%H:%M:%S') if times['first_in'] else 'N/A',
                'last_out': times['last_out'].strftime('%H:%M:%S') if times['last_out'] else 'N/A',
                'inside_time': format_seconds(times['total_inside_seconds']),
                'outside_time': format_seconds(times['total_outside_seconds']),
                'total_inside_seconds': times['total_inside_seconds']  # Sıralama için tutulur
            })

        # En yeniden en eskiye sırala (Tarih, sonra içeride geçirilen süre)
        final_logs.sort(key=lambda x: (datetime.strptime(x['date'], '%d.%m.%Y'), x['total_inside_seconds']),
                        reverse=True)
        return final_logs

    except Exception as e:
        print(f"🚨 Employee Logs Processing Error: {e}")
        return []
    finally:
        if cur: cur.close()
        if conn: conn.close()


def get_employee_logs_monthly(selected_month, selected_year):
    # (Aylık yoklama verisini çeken fonksiyon)
    conn = get_db_connection()
    if conn is None: return {'headers': [], 'logs': [], 'current_month': selected_month, 'current_year': selected_year}

    cur = conn.cursor()
    EIGHT_HOURS_SECONDS = 28800

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

    try:
        # 1. Fetch all employees (Sadece dropdown/görüntüleme için)
        cur.execute("SELECT id, name, last_name FROM public.pers_person ORDER BY last_name, name")
        person_data = cur.fetchall()

        employee_list = []
        for id_val, name, last_name in person_data:
            key = normalize_name(name) + normalize_name(last_name)
            employee_list.append({'key': key, 'id': id_val, 'name': name, 'last_name': last_name})

        # 2. Fetch all movements within the date range
        cur.execute("""
                    SELECT name, last_name, create_time, reader_name
                    FROM public.acc_transaction
                    WHERE create_time >= %s
                      AND create_time <= %s
                    ORDER BY create_time;
                    """, (datetime.combine(start_date, datetime.min.time()),
                          datetime.combine(end_date, datetime.max.time())))

        raw_transactions = cur.fetchall()

        # 3. Process transactions and Grouping
        for t_name, t_last_name, create_time, reader_name in raw_transactions:
            if create_time is None or not t_name or not t_last_name: continue

            log_date = create_time.date()

            direction_lower = (reader_name or '').lower()
            direction_type = None
            if '-in' in direction_lower and '-out' not in direction_lower:
                direction_type = 'in'
            elif '-out' in direction_lower and '-in' not in direction_lower:
                direction_type = 'out'

            if direction_type:
                t_key = normalize_name(t_name) + normalize_name(t_last_name)
                key = (log_date, t_key)
                daily_transactions[key].append({'time': create_time, 'direction': direction_type})

        # 4. Determine Daily Status
        for (log_date, person_key), transactions in daily_transactions.items():

            # Use the core calculation function
            times = calculate_times_from_transactions(transactions)
            total_inside_seconds = times['total_inside_seconds']

            # Assign Status Code
            day_number = log_date.day
            if total_inside_seconds >= EIGHT_HOURS_SECONDS:
                status_code = 'F'  # Full Day
            elif total_inside_seconds > 0:
                status_code = 'S'  # Short Hours
            else:
                status_code = 'A'  # Absent

            employee_daily_status[person_key][day_number] = status_code

        # 5. Prepare Results for HTML
        day_headers = list(range(1, days_in_month + 1))

        final_logs = []
        for emp in employee_list:
            row = {
                'id': emp['id'],
                'name': f"{emp['name']} {emp['last_name']}",
                'days': []
            }
            for day in day_headers:
                status = employee_daily_status[emp['key']].get(day, 'N')  # N: Not Logged
                row['days'].append(status)

            final_logs.append(row)

        return {
            'headers': day_headers,
            'logs': final_logs,
            'current_month': selected_month,
            'current_year': selected_year,
            'month_name': start_date.strftime('%B')
        }

    except Exception as e:
        print(f"🚨 Monthly Attendance Processing Error: {e}")
        return {'headers': [], 'logs': [], 'current_month': selected_month, 'current_year': selected_year,
                'month_name': 'Error'}
    finally:
        if cur: cur.close()
        if conn: conn.close()


def get_tracked_hours(person_key, period):
    """
    Calculates total worked time (time spent inside) and daily statuses
    for a specific employee on a weekly/monthly basis.
    """
    conn = get_db_connection()
    if conn is None: return {'logs': [], 'total_time_str': '00:00:00'}

    cur = conn.cursor()

    FULL_DAY_SECONDS = 28800  # 8 hours
    today = date.today()

    # Determine Date Range
    if period == 'week':
        # Start of the current week (Monday)
        start_date = today - timedelta(days=today.weekday())
    elif period == 'month':
        # Start of the current month
        start_date = date(today.year, today.month, 1)
    else:
        # Default: Last 7 days
        start_date = today - timedelta(days=7)

    daily_data = defaultdict(lambda: {'total_inside_seconds': 0, 'status_code': 'N'})

    try:
        # Fetch all logs (Filtered by date)
        cur.execute("""
                    SELECT name, last_name, create_time, reader_name
                    FROM public.acc_transaction
                    WHERE DATE (create_time) >= %s
                    ORDER BY create_time;
                    """, (start_date,))

        raw_transactions = cur.fetchall()

        # Filter and group movements only for the selected person
        daily_transactions = defaultdict(list)
        for t_name, t_last_name, create_time, reader_name in raw_transactions:
            if create_time is None or not t_name or not t_last_name: continue

            t_key = normalize_name(t_name) + normalize_name(t_last_name)

            if t_key != person_key:
                continue

            log_date = create_time.date()
            direction_lower = (reader_name or '').lower()
            direction_type = None
            if '-in' in direction_lower and '-out' not in direction_lower:
                direction_type = 'in'
            elif '-out' in direction_lower and '-in' not in direction_lower:
                direction_type = 'out'

            if direction_type:
                daily_transactions[log_date].append({'time': create_time, 'direction': direction_type})

        # Calculate working times
        total_tracked_seconds = 0
        for log_date, transactions in daily_transactions.items():

            # Use the core calculation function
            times = calculate_times_from_transactions(transactions)
            total_inside_seconds = times['total_inside_seconds']

            # Assign Status Code (F: Full, S: Short, A: Absent)
            if total_inside_seconds >= FULL_DAY_SECONDS:
                status_code = 'F'
            elif total_inside_seconds > 0:
                status_code = 'S'
            else:
                status_code = 'A'

            daily_data[log_date]['total_inside_seconds'] = total_inside_seconds
            daily_data[log_date]['status_code'] = status_code

        # Prepare Results
        tracked_logs = []
        current_day = start_date

        # Process all days from start_date up to today
        while current_day <= today:
            day_data = daily_data.get(current_day, {'total_inside_seconds': 0, 'status_code': 'N'})

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
# --- DASHBOARD VERİ ÇEKME ---
# --------------------------------------------------------------------------------------

def get_dashboard_data():
    conn = get_db_connection()
    data = {'total_employees': 0, 'total_departments': 0, 'total_transactions': 0,
            'new_employees_this_month': 0, 'today_birthdays': [],
            'present_employees_count': 0,
            'attendance_percentage': 0.0}

    if conn is None: return data

    cur = conn.cursor()
    try:
        # 1. Total Employees
        cur.execute("SELECT COUNT(*) FROM public.pers_person")
        data['total_employees'] = cur.fetchone()[0]

        # 2. Total Departments
        cur.execute("SELECT COUNT(*) FROM public.pers_position")
        data['total_departments'] = cur.fetchone()[0]

        # 3. Today's Total Transactions
        today_date = date.today()
        cur.execute("""SELECT COUNT(*)
                       FROM public.acc_transaction
                       WHERE DATE (create_time) = %s""", (today_date,))
        data['total_transactions'] = cur.fetchone()[0]

        # 4. New Employees This Month
        cur.execute("""SELECT COUNT(*)
                       FROM public.pers_person
                       WHERE date_trunc('month', create_time) = date_trunc('month', NOW())""")
        data['new_employees_this_month'] = cur.fetchone()[0]

        # 5. Employees Present Today
        cur.execute("""
                    SELECT COUNT(DISTINCT (name, last_name))
                    FROM public.acc_transaction
                    WHERE DATE (create_time) = %s AND reader_name ILIKE '%%-in%%'
                    """, (today_date,))
        data['present_employees_count'] = cur.fetchone()[0]

        # Attendance Percentage Calculation
        total = data['total_employees']
        present = data['present_employees_count']

        if total > 0:
            percentage = (present / total) * 100
            data['attendance_percentage'] = round(percentage, 2)

        # 6. Birthdays Today
        today_m_d = datetime.now().strftime('%m-%d')
        cur.execute("""
                    SELECT id, name, last_name, birthday
                    FROM public.pers_person
                    WHERE TO_CHAR(birthday, 'MM-DD') = %s
                    ORDER BY last_name, name;
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
# --- FLASK ROUTES (ROTALAR) ---
# ***************************************************************


@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    # Yönlendirme döngüsü hatasını önlemek için güvenli kontrol:
    # Kullanıcı ZATEN giriş yaptıysa, onu doğrudan dashboard'a yönlendir.
    if 'user' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username == 'admin' and password == '1234':
            session['user'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))

        flash('Invalid Username or Password!', 'danger')
    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    if (redirect_response := require_login()): return redirect_response
    dashboard_data = get_dashboard_data()
    return render_template('dashboard.html', data=dashboard_data)


# ROTA: Çalışanlar Listeleme Sayfası
@app.route('/employees')
def employees():
    if (redirect_response := require_login()): return redirect_response

    employees_list = get_employee_list()

    return render_template(
        'employees.html',
        employees=employees_list
    )


# ROTA: Çalışan Düzenleme Sayfası
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

    # GET veya güncelleme sonrası formu yeniden yüklemek için
    employee = get_employee_details(employee_id)

    if not employee:
        flash("Employee not found.", 'danger')  # Çeviri: Çalışan bulunamadı.
        return redirect(url_for('employees'))

    return render_template(
        'employee_edit.html',
        employee=employee,
        positions=positions
    )


# ROTA 1: EXPORT ÖZELLİĞİ (Çalışan Listesi)
@app.route('/employees/export')
def export_employees():
    if (redirect_response := require_login()): return redirect_response

    employees_list = get_employee_list()

    # 1. StringIO kullanarak hafızada bir CSV dosyası oluştur
    si = StringIO()
    cw = csv.writer(si)

    # 2. Başlık satırını yaz
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

    # 3. Verileri yaz
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

    # 4. Flask yanıtını (Response) hazırla
    response = make_response(output)
    response.headers["Content-Disposition"] = "attachment; filename=employees_export.csv"
    response.headers["Content-type"] = "text/csv"

    return response


# ROTA 2: ÇALIŞMA SÜRESİ ANALİZİ EXPORT ETME
@app.route('/employee_logs/export', methods=['GET'])
def export_employee_logs():
    if (redirect_response := require_login()): return redirect_response

    person_key = request.args.get('person_key', None)

    # Veriyi çekmek için mevcut fonksiyonu kullan (son 365 gün için)
    logs_data = get_employee_logs(person_key=person_key, days=365)

    if not logs_data:
        return make_response("No data found for export.", 404)  # Çeviri: Export edilecek veri bulunamadı.

    si = StringIO()
    cw = csv.writer(si)

    # Başlık satırını oluştur ve yaz
    header = [
        'Date',
        'Employee First Name',
        'Employee Last Name',
        'First In',
        'Last Out',
        'Total INSIDE Time (HH:MM:SS)',
        'Total OUTSIDE Time (HH:MM:SS)',
        'Total INSIDE Time (Seconds)'
    ]
    cw.writerow(header)

    # Verileri yaz
    for log in logs_data:
        cw.writerow([
            log['date'],
            log['name'],
            log['last_name'],
            log['first_in'],
            log['last_out'],
            log['inside_time'],
            log['outside_time'],
            log['total_inside_seconds']
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

    if request.method == 'POST':
        selected_person_key = request.form.get('person_key')
    else:
        # GET metodu için de kontrol
        selected_person_key = request.args.get('person_key') or ''

    logs_data = get_employee_logs(person_key=selected_person_key, days=365)

    selected_employee_name = next((emp['name'] for emp in employee_list if emp['key'] == selected_person_key),
                                  "All Employees")

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

    if request.method == 'POST':
        try:
            selected_month = int(request.form.get('month', today.month))
            selected_year = int(request.form.get('year', today.year))
        except ValueError:
            flash("Invalid month or year selection.")
            pass

    attendance_data = get_employee_logs_monthly(selected_month, selected_year)

    years = list(range(today.year - 2, today.year + 1))

    # İngilizce Ay İsimleri
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
        current_selection={'month': selected_month, 'year': selected_year}
    )


# ROTA 3: EXPORT ÖZELLİĞİ (Aylık Yoklama)
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

    data = get_employee_logs_monthly(selected_month, selected_year)

    if not data or not data.get('logs'):
        return make_response("No monthly attendance data found for export.", 404)

    si = StringIO()
    cw = csv.writer(si)

    month_name = data.get('month_name', 'Month')
    year = data.get('current_year', 'Year')

    # Başlık satırını oluştur ve yaz
    header = ['EMPLOYEE'] + [str(d) for d in data.get('headers', [])]
    cw.writerow(header)

    # Verileri yaz
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

    selected_person_key = request.args.get('person_key') or (employee_list[0]['key'] if employee_list else None)
    selected_period = request.args.get('period') or 'week'

    tracked_data = {'logs': [], 'total_time_str': '00:00:00'}

    if selected_person_key:
        try:
            tracked_data = get_tracked_hours(selected_person_key, selected_period)
        except Exception as e:
            flash(f"Data fetching error: {e}")

    # PERİYOT İSİMLERİ İNGİLİZCE YAPILDI
    periods = [
        ('week', 'Last 7 Work Days'),
        ('month', 'This Month (Work Days)')
    ]

    selected_employee_name = next((emp['name'] for emp in employee_list if emp['key'] == selected_person_key),
                                  "Select Employee")

    return render_template(
        'hours_tracked.html',
        employees=employee_list,
        periods=periods,
        selected_person_key=selected_person_key,
        selected_period=selected_period,
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
    # Flask uygulaması genellikle debug moduyla başlatılır
    app.run(debug=True)