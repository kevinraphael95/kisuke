import os
import psycopg2

def get_connection():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS reiatsu_scores (
            user_id TEXT PRIMARY KEY,
            score INTEGER NOT NULL
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

def get_reiatsu(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT score FROM reiatsu_scores WHERE user_id = %s;", (str(user_id),))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else 0

def add_reiatsu(user_id, amount=1):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO reiatsu_scores (user_id, score)
        VALUES (%s, %s)
        ON CONFLICT (user_id) DO UPDATE
        SET score = reiatsu_scores.score + EXCLUDED.score;
    """, (str(user_id), amount))
    conn.commit()
    cur.close()
    conn.close()
