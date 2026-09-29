"""本地 SQLite 消息存储：去重、按群/时间查询、生成统计。"""
import sqlite3, json, os, datetime
from pathlib import Path
DB_PATH = Path(__file__).resolve().parents[2] / "data" / "wechat.db"
SCHEMA = """
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_name TEXT NOT NULL,
    sender TEXT,
    body TEXT,
    ts TEXT,
    captured_at TEXT NOT NULL,
    screen TEXT,
    fingerprint TEXT UNIQUE
);
CREATE TABLE IF NOT EXISTS captures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_name TEXT,
    captured_at TEXT NOT NULL,
    image TEXT,
    raw TEXT
);
CREATE INDEX IF NOT EXISTS idx_msg_group_ts ON messages(group_name, captured_at);
"""
def _conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB_PATH); c.row_factory = sqlite3.Row; return c
def init():
    c = _conn(); c.executescript(SCHEMA); c.commit(); c.close()
def add_capture(group_name, image_path, raw_json):
    init(); c = _conn()
    now = datetime.datetime.now().isoformat(timespec="seconds")
    c.execute("INSERT INTO captures(group_name,captured_at,image,raw) VALUES(?,?,?,?)", (group_name, now, image_path, raw_json))
    c.commit(); c.close(); return now
def add_messages(items, group_name, captured_at, screen):
    init(); c = _conn()
    before = c.total_changes; n = 0
    for it in items:
        sender = it.get("sender"); body = it.get("body"); ts = it.get("ts")
        fp = "|".join([group_name, sender or "", body or "", ts or ""])
        c.execute("INSERT OR IGNORE INTO messages(group_name,sender,body,ts,captured_at,screen,fingerprint) VALUES(?,?,?,?,?,?,?)",
                  (group_name, sender, body, ts, captured_at, screen, fp))
    n = c.total_changes - before
    c.commit(); c.close(); return n
def query_messages(group_name=None, limit=5000):
    init(); c = _conn()
    if group_name:
        rows = c.execute("SELECT * FROM messages WHERE group_name=? ORDER BY captured_at, id LIMIT ?", (group_name, limit)).fetchall()
    else:
        rows = c.execute("SELECT * FROM messages ORDER BY captured_at, id LIMIT ?", (limit,)).fetchall()
    c.close(); return [dict(r) for r in rows]
def group_names():
    init(); c = _conn(); rows = c.execute("SELECT DISTINCT group_name FROM messages").fetchall(); c.close()
    return [r[0] for r in rows if r[0]]
if __name__ == "__main__":
    init(); print("db at", DB_PATH, "groups:", group_names())
