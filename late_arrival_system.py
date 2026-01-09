#!/usr/bin/env python3
"""
Gecikme Takip Sistemi
Bu sistem çalışanların gecikme durumlarını kontrol eder ve email gönderir.
"""

import psycopg2
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, date, time, timedelta
import os
from dotenv import load_dotenv
import logging

load_dotenv()

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('late_arrival_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Database connection
DB_CONFIG = {
    'dbname': os.environ.get('DB_NAME'),
    'user': os.environ.get('DB_USER'),
    'password': os.environ.get('DB_PASSWORD'),
    'host': os.environ.get('DB_HOST'),
    'port': os.environ.get('DB_PORT', '5432')
}

def get_db_connection():
    """Database bağlantısı oluştur"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except psycopg2.Error as e:
        logger.error(f"Database connection error: {e}")
        return None

def get_system_settings():
    """Sistem ayarlarını getir"""
    conn = get_db_connection()
    if not conn:
        return {}
    
    settings = {}
    try:
        cur = conn.cursor()
        cur.execute("SELECT setting_name, setting_value FROM public.late_arrival_settings")
        for name, value in cur.fetchall():
            settings[name] = value
        return settings
    except psycopg2.Error as e:
        logger.error(f"Settings fetch error: {e}")
        return {}
    finally:
        if conn:
            conn.close()

def get_employee_first_entry_today(employee_id, check_date=None):
    """Çalışanın bugünkü ilk giriş saatini getir"""
    if not check_date:
        check_date = date.today()
    
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cur = conn.cursor()
        
        # Çalışanın adını ve soyadını al
        cur.execute("""
            SELECT name, last_name 
            FROM public.pers_person 
            WHERE id = %s
        """, (employee_id,))
        
        employee_data = cur.fetchone()
        if not employee_data:
            logger.warning(f"Employee not found: {employee_id}")
            return None
        
        name, last_name = employee_data
        
        # İlk giriş saatini bul
        start_datetime = datetime.combine(check_date, datetime.min.time())
        end_datetime = datetime.combine(check_date, datetime.max.time())
        
        cur.execute("""
            SELECT MIN(t.create_time) as first_entry
            FROM public.acc_transaction t
            WHERE t.name = %s 
              AND t.last_name = %s
              AND t.create_time BETWEEN %s AND %s
              AND t.reader_name ~ '[1-2]'  -- Sadece giriş kapıları (1 ve 2)
        """, (name, last_name, start_datetime, end_datetime))
        
        result = cur.fetchone()
        return result[0] if result and result[0] else None
        
    except psycopg2.Error as e:
        logger.error(f"First entry fetch error: {e}")
        return None
    finally:
        if conn:
            conn.close()

def check_employee_late_arrival(employee_id, check_date=None):
    """Çalışanın gecikme durumunu kontrol et"""
    if not check_date:
        check_date = date.today()
    
    settings = get_system_settings()
    work_start_time = datetime.strptime(settings.get('work_start_time', '09:00:00'), '%H:%M:%S').time()
    late_threshold = int(settings.get('late_threshold_minutes', '15'))
    
    # İlk giriş saatini al
    first_entry = get_employee_first_entry_today(employee_id, check_date)
    if not first_entry:
        logger.info(f"No entry found for employee {employee_id} on {check_date}")
        return None
    
    # Gecikme hesapla
    actual_time = first_entry.time()
    expected_datetime = datetime.combine(check_date, work_start_time)
    actual_datetime = datetime.combine(check_date, actual_time)
    
    if actual_datetime > expected_datetime:
        late_minutes = int((actual_datetime - expected_datetime).total_seconds() / 60)
        
        if late_minutes >= late_threshold:
            return {
                'employee_id': employee_id,
                'late_date': check_date,
                'expected_time': work_start_time,
                'actual_time': actual_time,
                'late_minutes': late_minutes,
                'is_late': True
            }
    
    return {
        'employee_id': employee_id,
        'late_date': check_date,
        'expected_time': work_start_time,
        'actual_time': actual_time,
        'late_minutes': 0,
        'is_late': False
    }

def save_late_arrival_record(late_data):
    """Gecikme kaydını veritabanına kaydet"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO public.employee_late_arrivals 
            (employee_id, late_date, expected_arrival_time, actual_arrival_time, late_minutes)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (employee_id, late_date) 
            DO UPDATE SET
                actual_arrival_time = EXCLUDED.actual_arrival_time,
                late_minutes = EXCLUDED.late_minutes,
                updated_at = CURRENT_TIMESTAMP
            RETURNING id
        """, (
            late_data['employee_id'],
            late_data['late_date'],
            late_data['expected_time'],
            late_data['actual_time'],
            late_data['late_minutes']
        ))
        
        record_id = cur.fetchone()[0]
        conn.commit()
        logger.info(f"Late arrival record saved: {record_id}")
        return record_id
        
    except psycopg2.Error as e:
        logger.error(f"Save late arrival error: {e}")
        conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def get_employee_email(employee_id):
    """Çalışanın email adresini getir - sadece geçerli email adresleri"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT name, last_name, email 
            FROM public.pers_person 
            WHERE id = %s
        """, (employee_id,))
        
        result = cur.fetchone()
        if result:
            email = result[2]
            
            # Email geçerli mi kontrol et
            if email and is_valid_email(email):
                return {
                    'name': result[0],
                    'last_name': result[1],
                    'email': email,
                    'full_name': f"{result[0]} {result[1]}"
                }
            else:
                # Geçersiz email varsa log at ama sessizce geç
                if email:
                    logger.info(f"Skipping invalid email for employee {employee_id}: {email[:20]}...")
                else:
                    logger.info(f"No email address for employee {employee_id}")
                return None
        return None
        
    except psycopg2.Error as e:
        logger.error(f"Employee email fetch error: {e}")
        return None
    finally:
        if conn:
            conn.close()

def is_valid_email(email):
    """Email formatını kontrol et"""
    import re
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def send_late_arrival_email(late_data, employee_info):
    """Gecikme bildirimi emaili gönder"""
    settings = get_system_settings()
    
    if settings.get('email_enabled', 'false').lower() != 'true':
        logger.info("Email sending is disabled")
        return False
    
    if not employee_info.get('email'):
        logger.warning(f"No email address for employee {late_data['employee_id']}")
        return False
    
    # Artık email validation'a gerek yok çünkü get_employee_email zaten geçerli emailleri döndürüyor
    
    try:
        # Email içeriği hazırla
        subject_template = settings.get('email_template_subject', 'Late Arrival Notification - {date}')
        body_template = settings.get('email_template_body', 
            'Dear {name},\n\nYou were {late_minutes} minutes late on {date}.\n'
            'Expected arrival time: {expected_time}\nYour arrival time: {actual_time}\n\n'
            'Please ensure punctuality in the future.\n\nBest regards,\nHR Department')
        
        # Template değişkenlerini değiştir
        email_vars = {
            'name': employee_info['full_name'],
            'date': late_data['late_date'].strftime('%d.%m.%Y'),
            'late_minutes': late_data['late_minutes'],
            'expected_time': late_data['expected_time'].strftime('%H:%M'),
            'actual_time': late_data['actual_time'].strftime('%H:%M')
        }
        
        subject = subject_template.format(**email_vars)
        body = body_template.format(**email_vars)
        
        # SMTP ayarları - önce .env'den, sonra database'den
        smtp_server = os.getenv('SMTP_SERVER') or settings.get('smtp_server', '')
        smtp_port = int(os.getenv('SMTP_PORT', '587') or settings.get('smtp_port', '587'))
        smtp_username = os.getenv('SMTP_USERNAME') or settings.get('smtp_username', '')
        smtp_password = os.getenv('SMTP_PASSWORD') or settings.get('smtp_password', '')
        from_email = os.getenv('FROM_EMAIL') or settings.get('from_email', 'hr@company.com')
        
        if not all([smtp_server, smtp_username, smtp_password]):
            logger.error("SMTP settings incomplete")
            return False
        
        # Email oluştur
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = employee_info['email']
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # SMTP ile gönder
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.send_message(msg)
        server.quit()
        
        logger.info(f"Late arrival email sent to {employee_info['email']}")
        
        # Email kaydını veritabanına kaydet (MUTLAKA)
        save_email_record(late_data['employee_id'], employee_info, subject, body, 'sent')
        
        return True
        
    except Exception as e:
        logger.error(f"Email send error: {e}")
        # Hata durumunda da kaydet
        try:
            save_email_record(late_data['employee_id'], employee_info, subject, body, 'failed', str(e))
        except:
            pass  # Kayıt hatası olursa da devam et
        return False

def save_email_record(employee_id, employee_info, subject, body, status, error_msg=None):
    """Email gönderim kaydını veritabanına kaydet"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO public.late_arrival_emails 
            (employee_id, employee_name, employee_email, email_subject, email_body, email_status, error_message)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            employee_id,
            employee_info.get('full_name', ''),
            employee_info.get('email', ''),
            subject,
            body,
            status,
            error_msg
        ))
        
        conn.commit()
        return True
        
    except psycopg2.Error as e:
        logger.error(f"Email record save error: {e}")
        return False
    finally:
        if conn:
            conn.close()

def update_late_arrival_email_status(employee_id, check_date):
    """Gecikme kaydının email durumunu güncelle"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE public.employee_late_arrivals 
            SET email_sent = true, email_sent_at = CURRENT_TIMESTAMP
            WHERE employee_id = %s AND late_date = %s
        """, (employee_id, check_date))
        
        conn.commit()
        return True
        
    except psycopg2.Error as e:
        logger.error(f"Email status update error: {e}")
        return False
    finally:
        if conn:
            conn.close()

def is_email_already_sent_today(employee_id, check_date):
    """Bu çalışana bugün email gönderildi mi kontrol et"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cur = conn.cursor()
        
        # 1. employee_late_arrivals tablosundan kontrol et
        cur.execute("""
            SELECT email_sent, email_sent_at 
            FROM public.employee_late_arrivals 
            WHERE employee_id = %s AND late_date = %s AND email_sent = true
        """, (employee_id, check_date))
        
        late_arrival_record = cur.fetchone()
        if late_arrival_record:
            logger.info(f"Email already sent via late_arrivals table for employee {employee_id} on {check_date}")
            return True
        
        # 2. late_arrival_emails tablosundan da kontrol et (çift güvenlik)
        cur.execute("""
            SELECT COUNT(*) 
            FROM public.late_arrival_emails 
            WHERE employee_id = %s 
              AND DATE(sent_at) = %s 
              AND email_status = 'sent'
        """, (employee_id, check_date))
        
        email_count = cur.fetchone()[0]
        if email_count > 0:
            logger.info(f"Email already sent via emails table for employee {employee_id} on {check_date} ({email_count} times)")
            return True
        
        return False
        
    except psycopg2.Error as e:
        logger.error(f"Email check error: {e}")
        return False  # Hata durumunda email göndermeye izin verme
    finally:
        if conn:
            conn.close()


def check_all_employees_late_arrivals(check_date=None, limit=None):
    """Tüm çalışanların gecikme durumunu kontrol et"""
    if not check_date:
        check_date = date.today()
    
    # Hafta sonu kontrolü
    settings = get_system_settings()
    if check_date.weekday() >= 5 and settings.get('weekend_check_enabled', 'false').lower() != 'true':
        logger.info(f"Weekend check disabled, skipping {check_date}")
        return
    
    logger.info(f"Checking late arrivals for {check_date}")
    
    # Tüm aktif çalışanları al
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        cur = conn.cursor()
        
        # Limit ekle - production'da sadece ilk 50 çalışanı kontrol et
        limit_clause = f"LIMIT {limit}" if limit else ""
        
        cur.execute(f"""
            SELECT p.id, pp.name as position_name
            FROM public.pers_person p
            LEFT JOIN public.pers_position pp ON p.position_id = pp.id
            WHERE pp.name IS NOT NULL 
            AND pp.name NOT ILIKE '%STUDENT%' 
            AND pp.name NOT ILIKE '%ÖĞRENCİ%'
            AND pp.name NOT ILIKE '%VISITOR%' 
            AND pp.name NOT ILIKE '%ZİYARETÇİ%'
            AND pp.name NOT ILIKE '%MÜƏLLİM%'
            AND pp.name NOT ILIKE '%TEACHER%'
            AND pp.name NOT ILIKE '%GUEST%'
            AND pp.name NOT ILIKE '%KONUK%'
            ORDER BY p.last_name, p.name
            {limit_clause}
        """)
        
        employees = []
        for row in cur.fetchall():
            employee_id = row[0]
            position_name = row[1] if len(row) > 1 else "Unknown"
            employees.append(employee_id)
            
        logger.info(f"Found {len(employees)} employees to check (excluding students/teachers/visitors)")
        
        late_count = 0
        email_sent_count = 0
        email_failed_count = 0
        already_sent_count = 0
        
        for i, employee_id in enumerate(employees):
            try:
                # Her 10 çalışanda bir progress log
                if i % 10 == 0:
                    logger.info(f"Processing employee {i+1}/{len(employees)}")
                
                # ÖNCE: Bu çalışana bugün email gönderildi mi kontrol et (çift güvenlik)
                if is_email_already_sent_today(employee_id, check_date):
                    already_sent_count += 1
                    continue
                
                # Gecikme kontrolü
                late_result = check_employee_late_arrival(employee_id, check_date)
                
                if late_result and late_result['is_late']:
                    late_count += 1
                    logger.info(f"Employee {employee_id} is late: {late_result['late_minutes']} minutes")
                    
                    # Gecikme kaydını kaydet
                    record_id = save_late_arrival_record(late_result)
                    
                    if record_id:
                        # Employee bilgilerini al
                        employee_info = get_employee_email(employee_id)
                        
                        if employee_info and employee_info.get('email'):
                            logger.info(f"Sending email to {employee_info['email']} for employee {employee_id}")
                            
                            # Email gönder
                            email_success = send_late_arrival_email(late_result, employee_info)
                            
                            if email_success:
                                # Email durumunu güncelle
                                update_late_arrival_email_status(employee_id, check_date)
                                email_sent_count += 1
                                logger.info(f"✅ Email sent successfully to {employee_info['email']}")
                            else:
                                email_failed_count += 1
                                logger.error(f"❌ Failed to send email to {employee_info['email']}")
                        else:
                            logger.warning(f"No email address found for employee {employee_id}")
                    else:
                        logger.error(f"Failed to save late arrival record for employee {employee_id}")
                        
            except Exception as e:
                logger.error(f"Error processing employee {employee_id}: {e}")
                email_failed_count += 1
                continue  # Bir çalışanda hata olursa diğerlerine devam et
        
        logger.info(f"Late arrival check completed:")
        logger.info(f"  - Late employees: {late_count}")
        logger.info(f"  - Emails sent: {email_sent_count}")
        logger.info(f"  - Emails failed: {email_failed_count}")
        logger.info(f"  - Already sent today: {already_sent_count}")
        
    except psycopg2.Error as e:
        logger.error(f"Employee list fetch error: {e}")
    finally:
        if conn:
            conn.close()

def update_monthly_statistics(year=None, month=None):
    """Aylık gecikme istatistiklerini güncelle"""
    if not year or not month:
        today = date.today()
        year = today.year
        month = today.month
    
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO public.employee_late_statistics 
            (employee_id, year, month, total_late_days, total_late_minutes, 
             average_late_minutes, max_late_minutes, emails_sent)
            SELECT 
                employee_id,
                %s as year,
                %s as month,
                COUNT(*) as total_late_days,
                SUM(late_minutes) as total_late_minutes,
                AVG(late_minutes) as average_late_minutes,
                MAX(late_minutes) as max_late_minutes,
                COUNT(CASE WHEN email_sent THEN 1 END) as emails_sent
            FROM public.employee_late_arrivals
            WHERE EXTRACT(YEAR FROM late_date) = %s
              AND EXTRACT(MONTH FROM late_date) = %s
            GROUP BY employee_id
            ON CONFLICT (employee_id, year, month)
            DO UPDATE SET
                total_late_days = EXCLUDED.total_late_days,
                total_late_minutes = EXCLUDED.total_late_minutes,
                average_late_minutes = EXCLUDED.average_late_minutes,
                max_late_minutes = EXCLUDED.max_late_minutes,
                emails_sent = EXCLUDED.emails_sent,
                updated_at = CURRENT_TIMESTAMP
        """, (year, month, year, month))
        
        conn.commit()
        logger.info(f"Monthly statistics updated for {year}-{month}")
        
    except psycopg2.Error as e:
        logger.error(f"Statistics update error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    # Test çalıştırma
    logger.info("Starting late arrival check...")
    check_all_employees_late_arrivals()
    update_monthly_statistics()
    logger.info("Late arrival check completed.")