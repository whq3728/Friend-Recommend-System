import sqlite3
import random
from faker import Faker
from werkzeug.security import generate_password_hash

fake = Faker("zh_CN")

conn = sqlite3.connect("database/database.db")
cursor = conn.cursor()

USER_COUNT = 1000

# ------------------------
# ⚠️ 清空旧数据（保证实验可重复）
# ------------------------
cursor.execute("DELETE FROM friendships")
cursor.execute("DELETE FROM user_interests")
cursor.execute("DELETE FROM user_skills")
cursor.execute("DELETE FROM user_traits")
cursor.execute("DELETE FROM users")
conn.commit()

# ------------------------
# 基础属性
# ------------------------
genders = ["男", "女"]
grades = ["大一", "大二", "大三", "大四"]
majors = ["计算机", "软件工程", "人工智能", "数学", "金融", "机械"]

# ------------------------
# 兴趣（分组）
# ------------------------
interest_groups = {
    "运动": ["篮球", "足球", "跑步", "健身"],
    "艺术": ["音乐", "吉他", "绘画", "摄影"],
    "技术": ["编程", "AI", "开源", "科技"],
    "娱乐": ["游戏", "电影", "动漫", "综艺"],
    "生活": ["旅行", "美食", "阅读", "咖啡"]
}

# ------------------------
# 技能（半绑定）
# ------------------------
major_skill_map = {
    "计算机": ["Python", "后端开发", "算法"],
    "软件工程": ["Java", "系统设计", "测试"],
    "人工智能": ["机器学习", "深度学习", "数据分析"],
    "数学": ["建模", "统计", "数据分析"],
    "金融": ["Excel", "数据分析", "投资"],
    "机械": ["CAD", "制造", "工程设计"]
}

common_skills = ["PPT", "沟通", "写作", "英语"]

# ------------------------
# 性格
# ------------------------
traits_pool = ["外向", "内向", "幽默", "理性", "感性", "慢热", "社恐", "健谈"]

# ------------------------
# ✅ 1. 用户（优化：密码只生成一次）
# ------------------------
hashed_password = generate_password_hash("123456", method="pbkdf2:sha256")

user_data = []
for i in range(USER_COUNT):
    user_data.append((
        f"user{i}",
        fake.name(),
        hashed_password,
        random.choice(genders),
        random.choice(grades),
        random.choice(majors),
        fake.phone_number()
    ))

cursor.executemany("""
INSERT INTO users (account, username, password, gender, grade, major, phone)
VALUES (?, ?, ?, ?, ?, ?, ?)
""", user_data)

conn.commit()

# ------------------------
# 读取用户信息（后面用）
# ------------------------
cursor.execute("SELECT id, major FROM users")
users = cursor.fetchall()

# ------------------------
# ✅ 2. 兴趣（带圈子）
# ------------------------
interest_data = []

for user_id, _ in users:
    if random.random() < 0.8:
        group = random.choice(list(interest_groups.keys()))
        interests = random.sample(interest_groups[group], random.randint(2, 3))
    else:
        all_interests = sum(interest_groups.values(), [])
        interests = random.sample(all_interests, random.randint(2, 4))

    for interest in interests:
        interest_data.append((user_id, interest))

cursor.executemany(
    "INSERT OR IGNORE INTO user_interests (user_id, interest) VALUES (?, ?)",
    interest_data
)

conn.commit()

# ------------------------
# ✅ 3. 技能（半绑定）
# ------------------------
skill_data = []

for user_id, major in users:
    skills = []

    if random.random() < 0.7:
        skills += random.sample(major_skill_map[major], random.randint(1, 2))

    if random.random() < 0.3:
        skills += random.sample(common_skills, 1)

    skills = list(set(skills))

    for skill in skills:
        skill_data.append((user_id, skill))

cursor.executemany(
    "INSERT OR IGNORE INTO user_skills (user_id, skill) VALUES (?, ?)",
    skill_data
)

conn.commit()

# ------------------------
# ✅ 4. 性格
# ------------------------
trait_data = []

for user_id, _ in users:
    traits = random.sample(traits_pool, random.randint(1, 2))
    for t in traits:
        trait_data.append((user_id, t))

cursor.executemany(
    "INSERT OR IGNORE INTO user_traits (user_id, trait) VALUES (?, ?)",
    trait_data
)

conn.commit()

# ------------------------
# ✅ 5. 好友关系（基于兴趣相似）
# ------------------------
cursor.execute("SELECT user_id, interest FROM user_interests")
interest_map = {}

for uid, interest in cursor.fetchall():
    interest_map.setdefault(uid, set()).add(interest)

friendship_data = []

for user_id, _ in users:
    candidates = random.sample(users, 50)

    count = 0
    for other_id, _ in candidates:
        if other_id == user_id:
            continue

        common = len(interest_map[user_id] & interest_map.get(other_id, set()))
        prob = 0.1 + 0.2 * common

        if random.random() < prob:
            friendship_data.append((user_id, other_id))
            count += 1

        if count >= random.randint(5, 15):
            break

cursor.executemany("""
INSERT OR IGNORE INTO friendships (user_id, friend_id, created_at)
VALUES (?, ?, datetime('now'))
""", friendship_data)

conn.commit()
conn.close()

print("✅ 已生成 1000 条高质量模拟数据（优化版，快速）")