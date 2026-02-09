import os
import psycopg2
from dotenv import load_dotenv
import sys

# Force UTF-8
sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

DB_CONFIG = {
    'dbname': os.environ.get('DB_NAME'),
    'user': os.environ.get('DB_USER'),
    'password': os.environ.get('DB_PASSWORD'),
    'host': os.environ.get('DB_HOST'),
    'port': os.environ.get('DB_PORT', '5432')
}

def check_indexes():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        print("Checking existing indexes on public tables...")
        cur.execute("""
            SELECT tablename, indexname, indexdef 
            FROM pg_indexes 
            WHERE schemaname = 'public' 
            ORDER BY tablename, indexname;
        """)
        
        indexes = cur.fetchall()
        for table, name, definition in indexes:
            print(f"Table: {table} | Index: {name}")
            # print(f"  Definition: {definition}\n")

        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_indexes()
