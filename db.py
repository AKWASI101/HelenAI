"""
Helena — Database helper
Handles visit count tracking via PostgreSQL.
"""

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )

def increment_visit():
    """Increment visit count by 1 and return the new total."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("UPDATE visits SET count = count + 1 RETURNING count;")
        count = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return count
    except Exception as e:
        print(f"[Helena] DB error: {e}")
        return None

def get_visit_count():
    """Return current visit count."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT count FROM visits LIMIT 1;")
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        return count
    except Exception as e:
        print(f"[Helena] DB error: {e}")
        return None