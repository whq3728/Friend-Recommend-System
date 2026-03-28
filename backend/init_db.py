"""
数据库初始化脚本。

在 backend 目录执行: python init_db.py

创建所有表；若 users 表为旧 schema（无 account 列），会自动迁移到新结构，
并将明文密码转为 werkzeug 哈希存储。
"""
import os
import sqlite3

from werkzeug.security import generate_password_hash

BACKEND_ROOT = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BACKEND_ROOT, "database", "database.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# ---------------------------------------------------------------------------
# 用户表：account 用于登录，username 为昵称/显示名，password 存哈希
# ---------------------------------------------------------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account TEXT UNIQUE NOT NULL,
    username TEXT NOT NULL,
    password TEXT NOT NULL,
    gender TEXT,
    grade TEXT,
    major TEXT,
    phone TEXT
)
""")

# ---------------------------------------------------------------------------
# 好友关系表（created_at 记录成为好友时间）
# ---------------------------------------------------------------------------
cursor.execute(""" 
CREATE TABLE IF NOT EXISTS friendships (
    user_id INTEGER NOT NULL,
    friend_id INTEGER NOT NULL,
    created_at TEXT,
    UNIQUE(user_id, friend_id)
)
""")

# 若旧表无 created_at，添加该列
cursor.execute("PRAGMA table_info(friendships)")
fs_cols = {r[1] for r in cursor.fetchall()}
if "created_at" not in fs_cols:
    cursor.execute("ALTER TABLE friendships ADD COLUMN created_at TEXT")
    cursor.execute("UPDATE friendships SET created_at = datetime('now') WHERE created_at IS NULL")

# ---------------------------------------------------------------------------
# 兴趣标签表
# ---------------------------------------------------------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS user_interests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    interest TEXT NOT NULL,
    UNIQUE(user_id, interest)
)
""")

# ---------------------------------------------------------------------------
# 技能表（组队推荐用）
# ---------------------------------------------------------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS user_skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    skill TEXT NOT NULL,
    UNIQUE(user_id, skill)
)
""")

# ---------------------------------------------------------------------------
# 项目/比赛经历表
# ---------------------------------------------------------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS user_projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    project_name TEXT NOT NULL,
    UNIQUE(user_id, project_name)
)
""")

# ---------------------------------------------------------------------------
# 性格标签表（恋爱推荐用）
# ---------------------------------------------------------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS user_traits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    trait TEXT NOT NULL,
    UNIQUE(user_id, trait)
)
""")

# ---------------------------------------------------------------------------
# 匹配隐私偏好（控制哪些维度参与推荐）
# ---------------------------------------------------------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS user_matching_prefs (
    user_id INTEGER PRIMARY KEY,
    share_interests INTEGER NOT NULL DEFAULT 1,
    share_skills INTEGER NOT NULL DEFAULT 1,
    share_friend_graph INTEGER NOT NULL DEFAULT 1
)
""")

# ---------------------------------------------------------------------------
# 好友请求表
# ---------------------------------------------------------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS friend_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_id INTEGER NOT NULL,
    to_id INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(from_id, to_id)
)
""")

# ---------------------------------------------------------------------------
# 推荐记录表（每次推荐页刷新时写入快照）
# ---------------------------------------------------------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS recommendation_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    mode TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    snapshot_json TEXT NOT NULL
)
""")

# ---------------------------------------------------------------------------
# 私信表（好友间聊天）
# ---------------------------------------------------------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id INTEGER NOT NULL,
    receiver_id INTEGER NOT NULL,
    body TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
)
""")

# ---------------------------------------------------------------------------
# 迁移：若 users 为旧 schema（无 account 列），升级并哈希密码
# ---------------------------------------------------------------------------
cursor.execute("PRAGMA table_info(users)")
cols = [r[1] for r in cursor.fetchall()]
if "account" not in cols:
    cursor.execute("""
        CREATE TABLE users_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account TEXT UNIQUE NOT NULL,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            gender TEXT,
            grade TEXT,
            major TEXT
        )
    """)
    cursor.execute("PRAGMA table_info(users)")
    old_cols = {r[1] for r in cursor.fetchall()}
    sel = ["id", "username", "password"]
    for c in ("gender", "grade", "major"):
        if c in old_cols:
            sel.append(c)
    cursor.execute(f"SELECT {', '.join(sel)} FROM users")
    for row in cursor.fetchall():
        uid, username, pwd = row[0], row[1], row[2]
        gender = row[3] if len(row) > 3 else None
        grade = row[4] if len(row) > 4 else None
        major = row[5] if len(row) > 5 else None
        # 若已是哈希格式（pbkdf2/scrypt 等）则不再处理
        pwd_hash = pwd if (pwd and (pwd.startswith("pbkdf2:") or pwd.startswith("scrypt:"))) else generate_password_hash(pwd or "")
        cursor.execute(
            "INSERT INTO users_new (id, account, username, password, gender, grade, major) VALUES (?,?,?,?,?,?,?)",
            (uid, username, username, pwd_hash, gender, grade, major),
        )
    cursor.execute("DROP TABLE users")
    cursor.execute("ALTER TABLE users_new RENAME TO users")
    print("已迁移 users 表到新结构，密码已哈希")

# 手机号（可选，用于演示验证码登录 / 找回密码）
cursor.execute("PRAGMA table_info(users)")
_user_cols = {r[1] for r in cursor.fetchall()}
if "phone" not in _user_cols:
    cursor.execute("ALTER TABLE users ADD COLUMN phone TEXT")

conn.commit()
conn.close()
print("数据库已就绪:", DB_PATH)
