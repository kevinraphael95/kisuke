import os
import psycopg2
from urllib.parse import urlparse

# Connexion à la base de données via DATABASE_URL
def get_connection():
    url = os.getenv("DATABASE_URL")
    result = urlparse(url)

    return psycopg2.connect(
        dbname=result.path[1:],
        user=result.username,
        password=result.password,
        host=result.hostname,
        port=result.port
    )

# Initialisation des tables
def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # Table pour les scores Reiatsu
    cur.execute("""
        CREATE TABLE IF NOT EXISTS reiatsu_scores (
            user_id TEXT PRIMARY KEY,
            score INTEGER NOT NULL
        );
    """)

    # Table pour le salon de spawn des Reiatsu par serveur
    cur.execute("""
        CREATE TABLE IF NOT EXISTS reiatsu_channels (
            guild_id TEXT PRIMARY KEY,
            channel_id TEXT NOT NULL
        );
    """)

    conn.commit()
    cur.close()
    conn.close()

# Obtenir le score d’un utilisateur
def get_reiatsu(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT score FROM reiatsu_scores WHERE user_id = %s;", (str(user_id),))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else 0

# Ajouter du Reiatsu à un utilisateur
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

# Définir le salon pour les apparitions de Reiatsu
def set_reiatsu_channel(guild_id, channel_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO reiatsu_channels (guild_id, channel_id)
        VALUES (%s, %s)
        ON CONFLICT (guild_id) DO UPDATE
        SET channel_id = EXCLUDED.channel_id;
    """, (str(guild_id), str(channel_id)))
    conn.commit()
    cur.close()
    conn.close()

# Obtenir le salon défini pour un serveur
def get_reiatsu_channel(guild_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT channel_id FROM reiatsu_channels WHERE guild_id = %s;", (str(guild_id),))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return int(row[0]) if row else None
