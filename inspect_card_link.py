
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

def get_columns(table_name):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    print(f"\n--- Columns in {table_name} ---")
    cur.execute(f"""
        SELECT column_name
        FROM information_schema.columns 
        WHERE table_name = '{table_name}'
        ORDER BY column_name;
    """)
    columns = cur.fetchall()
    for col in columns:
        print(f"{col[0]}")
    conn.close()

if __name__ == "__main__":
    try:
        get_columns('pers_card')
        get_columns('pers_person')
    except Exception as e:
        print(f"Connection failed: {e}")
