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

def check_keys(table_name):
    query = """
    SELECT
        tc.constraint_name, 
        tc.constraint_type,
        kcu.column_name
    FROM 
        information_schema.table_constraints AS tc 
        JOIN information_schema.key_column_usage AS kcu
          ON tc.constraint_name = kcu.constraint_name
          AND tc.table_schema = kcu.table_schema
    WHERE tc.table_name=%s AND tc.constraint_type IN ('PRIMARY KEY', 'UNIQUE');
    """
    
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute(query, (table_name,))
        rows = cur.fetchall()
        
        print(f"Keys for table '{table_name}':")
        for row in rows:
            print(f"Type: {row[1]}, Column: {row[2]} [Constraint: {row[0]}]")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    check_keys('pers_person')
