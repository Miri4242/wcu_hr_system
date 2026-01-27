import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'dbname': os.environ.get('DB_NAME'),
    'user': os.environ.get('DB_USER'),
    'password': os.environ.get('DB_PASSWORD'),
    'host': os.environ.get('DB_HOST'),
    'port': os.environ.get('DB_PORT', '5432')
}

def check_triggers(table_name):
    query = """
    SELECT trigger_name, event_manipulation, action_statement, action_timing
    FROM information_schema.triggers
    WHERE event_object_table = %s;
    """
    
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute(query, (table_name,))
        rows = cur.fetchall()
        
        print(f"Triggers for table '{table_name}':")
        if not rows:
            print("No triggers found.")
        else:
            for row in rows:
                print(f"Trigger: {row[0]}, Event: {row[1]}, Timing: {row[3]}")
                # print(f"Action: {row[2]}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    check_triggers('pers_person')
