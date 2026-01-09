#!/usr/bin/env python3
"""
Gerçek email gönderme testi
"""

from late_arrival_system import *
from datetime import date

def send_real_late_email():
    """Tünzalə'ye gerçek email gönder"""
    print("🚀 Sending REAL email to late employee...")
    
    # Çalışanın bilgilerini al
    conn = get_db_connection()
    if not conn:
        print("❌ Database connection failed")
        return
    
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT p.id FROM public.pers_person p
            WHERE p.name = 'Tünzalə' AND p.last_name = 'Məcidova'
        """, )
        
        employee = cur.fetchone()
        if not employee:
            print("❌ Employee not found")
            return
        
        employee_id = employee[0]
        print(f"✅ Found employee ID: {employee_id}")
        
        # Gecikme kontrolü yap
        late_result = check_employee_late_arrival(employee_id)
        
        if late_result and late_result['is_late']:
            print(f"🔴 Late arrival confirmed: {late_result['late_minutes']} minutes")
            
            # Gecikme kaydını kaydet
            record_id = save_late_arrival_record(late_result)
            print(f"💾 Record saved with ID: {record_id}")
            
            # Employee bilgilerini al
            employee_info = get_employee_email(employee_id)
            
            if employee_info and employee_info.get('email'):
                print(f"📧 Sending email to: {employee_info['email']}")
                
                # GERÇEK EMAIL GÖNDER
                email_sent = send_late_arrival_email(late_result, employee_info)
                
                if email_sent:
                    print("✅ EMAIL SENT SUCCESSFULLY!")
                    
                    # Database'de email durumunu güncelle
                    update_late_arrival_email_status(employee_id, late_result['late_date'])
                    print("✅ Email status updated in database")
                    
                    # Kontrol et
                    cur.execute("""
                        SELECT email_sent, email_sent_at 
                        FROM public.employee_late_arrivals 
                        WHERE employee_id = %s AND late_date = %s
                    """, (employee_id, late_result['late_date']))
                    
                    result = cur.fetchone()
                    if result:
                        email_sent_db, sent_at = result
                        print(f"📊 Database status: Email sent = {email_sent_db}, Time = {sent_at}")
                    
                else:
                    print("❌ EMAIL SENDING FAILED!")
                    
            else:
                print("❌ No email address found")
                
        else:
            print("✅ Employee is not late today")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    send_real_late_email()