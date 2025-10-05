import sqlite3
import threading

DB_PATH = "user_tokens.db"
_lock = threading.Lock()

def _init_db():
    with _lock:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS user_tokens (
                user_id INTEGER PRIMARY KEY,  -- Telegram user_id
                username TEXT,
                token TEXT,
                user_uuid TEXT  -- UUID из API
            )
        ''')
        conn.commit()
        conn.close()

def setup():
    _init_db()

def set_token(user_id, username, token):
    with _lock:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
            INSERT INTO user_tokens (user_id, username, token)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET username=?, token=?
        ''', (user_id, username, token, username, token))
        conn.commit()
        conn.close()

def set_user_id(user_id, user_uuid):
    with _lock:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
            UPDATE user_tokens SET user_uuid=? WHERE user_id=?
        ''', (user_uuid, user_id))
        conn.commit()
        conn.close()

def get_token(user_id):
    with _lock:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT token FROM user_tokens WHERE user_id=?', (user_id,))
        row = c.fetchone()
        conn.close()
        return row[0] if row else None

def get_user_id(user_id):
    with _lock:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT user_uuid FROM user_tokens WHERE user_id=?', (user_id,))
        row = c.fetchone()
        conn.close()
        return row[0] if row else None

def clear_token(user_id):
    with _lock:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('DELETE FROM user_tokens WHERE user_id=?', (user_id,))
        conn.commit()
        conn.close()