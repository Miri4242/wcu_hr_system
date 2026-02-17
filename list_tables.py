
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

def list_tables():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    print("\n--- Tables in public schema ---")
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name;
    """)
    tables = cur.fetchall()
    for t in tables:
        print(t[0])
    
    conn.close()

if __name__ == "__main__":
    try:
        list_tables()
    except Exception as e:
        print(f"Connection failed: {e}")
