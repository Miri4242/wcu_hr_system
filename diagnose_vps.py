#!/usr/bin/env python3
"""
VPS-də problemi diaqnoz etmək üçün script
"""

import os
import sys
from dotenv import load_dotenv
import psycopg2

# Load environment variables
load_dotenv()

print("=" * 60)
print("VPS DIAGNOSTIC TOOL")
print("=" * 60)

# 1. Check Python version
print(f"\n1. Python Version: {sys.version}")

# 2. Check environment variables
print("\n2. Environment Variables:")
env_vars = ['DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_HOST', 'DB_PORT', 'SECRET_KEY']
for var in env_vars:
    value = os.environ.get(var)
    if value:
        # Mask sensitive data
        if 'PASSWORD' in var or 'SECRET' in var:
            print(f"   ✅ {var}: {'*' * len(value)}")
        else:
            print(f"   ✅ {var}: {value}")
    else:
        print(f"   ❌ {var}: NOT SET")

# 3. Check database connection
print("\n3. Database Connection:")
try:
    DB_CONFIG = {
        'dbname': os.environ.get('DB_NAME'),
        'user': os.environ.get('DB_USER'),
        'password': os.environ.get('DB_PASSWORD'),
        'host': os.environ.get('DB_HOST'),
        'port': os.environ.get('DB_PORT', '5432')
    }
    
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    # Test query
    cur.execute("SELECT COUNT(*) FROM public.pers_person")
    count = cur.fetchone()[0]
    
    print(f"   ✅ Database connected successfully")
    print(f"   ✅ Total persons in database: {count}")
    
    # Test employees query
    cur.execute("""
        SELECT COUNT(*) 
        FROM public.pers_person p
        LEFT JOIN public.pers_position pp ON p.position_id = pp.id
        LEFT JOIN public.auth_department ad ON p.auth_dept_id = ad.id
        WHERE (pp.name IS NULL OR (pp.name NOT ILIKE 'STUDENT' 
                                  AND pp.name NOT ILIKE 'VISITOR' 
                                  AND pp.name NOT ILIKE 'MÜƏLLİM'))
          AND (ad.name IS NULL OR ad.name != 'School')
    """)
    active_count = cur.fetchone()[0]
    print(f"   ✅ Active employees (Administrative): {active_count}")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"   ❌ Database connection failed: {e}")

# 4. Check Flask app file
print("\n4. Flask Application:")
if os.path.exists('app.py'):
    print(f"   ✅ app.py exists")
    file_size = os.path.getsize('app.py')
    print(f"   ✅ File size: {file_size} bytes")
else:
    print(f"   ❌ app.py not found")

# 5. Check virtual environment
print("\n5. Virtual Environment:")
if os.path.exists('.venv'):
    print(f"   ✅ .venv directory exists")
    if os.path.exists('.venv/bin/python'):
        print(f"   ✅ Python binary found in venv")
    else:
        print(f"   ❌ Python binary not found in venv")
else:
    print(f"   ❌ .venv directory not found")

# 6. Check required packages
print("\n6. Required Packages:")
try:
    import flask
    print(f"   ✅ Flask: {flask.__version__}")
except ImportError:
    print(f"   ❌ Flask not installed")

try:
    import psycopg2
    print(f"   ✅ psycopg2: {psycopg2.__version__}")
except ImportError:
    print(f"   ❌ psycopg2 not installed")

try:
    from dotenv import load_dotenv
    print(f"   ✅ python-dotenv installed")
except ImportError:
    print(f"   ❌ python-dotenv not installed")

print("\n" + "=" * 60)
print("DIAGNOSTIC COMPLETE")
print("=" * 60)
