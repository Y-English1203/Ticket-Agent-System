import sqlite3

conn = sqlite3.connect("tickets.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    issue TEXT,
    priority TEXT,
    status TEXT DEFAULT '待处理',
    created_at TEXT,
    updated_at TEXT,
    handler TEXT DEFAULT 'AI'
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER,
    action TEXT,
    operator TEXT,
    timestamp TEXT
)
""")

conn.commit()
conn.close()
print("工单数据库初始化完成")