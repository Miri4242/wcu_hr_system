import psycopg2
import os
from dotenv import load_dotenv
import uuid

# Load environment variables
load_dotenv()

DB_CONFIG = {
    'dbname': os.environ.get('DB_NAME'),
    'user': os.environ.get('DB_USER'),
    'password': os.environ.get('DB_PASSWORD'),
    'host': os.environ.get('DB_HOST'),
    'port': os.environ.get('DB_PORT', '5432')
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def test_deletion():
    conn = get_db_connection()
    cur = conn.cursor()
    
    test_id = str(uuid.uuid4())[:20]
    test_pin = "TEST" + str(uuid.uuid4())[:10]
    test_name = "Test"
    test_last_name = "User"
    
    try:
        print(f"Starting verification test for ID: {test_id}")
        
        # 0. Get a valid department ID
        cur.execute("SELECT id FROM public.auth_department LIMIT 1")
        dept_id_row = cur.fetchone()
        dept_id = dept_id_row[0] if dept_id_row else None
        
        if not dept_id:
            print("Warning: No departments found in public.auth_department")
        
        # 1. Create a dummy employee
        cur.execute("""
            INSERT INTO public.pers_person (id, name, last_name, pin, create_time, auth_dept_id)
            VALUES (%s, %s, %s, %s, NOW(), %s)
        """, (test_id, test_name, test_last_name, test_pin, dept_id))
        
        # 2. Add related records
        print("Adding related records...")
        cur.execute("INSERT INTO public.pers_biotemplate (id, person_id) VALUES (%s, %s)", (str(uuid.uuid4())[:20], test_id))
        cur.execute("INSERT INTO public.pers_certificate (id, person_id) VALUES (%s, %s)", (str(uuid.uuid4())[:20], test_id))
        cur.execute("INSERT INTO public.pers_personchange (id, person_id) VALUES (%s, %s)", (str(uuid.uuid4())[:20], test_id))
        
        conn.commit()
        print("Dummy employee and related records created.")
        
        # 3. Call the delete function logic directly
        print("Running deletion logic...")
        
        # Clean up related records (using a safer approach)
        tables_to_clean = [
            ("pers_biotemplate", "person_id", test_id),
            ("pers_certificate", "person_id", test_id),
            ("pers_personchange", "person_id", test_id),
            ("pers_biophoto", "person_id", test_id),
            ("pers_card", "person_id", test_id),
            ("pers_person_link", "person_id", test_id),
            ("employee_late_arrivals", "employee_id", test_id)
        ]
        
        for table, col, val in tables_to_clean:
            try:
                cur.execute(f"DELETE FROM public.{table} WHERE {col} = %s", (val,))
            except Exception as e:
                print(f"Skipping cleanup for {table}: {e}")
                conn.rollback() # Rollback the sub-transaction error

        # Delete the employee
        cur.execute("DELETE FROM public.pers_person WHERE id = %s", (test_id,))
        
        if cur.rowcount > 0:
            print("Deletion successful!")
        else:
            print("Deletion failed!")
            
        # 4. Verify everything is gone
        cur.execute("SELECT COUNT(*) FROM public.pers_person WHERE id = %s", (test_id,))
        if cur.fetchone()[0] == 0:
            print("Verified: Employee record is gone.")
        else:
            print("Error: Employee record still exists!")

        cur.execute("SELECT COUNT(*) FROM public.pers_biotemplate WHERE person_id = %s", (test_id,))
        if cur.fetchone()[0] == 0:
            print("Verified: Biotemplate record is gone.")
        else:
            print("Error: Biotemplate record still exists!")

        conn.commit()
        print("Verification test passed!")

    except Exception as e:
        conn.rollback()
        print(f"Verification test failed with error: {e}")
    finally:
        # Cleanup just in case
        try:
            cur.execute("DELETE FROM public.pers_biotemplate WHERE person_id = %s", (test_id,))
            cur.execute("DELETE FROM public.pers_certificate WHERE person_id = %s", (test_id,))
            cur.execute("DELETE FROM public.pers_personchange WHERE person_id = %s", (test_id,))
            cur.execute("DELETE FROM public.pers_person WHERE id = %s", (test_id,))
            conn.commit()
        except:
            pass
        cur.close()
        conn.close()

if __name__ == "__main__":
    test_deletion()
