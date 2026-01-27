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

def find_tables_with_column(column_name):
    query = """
    SELECT table_schema, table_name 
    FROM information_schema.columns 
    WHERE column_name = %s;
    """
    
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute(query, (column_name,))
        rows = cur.fetchall()
        
        print(f"Tables with column '{column_name}':")
        for row in rows:
            print(f"{row[0]}.{row[1]}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    find_tables_with_column('person_id')
    print("-" * 20)
    find_tables_with_column('pin') # Some systems use 'pin' for person ID
