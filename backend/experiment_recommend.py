"""多场景推荐实验日志（在 backend 目录执行: python experiment_recommend.py）"""
import os
import sys

BACKEND_ROOT = os.path.dirname(os.path.abspath(__file__))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

import sqlite3

from modules.psi import psi_intersection
from modules.recommend import get_recommendations_multi

TOP_N = 3
MODES = ["friend", "team", "love"]

DB_PATH = os.path.join(BACKEND_ROOT, "database", "database.db")
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("SELECT id, username FROM users")
users = cursor.fetchall()

log_lines = ["==== 多场景推荐实验日志开始 ===="]

for user_id, username in users:
    log_lines.append(f"\n用户 {user_id} - {username}")

    cursor.execute("SELECT friend_id FROM friendships WHERE user_id=?", (user_id,))
    user_friends = set(row[0] for row in cursor.fetchall())
    cursor.execute("SELECT interest FROM user_interests WHERE user_id=?", (user_id,))
    user_interests = set(row[0] for row in cursor.fetchall())
    cursor.execute("SELECT skill FROM user_skills WHERE user_id=?", (user_id,))
    user_skills = set(row[0] for row in cursor.fetchall())

    for mode in MODES:
        recs = get_recommendations_multi(user_id, mode=mode, top_n=TOP_N, output_mode="full_score")
        log_lines.append(f"  模式 {mode.upper()} 推荐:")

        for r_id, score in recs:
            cursor.execute("SELECT username FROM users WHERE id=?", (r_id,))
            row = cursor.fetchone()
            r_name = row[0] if row else f"未知用户({r_id})"

            cursor.execute("SELECT friend_id FROM friendships WHERE user_id=?", (r_id,))
            other_friends = set(row[0] for row in cursor.fetchall())
            cursor.execute("SELECT interest FROM user_interests WHERE user_id=?", (r_id,))
            other_interests = set(row[0] for row in cursor.fetchall())
            cursor.execute("SELECT skill FROM user_skills WHERE user_id=?", (r_id,))
            other_skills = set(row[0] for row in cursor.fetchall())

            friend_inter = psi_intersection(user_friends, other_friends)
            interest_inter = psi_intersection(user_interests, other_interests)
            skill_inter = psi_intersection(user_skills, other_skills)

            log_lines.append(
                f"    推荐用户 {r_id} - {r_name} | 好友交集={len(friend_inter)}, "
                f"兴趣交集={len(interest_inter)}, 技能交集={len(skill_inter)} | 综合分数={score:.3f}"
            )

    log_lines.append("-" * 50)

log_lines.append("==== 多场景推荐实验日志结束 ====")

out_path = os.path.join(BACKEND_ROOT, "experiment_log.txt")
with open(out_path, "w", encoding="utf-8") as f:
    f.write("\n".join(log_lines))

print("实验日志已生成:", out_path)
conn.close()
