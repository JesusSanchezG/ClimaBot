import sqlite3
import asyncio
from config import DB_PATH, HISTORIAL_LIMIT

def _conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    c.execute('PRAGMA journal_mode=WAL')
    return c

async def init_db():
    def _():
        conn = _conn()
        conn.executescript('''
            CREATE TABLE IF NOT EXISTS chat_state (
                chat_id INTEGER PRIMARY KEY,
                message_id INTEGER,
                menu_message_id INTEGER
            );
            CREATE TABLE IF NOT EXISTS weather_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                timestamp TEXT NOT NULL DEFAULT (datetime('now','localtime')),
                temp REAL,
                feels_like REAL,
                humidity INTEGER,
                description TEXT,
                wind_speed REAL,
                type TEXT DEFAULT 'current'
            );
            CREATE TABLE IF NOT EXISTS kv (
                key TEXT PRIMARY KEY,
                value TEXT
            );
        ''')
        cols = [r[1] for r in conn.execute('PRAGMA table_info(chat_state)')]
        if 'menu_message_id' not in cols:
            conn.execute('ALTER TABLE chat_state ADD COLUMN menu_message_id INTEGER')
        conn.commit()
        conn.close()
    await asyncio.to_thread(_)

async def get_chat_state(chat_id):
    def _():
        conn = _conn()
        row = conn.execute('SELECT * FROM chat_state WHERE chat_id = ?', (chat_id,)).fetchone()
        conn.close()
        return dict(row) if row else None
    return await asyncio.to_thread(_)

async def set_chat_state(chat_id, message_id):
    def _():
        conn = _conn()
        conn.execute('''
            INSERT INTO chat_state (chat_id, message_id)
            VALUES (?, ?)
            ON CONFLICT(chat_id) DO UPDATE SET message_id=?
        ''', (chat_id, message_id, message_id))
        conn.commit()
        conn.close()
    await asyncio.to_thread(_)

async def set_menu_state(chat_id, menu_message_id):
    def _():
        conn = _conn()
        conn.execute('''
            INSERT INTO chat_state (chat_id, message_id, menu_message_id)
            VALUES (?, NULL, ?)
            ON CONFLICT(chat_id) DO UPDATE SET message_id=NULL, menu_message_id=?
        ''', (chat_id, menu_message_id, menu_message_id))
        conn.commit()
        conn.close()
    await asyncio.to_thread(_)

async def add_history(chat_id, temp, feels_like, humidity, description, wind_speed, type_='current'):
    def _():
        conn = _conn()
        conn.execute('''
            INSERT INTO weather_history (chat_id, temp, feels_like, humidity, description, wind_speed, type)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (chat_id, temp, feels_like, humidity, description, wind_speed, type_))
        conn.execute('''
            DELETE FROM weather_history
            WHERE chat_id = ?
              AND id NOT IN (
                  SELECT id FROM weather_history
                  WHERE chat_id = ?
                  ORDER BY id DESC LIMIT ?
              )
        ''', (chat_id, chat_id, HISTORIAL_LIMIT))
        conn.commit()
        conn.close()
    await asyncio.to_thread(_)

async def get_history(chat_id, limit=10):
    def _():
        conn = _conn()
        rows = conn.execute('''
            SELECT * FROM weather_history
            WHERE chat_id = ?
            ORDER BY id DESC LIMIT ?
        ''', (chat_id, limit)).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    return await asyncio.to_thread(_)

async def get_all_chat_ids():
    def _():
        conn = _conn()
        rows = conn.execute('SELECT chat_id FROM chat_state').fetchall()
        conn.close()
        return [r['chat_id'] for r in rows]
    return await asyncio.to_thread(_)

async def kv_get(key):
    def _():
        conn = _conn()
        row = conn.execute('SELECT value FROM kv WHERE key = ?', (key,)).fetchone()
        conn.close()
        return row['value'] if row else None
    return await asyncio.to_thread(_)

async def kv_set(key, value):
    def _():
        conn = _conn()
        conn.execute('''
            INSERT INTO kv (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value
        ''', (key, str(value)))
        conn.commit()
        conn.close()
    await asyncio.to_thread(_)
