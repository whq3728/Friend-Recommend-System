import sqlite3
import random
import os
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), "database", "database.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# =========================
# 基础数据池
# =========================

majors = ["计算机", "软件工程", "人工智能", "通信工程", "电子信息", "自动化"]
grades = ["大一", "大二", "大三", "大四"]
genders = ["男", "女"]

interests_pool = {
    "娱乐": ["游戏", "音乐", "电影", "动漫"],
    "运动": ["篮球", "足球", "健身"],
    "技术": ["编程", "机器学习", "数据分析"],
    "生活": ["美食", "旅行", "摄影"]
}


skills_pool = [
    "Python", "Java", "C++", "前端开发", "后端开发",
    "机器学习", "数据分析", "UI设计", "产品设计"
]

traits_pool = [
    "外向", "内向", "理性", "感性",
    "幽默", "认真", "随和", "独立"
]

# =========================
# 工具函数
# =========================

def gen_bigfive():
    return (
        round(random.uniform(0.2, 0.9), 2),  # extro
        round(random.uniform(0.3, 0.9), 2),  # agree
        round(random.uniform(0.3, 0.9), 2),  # cons
        round(random.uniform(0.1, 0.7), 2),  # neuro
        round(random.uniform(0.3, 0.9), 2),  # open
    )

def jaccard(a, b):
    if not a or not b:
        return 0
    return len(a & b) / len(a | b)

def gen_interests(openness):
    k = int(3 + openness * 4)
    return set(random.sample(interests_pool, min(k, len(interests_pool))))

def gen_skills(conscientiousness):
    k = int(2 + conscientiousness * 3)
    return random.sample(skills_pool, min(k, len(skills_pool)))

# =========================
# 清空旧数据（可选）
# =========================

print("清空旧数据...")

tables = [
    "users", "friendships", "user_interests", "user_skills",
    "user_traits", "user_personality_bigfive",
    "friend_requests", "messages"
]

for t in tables:
    cursor.execute(f"DELETE FROM {t}")

conn.commit()

# =========================
# 1. 生成用户 + BigFive
# =========================

USER_COUNT = 200

print("生成用户 + 性格...")

user_bigfive = {}

for i in range(USER_COUNT):
    account = f"user{i}"
    username = f"用户{i}"
    password = generate_password_hash("123456")

    gender = random.choice(genders)
    grade = random.choice(grades)
    major = random.choice(majors)

    cursor.execute("""
    INSERT INTO users (account, username, password, gender, grade, major)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (account, username, password, gender, grade, major))

    uid = cursor.lastrowid

    bf = gen_bigfive()
    user_bigfive[uid] = bf

    cursor.execute("""
    INSERT INTO user_personality_bigfive
    VALUES (?, ?, ?, ?, ?, ?)
    """, (uid, *bf))

conn.commit()

user_ids = list(user_bigfive.keys())

# =========================
# 2. 兴趣（受 openness 控制）
# =========================

print("生成兴趣（性格驱动）...")

user_interests_map = {}

for uid in user_ids:
    openness = user_bigfive[uid][4]

    interests = gen_interests(openness)
    user_interests_map[uid] = interests

    for it in interests:
        cursor.execute("""
        INSERT INTO user_interests (user_id, interest)
        VALUES (?, ?)
        """, (uid, it))

conn.commit()

# =========================
# 3. 技能（受 conscientiousness 控制）
# =========================

print("生成技能...")

for uid in user_ids:
    cons = user_bigfive[uid][2]
    skills = gen_skills(cons)

    for sk in skills:
        cursor.execute("""
        INSERT INTO user_skills (user_id, skill)
        VALUES (?, ?)
        """, (uid, sk))

conn.commit()

# =========================
# 4. 性格标签
# =========================

print("生成性格标签...")

for uid in user_ids:
    traits = random.sample(traits_pool, k=random.randint(2, 4))

    for t in traits:
        cursor.execute("""
        INSERT INTO user_traits (user_id, trait)
        VALUES (?, ?)
        """, (uid, t))

conn.commit()

# =========================
# 5. 好友关系（核心🔥）
# =========================

print("生成好友关系（兴趣 + 性格驱动）...")

for uid in user_ids:
    my_interests = user_interests_map[uid]

    extro, agree = user_bigfive[uid][0], user_bigfive[uid][1]

    target_friends = int(5 + extro * 15)

    candidates = []

    for other in user_ids:
        if uid == other:
            continue

        sim = jaccard(my_interests, user_interests_map[other])

        # 综合概率
        prob = sim * 0.7 + agree * 0.3

        if random.random() < prob:
            candidates.append((other, sim))

    # 选最相似的
    candidates.sort(key=lambda x: x[1], reverse=True)
    friends = [x[0] for x in candidates[:target_friends]]

    for fid in friends:
        created_at = datetime.now() - timedelta(days=random.randint(1, 365))

        cursor.execute("""
        INSERT OR IGNORE INTO friendships (user_id, friend_id, created_at)
        VALUES (?, ?, ?)
        """, (uid, fid, created_at.strftime("%Y-%m-%d %H:%M:%S")))

        cursor.execute("""
        INSERT OR IGNORE INTO friendships (user_id, friend_id, created_at)
        VALUES (?, ?, ?)
        """, (fid, uid, created_at.strftime("%Y-%m-%d %H:%M:%S")))

conn.commit()

# =========================
# 6. 好友请求
# =========================

print("生成好友请求...")

for _ in range(300):
    u1, u2 = random.sample(user_ids, 2)

    status = random.choice(["pending", "accepted", "rejected"])

    cursor.execute("""
    INSERT OR IGNORE INTO friend_requests (from_id, to_id, status)
    VALUES (?, ?, ?)
    """, (u1, u2, status))

conn.commit()

# =========================
# 7. 聊天记录
# =========================

print("生成聊天记录...")

msgs = ["你好", "在吗", "一起打游戏吗", "哈哈哈", "这个不错", "吃了吗"]

for _ in range(1000):
    u1, u2 = random.sample(user_ids, 2)

    cursor.execute("""
    INSERT INTO messages (sender_id, receiver_id, body)
    VALUES (?, ?, ?)
    """, (u1, u2, random.choice(msgs)))

conn.commit()

conn.close()

print("✅ 高质量测试数据生成完成！")