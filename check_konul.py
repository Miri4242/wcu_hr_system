import psycopg2
import os
from dotenv import load_dotenv

def check():
    load_dotenv()
    dbname = os.environ.get('DB_NAME')
    user = os.environ.get('DB_USER')
    password = os.environ.get('DB_PASSWORD')
    host = os.environ.get('DB_HOST')
    port = os.environ.get('DB_PORT')
    
    if not all([dbname, user, password, host, port]):
        print("Database environment variables missing")
        return

    conn = psycopg2.connect(
        dbname=dbname,
        user=user,
        password=password,
        host=host,
        port=port
    )
    cur = conn.cursor()

    # Total teacher transactions
    cur.execute("""
        SELECT COUNT(*)
        FROM public.acc_transaction t
        JOIN public.pers_person p ON (t.pin = p.pin OR (t.name = p.name AND t.last_name = p.last_name))
        JOIN public.pers_position pp ON p.position_id = pp.id
        LEFT JOIN public.auth_department ad ON p.auth_dept_id = ad.id
        WHERE pp.name = 'Müəllim' 
          AND (ad.name IS NULL OR ad.name != 'School')
          AND t.create_time > CURRENT_DATE - INTERVAL '1 year'
    """)
    print(f'Total Teacher Transactions (Last Year): {cur.fetchone()[0]}')

    # Könül Transactions
    cur.execute("""
        SELECT COUNT(*) 
        FROM public.acc_transaction t
        JOIN public.pers_person p ON (t.pin = p.pin OR (t.name = p.name AND t.last_name = p.last_name))
        WHERE (LOWER(p.name) = 'könül' AND LOWER(p.last_name) = 'əhmədova')
    """)
    print(f'Könül Transactions (Total): {cur.fetchone()[0]}')

    # Dates for Könül
    cur.execute("""
        SELECT MIN(create_time), MAX(create_time)
        FROM public.acc_transaction t
        JOIN public.pers_person p ON (t.pin = p.pin OR (t.name = p.name AND t.last_name = p.last_name))
        WHERE (LOWER(p.name) = 'könül' AND LOWER(p.last_name) = 'əhmədova')
    """)
    dates = cur.fetchone()
    print(f'Könül First Transaction: {dates[0]}')
    print(f'Könül Last Transaction: {dates[1]}')

    conn.close()

if __name__ == "__main__":
    check()
