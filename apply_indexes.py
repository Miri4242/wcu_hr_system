
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

def apply_indexes():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        print("Reading database_indexes.sql...")
        with open('database_indexes.sql', 'r', encoding='utf-8') as f:
            sql_content = f.read()
            
        # Split by command, simple split by ; might be risky if comments exist
        # But for this file structure it seems okay or just execute as one block
        print("Applying indexes...")
        cur.execute(sql_content)
        conn.commit()
        print("✅ Indexes applied successfully.")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"❌ Error applying indexes: {e}")

if __name__ == "__main__":
    apply_indexes()
