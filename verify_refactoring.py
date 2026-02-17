
import sys
import os

# Set encoding to utf-8 for output BEFORE importing app
sys.stdout.reconfigure(encoding='utf-8')

from datetime import datetime, timedelta
from app import get_employee_logs, get_employee_list_for_dropdown, normalize_name, get_db_connection

def test_logs():
    print("\n--- Testing get_employee_logs (New Logic) ---")
    
    # 1. Get a person key (Miryusif)
    target_name = "Miryusif Babayev"
    print(f"Target: {target_name}")
    
    # Try to find him in the dropdown list to get the key
    employees = get_employee_list_for_dropdown(category="active")
    person_key = None
    for emp in employees:
        if "Miryusif" in emp['name'] and "Babayev" in emp['name']:
            person_key = emp['key']
            print(f"Found Key: {person_key}")
            break
            
    if not person_key:
        print("Could not find Miryusif in active list. Trying to generate key manually.")
        person_key = normalize_name("MIRYUSIF") + normalize_name("BABAYEV")
        
    # 2. Fetch logs for last 30 days
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)
    
    print(f"Fetching logs from {start_date} to {end_date}...")
    try:
        logs = get_employee_logs(person_key=person_key, start_date=start_date, end_date=end_date, category="active")
        print(f"Logs found: {len(logs)}")
        
        if len(logs) > 0:
            print("\nLatest 3 logs:")
            for log in logs[:3]:
                print(f"Date: {log['date']}, Status: {log['status_display']}, In: {log['first_in']}, Out: {log['last_out']}")
        else:
            print("No logs found. This might be correct if he hasn't attended, but verify manually.")
            
    except Exception as e:
        print(f"❌ Error in get_employee_logs: {e}")
        import traceback
        traceback.print_exc()

def test_late_system():
    print("\n--- Testing late_arrival_system (New Logic) ---")
    try:
        from late_arrival_system import check_employee_late_arrival
        
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id FROM public.pers_person WHERE name ILIKE '%Miryusif%' AND last_name ILIKE '%Babayev%'")
        row = cur.fetchone()
        
        if row:
            emp_id = row[0]
            print(f"Found ID: {emp_id}")
            
            # Check for today (or yesterday if weekend)
            check_date = datetime.now().date()
            if check_date.weekday() >= 5: # Weekend
                check_date = check_date - timedelta(days=2)
                
            print(f"Checking late status for {check_date}...")
            result = check_employee_late_arrival(emp_id, check_date)
            print(f"Result: {result}")
        else:
            print("Could not find ID for late system test.")
            
        conn.close()
        
    except ImportError:
        print("Could not import late_arrival_system. Make sure requirements are met.")
    except Exception as e:
        print(f"❌ Error in late_arrival_system: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_logs()
    test_late_system()
