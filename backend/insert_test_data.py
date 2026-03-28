"""向 backend/database/database.db 写入示例数据。请先执行 init_db.py。"""
import os
import sqlite3

from werkzeug.security import generate_password_hash

BACKEND_ROOT = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BACKEND_ROOT, "database", "database.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# (登录账号, 昵称, 明文密码, 性别, 年级, 专业) — 密码在入库前哈希
users = [
    ("alice", "Alice", "alice123", "F", "大二", "计算机"),
    ("bob", "Bob", "bob123", "M", "大三", "电子信息"),
    ("cathy", "Cathy", "cathy123", "F", "大二", "计算机"),
    ("david", "David", "david123", "M", "大一", "数学"),
    ("eva", "Eva", "eva123", "F", "大三", "物理"),
]

for account, username, plain_pwd, gender, grade, major in users:
    pwd_hash = generate_password_hash(plain_pwd)
    cursor.execute(
        """
    INSERT OR IGNORE INTO users (account, username, password, gender, grade, major)
    VALUES (?, ?, ?, ?, ?, ?)
    """,
        (account, username, pwd_hash, gender, grade, major),
    )

friendships = [
    (1, 2),
    (2, 1),
    (2, 5),
    (5, 2),
    (3, 5),
    (5, 3),
]

for user_id, friend_id in friendships:
    cursor.execute(
        """
    INSERT OR IGNORE INTO friendships (user_id, friend_id)
    VALUES (?, ?)
    """,
        (user_id, friend_id),
    )

interests = [
    (1, "音乐"),
    (1, "运动"),
    (2, "运动"),
    (2, "编程"),
    (3, "音乐"),
    (3, "编程"),
    (4, "音乐"),
    (5, "运动"),
    (5, "编程"),
]

for user_id, interest in interests:
    cursor.execute(
        """
    INSERT OR IGNORE INTO user_interests (user_id, interest)
    VALUES (?, ?)
    """,
        (user_id, interest),
    )

skills = [
    (1, "Python"),
    (1, "PPT"),
    (2, "C++"),
    (2, "Python"),
    (3, "Python"),
    (3, "设计"),
    (4, "Java"),
    (5, "Python"),
    (5, "PPT"),
]

for user_id, skill in skills:
    cursor.execute(
        """
    INSERT OR IGNORE INTO user_skills (user_id, skill)
    VALUES (?, ?)
    """,
        (user_id, skill),
    )

projects = [
    (1, "大创1"),
    (1, "比赛A"),
    (2, "大创2"),
    (2, "比赛A"),
    (3, "大创1"),
    (3, "比赛B"),
    (4, "比赛A"),
    (5, "大创2"),
    (5, "比赛B"),
]

for user_id, project in projects:
    cursor.execute(
        """
    INSERT OR IGNORE INTO user_projects (user_id, project_name)
    VALUES (?, ?)
    """,
        (user_id, project),
    )

traits = [
    (1, "开朗"),
    (2, "内向"),
    (3, "开朗"),
    (4, "稳重"),
    (5, "活泼"),
]

for user_id, trait in traits:
    cursor.execute(
        """
    INSERT OR IGNORE INTO user_traits (user_id, trait)
    VALUES (?, ?)
    """,
        (user_id, trait),
    )

conn.commit()
conn.close()
print("测试数据已写入:", DB_PATH)
