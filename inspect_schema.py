
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

def get_table_info(table_name):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    print(f"\n--- Columns in {table_name} ---")
    cur.execute(f"""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = '{table_name}';
    """)
    columns = cur.fetchall()
    for col in columns:
        print(f"{col[0]}: {col[1]}")
        
    print(f"\n--- Sample Data from {table_name} (First 1 row) ---")
    try:
        cur.execute(f"SELECT * FROM public.{table_name} LIMIT 1")
        row = cur.fetchone()
        if row:
            col_names = [desc[0] for desc in cur.description]
            for name, value in zip(col_names, row):
                print(f"{name}: {value}")
        else:
            print("Table is empty.")
    except Exception as e:
        print(f"Error fetching data: {e}")

    conn.close()

if __name__ == "__main__":
    try:
        get_table_info('pers_card')
        get_table_info('pers_issuecard')
    except Exception as e:
        print(f"Connection failed: {e}")
