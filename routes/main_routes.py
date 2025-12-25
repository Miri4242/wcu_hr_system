from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response, session
from io import StringIO
import csv
from datetime import date, timedelta, datetime
import calendar

# db_service.py dosyasından tüm gerekli fonksiyonları import ediyoruz
import db_service
from db_service import get_employee_list, get_employee_list_for_dropdown, get_employee_details, \
    get_all_positions, update_employee_details, get_employee_logs, get_employee_logs_monthly, \
    get_dashboard_data, get_tracked_hours_by_dates, get_available_months


# Blueprint'i tanımlıyoruz
main_bp = Blueprint('main', __name__)

# NOT: require_login fonksiyonu, session kullandığı için app.py'de bırakıldı.
# Gerçek projede bu da ayrı bir auth.py dosyasına taşınmalıdır.
# Burada, bu fonksiyonun app.py'de tanımlandığını varsayarak kullanıyoruz.
# Ancak Flask'ta Blueprint kullanırken bu global fonksiyona erişmek zor olduğu için,
# app.py'den bu fonksiyonu import edemeyeceğimizden, şimdilik her rotada tekrar tanımlayalım.
def require_login():
    """Giriş yapılmadıysa login sayfasına yönlendirir."""
    if 'user' not in session:
        flash('You need to log in first.', 'danger')
        return redirect(url_for('login'))
    return None

@main_bp.route('/dashboard')
def dashboard():
    if (redirect_response := require_login()): return redirect_response
    dashboard_data = get_dashboard_data()
    return render_template('dashboard.html', data=dashboard_data)


@main_bp.route('/employees')
def employees():
    if (redirect_response := require_login()): return redirect_response

    employees_list = get_employee_list()

    return render_template(
        'employees.html',
        employees=employees_list
    )


@main_bp.route('/employees/edit/<employee_id>', methods=['GET', 'POST'])
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
            return redirect(url_for('main.employees')) # Blueprint kullandığımız için main.employees
        else:
            flash(message, 'danger')

    employee = get_employee_details(employee_id)

    if not employee:
        flash("Employee not found.", 'danger')
        return redirect(url_for('main.employees'))

    return render_template(
        'employee_edit.html',
        employee=employee,
        positions=positions
    )


@main_bp.route('/employees/export')
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


@main_bp.route('/employee_logs/export', methods=['GET'])
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
        'Total INSIDE Time (Seconds)'
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


@main_bp.route('/employee_logs', methods=['GET', 'POST'])
def employee_logs():
    if (redirect_response := require_login()): return redirect_response

    employee_list = get_employee_list_for_dropdown()
    selected_person_key = None

    if request.method == 'POST':
        selected_person_key = request.form.get('person_key')
    else:
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


@main_bp.route('/attendance', methods=['GET', 'POST'])
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

    # Month names
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


@main_bp.route('/attendance/export', methods=['GET'])
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


@main_bp.route('/hours_tracked', methods=['GET'])
def hours_tracked():
    if (redirect_response := require_login()): return redirect_response

    employee_list = get_employee_list_for_dropdown()

    selected_person_key = request.args.get('person_key') or (employee_list[0]['key'] if employee_list else None)
    selected_period = request.args.get('period', 'last_7_days')

    tracked_data = {'logs': [], 'total_time_str': '00:00:00'}
    today = date.today()
    start_date, end_date = today, today

    # Determine Date Range based on selected_period
    if selected_period == 'last_7_days':
        start_date = today - timedelta(days=6)
        end_date = today
    elif selected_period == 'last_30_days':
        start_date = today - timedelta(days=29)
        end_date = today
    elif selected_period == 'this_month':
        start_date = today.replace(day=1)
        end_date = today
    elif selected_period == 'last_month':
        last_day_last_month = today.replace(day=1) - timedelta(days=1)
        start_date = last_day_last_month.replace(day=1)
        end_date = last_day_last_month

    elif '-' in selected_period:
        # 'YYYY-MM' format (Month selection)
        try:
            year, month = map(int, selected_period.split('-'))

            start_date = date(year, month, 1)

            last_day = calendar.monthrange(year, month)[1]
            end_date = date(year, month, last_day)

            if end_date > today:
                end_date = today

        except ValueError:
            start_date = today - timedelta(days=6)
            end_date = today
            selected_period = 'last_7_days'

    # Fetch Data using the determined date range
    if selected_person_key and start_date <= end_date:
        try:
            # db_service'ten fonksiyonu çağır
            tracked_data = get_tracked_hours_by_dates(selected_person_key, start_date, end_date)
        except Exception as e:
            flash(f"Data fetching error: {e}", 'danger')

    # Prepare template variables
    selected_employee_name = next((emp['name'] for emp in employee_list if emp['key'] == selected_person_key),
                                  "Select Employee")

    return render_template(
        'hours_tracked.html',
        employees=employee_list,
        available_months=get_available_months(),
        selected_person_key=selected_person_key,
        selected_period=selected_period,
        selected_employee_name=selected_employee_name,
        tracked_data=tracked_data
    )


@main_bp.route('/salary')
def salary():
    if (redirect_response := require_login()): return redirect_response
    # Burada maaş hesaplama veya gösterme mantığı olmalı
    return render_template('salary.html')