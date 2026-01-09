# HR System Performance Optimization
# Bu dosya performans iyileştirmelerini içerir

from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response, jsonify
import psycopg2
from datetime import datetime, date, timedelta, timezone
from collections import defaultdict
from io import StringIO
import csv
import calendar
import hashlib
import secrets
import os
from dotenv import load_dotenv
import functools
import time

# Cache decorator for expensive operations
def cache_result(timeout=300):  # 5 minutes default
    def decorator(func):
        cache = {}
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}_{hash(str(args) + str(sorted(kwargs.items())))}"
            current_time = time.time()
            
            # Check if we have cached result and it's not expired
            if cache_key in cache:
                result, timestamp = cache[cache_key]
                if current_time - timestamp < timeout:
                    return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache[cache_key] = (result, current_time)
            
            # Clean old cache entries (simple cleanup)
            if len(cache) > 100:  # Keep cache size reasonable
                oldest_key = min(cache.keys(), key=lambda k: cache[k][1])
                del cache[oldest_key]
            
            return result
        return wrapper
    return decorator

# Optimized database connection with connection pooling
class DatabasePool:
    def __init__(self, db_config, min_connections=2, max_connections=10):
        self.db_config = db_config
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.pool = []
        self.active_connections = 0
        
        # Initialize minimum connections
        for _ in range(min_connections):
            conn = self._create_connection()
            if conn:
                self.pool.append(conn)
    
    def _create_connection(self):
        try:
            conn = psycopg2.connect(**self.db_config)
            return conn
        except psycopg2.Error as e:
            print(f"🚨 Database connection error: {e}")
            return None
    
    def get_connection(self):
        if self.pool:
            conn = self.pool.pop()
            # Test connection
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                self.active_connections += 1
                return conn
            except:
                # Connection is dead, create new one
                conn.close()
        
        # Create new connection if pool is empty or connection is dead
        if self.active_connections < self.max_connections:
            conn = self._create_connection()
            if conn:
                self.active_connections += 1
                return conn
        
        return None
    
    def return_connection(self, conn):
        if conn and not conn.closed:
            self.pool.append(conn)
            self.active_connections -= 1

# Initialize connection pool
DB_CONFIG = {
    'dbname': os.environ.get('DB_NAME'),
    'user': os.environ.get('DB_USER'),
    'password': os.environ.get('DB_PASSWORD'),
    'host': os.environ.get('DB_HOST'),
    'port': os.environ.get('DB_PORT', '5432')
}

db_pool = DatabasePool(DB_CONFIG)

def get_db_connection_optimized():
    """Get optimized database connection from pool"""
    return db_pool.get_connection()

def return_db_connection(conn):
    """Return connection to pool"""
    db_pool.return_connection(conn)

# Optimized dashboard data with caching and single query
@cache_result(timeout=60)  # Cache for 1 minute
def get_dashboard_data_optimized():
    """Optimized dashboard data with single query and caching"""
    conn = get_db_connection_optimized()
    if conn is None:
        return {
            'total_employees': 0, 'total_departments': 0, 'total_transactions': 0,
            'new_employees_this_month': 0, 'today_birthdays': [],
            'present_employees_count': 0, 'attendance_percentage': 0.0,
            'absent_employees': [], 'late_employees': []
        }

    cur = conn.cursor()
    try:
        today_date = datetime.now().date()
        
        # Single optimized query for all dashboard stats
        cur.execute("""
            WITH employee_stats AS (
                SELECT 
                    COUNT(*) as total_employees,
                    COUNT(CASE WHEN date_trunc('month', p.create_time) = date_trunc('month', NOW()) THEN 1 END) as new_this_month
                FROM public.pers_person p
                LEFT JOIN public.pers_position pp ON p.position_id = pp.id
                WHERE pp.name IS NULL OR (pp.name NOT ILIKE 'STUDENT' AND pp.name NOT ILIKE 'VISITOR' AND pp.name NOT ILIKE 'MÜƏLLİM')
            ),
            transaction_stats AS (
                SELECT 
                    COUNT(*) as total_transactions,
                    COUNT(DISTINCT CASE WHEN t.reader_name ILIKE '%-in%' THEN (t.name, t.last_name) END) as present_count
                FROM public.acc_transaction t
                INNER JOIN public.pers_person p ON t.name = p.name AND t.last_name = p.last_name
                LEFT JOIN public.pers_position pp ON p.position_id = pp.id
                WHERE DATE(t.create_time) = %s 
                AND (pp.name IS NULL OR (pp.name NOT ILIKE 'student' AND pp.name NOT ILIKE 'visitor' AND pp.name NOT ILIKE 'müəllim'))
            ),
            department_stats AS (
                SELECT COUNT(*) as total_departments FROM public.auth_department
            )
            SELECT 
                es.total_employees,
                es.new_this_month,
                ts.total_transactions,
                ts.present_count,
                ds.total_departments
            FROM employee_stats es, transaction_stats ts, department_stats ds
        """, (today_date,))
        
        stats = cur.fetchone()
        
        data = {
            'total_employees': stats[0] or 0,
            'new_employees_this_month': stats[1] or 0,
            'total_transactions': stats[2] or 0,
            'present_employees_count': stats[3] or 0,
            'total_departments': stats[4] or 0,
            'attendance_percentage': round((stats[3] / stats[0] * 100) if stats[0] > 0 else 0, 2),
            'absent_employees': [],  # Load separately if needed
            'late_employees': [],    # Load separately if needed
            'today_birthdays': []    # Load separately if needed
        }
        
        return data
        
    except psycopg2.Error as e:
        print(f"🚨 Dashboard Query Error: {e}")
        return {
            'total_employees': 0, 'total_departments': 0, 'total_transactions': 0,
            'new_employees_this_month': 0, 'today_birthdays': [],
            'present_employees_count': 0, 'attendance_percentage': 0.0,
            'absent_employees': [], 'late_employees': []
        }
    finally:
        if cur: cur.close()
        return_db_connection(conn)

# Optimized employee list with pagination and indexing
@cache_result(timeout=120)  # Cache for 2 minutes
def get_employee_list_optimized(limit=None, offset=None):
    """Optimized employee list with proper indexing"""
    conn = get_db_connection_optimized()
    if conn is None: 
        return []

    cur = conn.cursor()
    try:
        # Optimized query with proper indexing
        query = """
            SELECT p.id, p.name, p.last_name, p.mobile_phone, p.email, 
                   p.birthday, pp.name AS position_name, p.create_time AS hire_date, p.photo_path
            FROM public.pers_person p
            LEFT JOIN public.pers_position pp ON p.position_id = pp.id
            WHERE (pp.name IS NULL OR (pp.name NOT ILIKE 'STUDENT' AND pp.name NOT ILIKE 'VISITOR' AND pp.name NOT ILIKE 'MÜƏLLİM'))
            ORDER BY p.last_name, p.name
        """
        
        params = []
        if limit:
            query += " LIMIT %s"
            params.append(limit)
            if offset:
                query += " OFFSET %s"
                params.append(offset)
        
        cur.execute(query, params)
        employees_raw = cur.fetchall()
        
        employees = []
        for row in employees_raw:
            employees.append({
                'id': row[0],
                'name': row[1],
                'last_name': row[2],
                'mobile_phone': row[3] or 'N/A',
                'email': row[4] or 'N/A',
                'birthday': row[5].strftime('%d.%m.%Y') if row[5] else 'N/A',
                'position': row[6] or 'Undefined',
                'hire_date': row[7].strftime('%d.%m.%Y') if row[7] else 'N/A',
                'photo_path': row[8] or ''
            })
        
        return employees
        
    except psycopg2.Error as e:
        print(f"🚨 Employee List Fetch Error: {e}")
        return []
    finally:
        if cur: cur.close()
        return_db_connection(conn)

# Database indexing recommendations
DATABASE_INDEXES = """
-- Performance optimization indexes
-- Run these in your PostgreSQL database

-- Index for employee filtering by position
CREATE INDEX IF NOT EXISTS idx_pers_person_position_id ON public.pers_person(position_id);
CREATE INDEX IF NOT EXISTS idx_pers_position_name ON public.pers_position(name);

-- Index for transaction queries
CREATE INDEX IF NOT EXISTS idx_acc_transaction_date ON public.acc_transaction(DATE(create_time));
CREATE INDEX IF NOT EXISTS idx_acc_transaction_name_date ON public.acc_transaction(name, last_name, DATE(create_time));
CREATE INDEX IF NOT EXISTS idx_acc_transaction_reader ON public.acc_transaction(reader_name);

-- Index for employee names (for joins)
CREATE INDEX IF NOT EXISTS idx_pers_person_name ON public.pers_person(name, last_name);

-- Index for birthday queries
CREATE INDEX IF NOT EXISTS idx_pers_person_birthday ON public.pers_person(birthday);

-- Index for employee creation date
CREATE INDEX IF NOT EXISTS idx_pers_person_create_time ON public.pers_person(create_time);

-- Composite index for common queries
CREATE INDEX IF NOT EXISTS idx_pers_person_composite ON public.pers_person(position_id, name, last_name);
"""

# Frontend optimization recommendations
FRONTEND_OPTIMIZATIONS = """
Frontend Performance Optimizations:

1. Image Optimization:
   - Use WebP format for better compression
   - Implement lazy loading for images
   - Use appropriate image sizes (don't load 1MB images for 40px avatars)

2. JavaScript Optimization:
   - Debounce search inputs (wait 300ms before searching)
   - Use virtual scrolling for large lists
   - Minimize DOM manipulations

3. CSS Optimization:
   - Use CSS transforms instead of changing layout properties
   - Minimize repaints and reflows
   - Use will-change property for animated elements

4. Caching:
   - Implement browser caching for static assets
   - Use service workers for offline functionality
   - Cache API responses in localStorage/sessionStorage

5. Network Optimization:
   - Compress responses (gzip/brotli)
   - Use CDN for static assets
   - Implement request batching
"""

print("Performance optimization file created!")
print("\nKey optimizations:")
print("1. Database connection pooling")
print("2. Query result caching")
print("3. Optimized dashboard queries")
print("4. Database indexing recommendations")
print("5. Frontend optimization guidelines")