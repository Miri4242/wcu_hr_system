
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

def verify_match():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    print("\n--- Verifying Match ---")
    
    # Check total transactions
    cur.execute("SELECT COUNT(*) FROM public.acc_transaction")
    total_transactions = cur.fetchone()[0]
    print(f"Total Transactions: {total_transactions}")
    
    # Check matches
    cur.execute("""
        SELECT COUNT(*) 
        FROM public.acc_transaction t
        JOIN public.pers_card c ON t.card_no = c.card_no
    """)
    matches = cur.fetchone()[0]
    print(f"Matches found: {matches}")
    
    if total_transactions > 0:
        print(f"Match percentage: {matches/total_transactions*100:.2f}%")
        
    # Check sample match
    print("\n--- Sample Match Details ---")
    cur.execute("""
        SELECT t.card_no, c.person_id, p.name, p.last_name
        FROM public.acc_transaction t
        JOIN public.pers_card c ON t.card_no = c.card_no
        JOIN public.pers_person p ON c.person_id = p.id
        LIMIT 5
    """)
    samples = cur.fetchall()
    for s in samples:
        print(f"Card: {s[0][:10]}... -> Person: {s[2]} {s[3]}")

    conn.close()

if __name__ == "__main__":
    try:
        verify_match()
    except Exception as e:
        print(f"Connection failed: {e}")
