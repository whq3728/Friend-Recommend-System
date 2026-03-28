# modules/profile.py — 个人资料、匹配隐私偏好、他人公开资料
# 资料页展示 account（只读）、username（昵称可改）；修改密码时使用哈希存储
import sqlite3

from flask import Blueprint, jsonify, request, session
from werkzeug.security import generate_password_hash

from config import DATABASE_PATH

profile_bp = Blueprint("profile", __name__)

# 多值列表表：(表名, 列名, 前端 key)
_LIST_SPECS = (
    ("user_interests", "interest", "interests"),
    ("user_skills", "skill", "skills"),
    ("user_projects", "project_name", "projects"),
    ("user_traits", "trait", "traits"),
)

_prefs_table_ok = False


def _conn():
    """获取数据库连接。"""
    return sqlite3.connect(DATABASE_PATH)


def _ensure_prefs_table(conn):
    """确保匹配偏好表存在（向后兼容）。"""
    global _prefs_table_ok
    if _prefs_table_ok:
        return
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS user_matching_prefs (
            user_id INTEGER PRIMARY KEY,
            share_interests INTEGER NOT NULL DEFAULT 1,
            share_skills INTEGER NOT NULL DEFAULT 1,
            share_friend_graph INTEGER NOT NULL DEFAULT 1
        )
        """
    )
    conn.commit()
    _prefs_table_ok = True


def load_matching_prefs(user_id):
    """加载用户的匹配隐私偏好。"""
    conn = _conn()
    _ensure_prefs_table(conn)
    c = conn.cursor()
    c.execute(
        "SELECT share_interests, share_skills, share_friend_graph FROM user_matching_prefs WHERE user_id=?",
        (user_id,),
    )
    row = c.fetchone()
    if not row:
        c.execute("INSERT INTO user_matching_prefs (user_id) VALUES (?)", (user_id,))
        conn.commit()
        row = (1, 1, 1)
    conn.close()
    return {
        "share_interests": bool(row[0]),
        "share_skills": bool(row[1]),
        "share_friend_graph": bool(row[2]),
    }


def save_matching_prefs(user_id, data):
    """保存匹配隐私偏好。"""
    share_i = 1 if data.get("share_interests", True) else 0
    share_s = 1 if data.get("share_skills", True) else 0
    share_f = 1 if data.get("share_friend_graph", True) else 0
    conn = _conn()
    _ensure_prefs_table(conn)
    c = conn.cursor()
    c.execute("SELECT user_id FROM user_matching_prefs WHERE user_id=?", (user_id,))
    if c.fetchone():
        c.execute(
            """
            UPDATE user_matching_prefs
            SET share_interests=?, share_skills=?, share_friend_graph=?
            WHERE user_id=?
            """,
            (share_i, share_s, share_f, user_id),
        )
    else:
        c.execute(
            """
            INSERT INTO user_matching_prefs (user_id, share_interests, share_skills, share_friend_graph)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, share_i, share_s, share_f),
        )
    conn.commit()
    conn.close()
    return load_matching_prefs(user_id)


def _normalize_str_list(raw, max_items=80):
    """将字符串或列表规范化为去重后的字符串列表。"""
    if raw is None:
        return []
    if isinstance(raw, str):
        items = [s.strip() for s in raw.replace(",", "\n").split("\n") if s.strip()]
    elif isinstance(raw, list):
        items = [str(x).strip() for x in raw if x is not None and str(x).strip()]
    else:
        return []
    out, seen = [], set()
    for s in items:
        if s not in seen:
            seen.add(s)
            out.append(s)
        if len(out) >= max_items:
            break
    return out


def load_profile(user_id):
    """加载完整个人资料（含 account、username、标签列表等）。"""
    conn = _conn()
    c = conn.cursor()
    c.execute(
        "SELECT id, account, username, gender, grade, major, phone FROM users WHERE id=?",
        (user_id,),
    )
    row = c.fetchone()
    if not row:
        conn.close()
        return None
    uid, account, username, gender, grade, major, phone = row
    out = {
        "id": uid,
        "account": account or "",
        "username": username or "",
        "gender": gender or "",
        "grade": grade or "",
        "major": major or "",
        "phone": phone or "",
    }
    for table, col, key in _LIST_SPECS:
        c.execute(f"SELECT {col} FROM {table} WHERE user_id=? ORDER BY id", (user_id,))
        out[key] = [r[0] for r in c.fetchall()]
    conn.close()
    return out


def _save_lists(c, user_id, data):
    """保存兴趣、技能、项目、性格等列表数据。"""
    for table, col, key in _LIST_SPECS:
        items = _normalize_str_list(data.get(key))
        c.execute(f"DELETE FROM {table} WHERE user_id=?", (user_id,))
        for item in items:
            c.execute(
                f"INSERT INTO {table} (user_id, {col}) VALUES (?,?)",
                (user_id, item),
            )


def _friends_linked(a, b):
    """判断两人是否为好友。"""
    conn = _conn()
    c = conn.cursor()
    c.execute(
        """
        SELECT 1 FROM friendships
        WHERE (user_id=? AND friend_id=?) OR (user_id=? AND friend_id=?)
        """,
        (a, b, b, a),
    )
    ok = c.fetchone() is not None
    conn.close()
    return ok


@profile_bp.route("/api/profile", methods=["GET"])
def api_profile_get():
    """获取当前用户的完整个人资料。"""
    if "user_id" not in session:
        return jsonify({"error": "未登录"}), 401
    p = load_profile(session["user_id"])
    if not p:
        return jsonify({"error": "用户不存在"}), 404
    return jsonify(p)


@profile_bp.route("/api/profile", methods=["PUT"])
def api_profile_put():
    """
    更新个人资料。
    account 不可修改；username 可改，不能与其他用户重复；密码可选，修改时哈希存储。
    """
    if "user_id" not in session:
        return jsonify({"error": "未登录"}), 401
    user_id = session["user_id"]
    data = request.get_json(silent=True) or {}

    username = (data.get("username") or "").strip()
    if not username:
        return jsonify({"error": "昵称不能为空"}), 400
    if len(username) > 64:
        return jsonify({"error": "昵称过长"}), 400

    gender = (data.get("gender") or "").strip() or None
    grade = (data.get("grade") or "").strip() or None
    major = (data.get("major") or "").strip() or None
    phone = (data.get("phone") or "").strip().replace(" ", "") or None
    for label, val in (("性别", gender), ("年级", grade), ("专业", major)):
        if val and len(val) > 128:
            return jsonify({"error": f"{label}内容过长"}), 400
    if phone and len(phone) > 20:
        return jsonify({"error": "手机号过长"}), 400

    new_password = None
    password = data.get("password")
    if password is not None and str(password).strip() != "":
        new_password = str(password).strip()
        if len(new_password) < 4:
            return jsonify({"error": "新密码至少 4 位"}), 400
        if len(new_password) > 128:
            return jsonify({"error": "密码过长"}), 400

    conn = _conn()
    try:
        c = conn.cursor()
        # 昵称唯一性检查（不含当前用户）
        c.execute("SELECT id FROM users WHERE username=? AND id!=?", (username, user_id))
        if c.fetchone():
            conn.close()
            return jsonify({"error": "该昵称已被其他账号使用"}), 400
        if phone:
            c.execute(
                "SELECT id FROM users WHERE phone=? AND id!=? AND phone IS NOT NULL AND phone != ''",
                (phone, user_id),
            )
            if c.fetchone():
                conn.close()
                return jsonify({"error": "该手机号已被其他账号绑定"}), 400

        if new_password is not None:
            pwd_hash = generate_password_hash(new_password)
            c.execute(
                """
                UPDATE users SET username=?, password=?, gender=?, grade=?, major=?, phone=?
                WHERE id=?
                """,
                (username, pwd_hash, gender, grade, major, phone, user_id),
            )
        else:
            c.execute(
                """
                UPDATE users SET username=?, gender=?, grade=?, major=?, phone=?
                WHERE id=?
                """,
                (username, gender, grade, major, phone, user_id),
            )
        _save_lists(c, user_id, data)
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        conn.close()
        return jsonify({"error": f"保存失败：{e}"}), 500
    conn.close()

    return jsonify(load_profile(user_id))


@profile_bp.route("/api/matching-prefs", methods=["GET"])
def api_matching_prefs_get():
    """获取匹配隐私偏好。"""
    if "user_id" not in session:
        return jsonify({"error": "未登录"}), 401
    return jsonify(load_matching_prefs(session["user_id"]))


@profile_bp.route("/api/matching-prefs", methods=["PUT"])
def api_matching_prefs_put():
    """更新匹配隐私偏好。"""
    if "user_id" not in session:
        return jsonify({"error": "未登录"}), 401
    data = request.get_json(silent=True) or {}
    prefs = save_matching_prefs(
        session["user_id"],
        {
            "share_interests": bool(data.get("share_interests", True)),
            "share_skills": bool(data.get("share_skills", True)),
            "share_friend_graph": bool(data.get("share_friend_graph", True)),
        },
    )
    return jsonify(prefs)


@profile_bp.route("/api/users/<int:uid>/public")
def api_user_public(uid):
    """
    获取用户公开资料。
    本人返回完整资料；好友返回完整；陌生人仅返回基础信息与标签数量。
    """
    if "user_id" not in session:
        return jsonify({"error": "未登录"}), 401
    viewer = session["user_id"]
    conn = _conn()
    c = conn.cursor()
    c.execute(
        "SELECT id, account, username, gender, grade, major FROM users WHERE id=?",
        (uid,),
    )
    row = c.fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "用户不存在"}), 404
    _, account, username, gender, grade, major = row

    c.execute("SELECT COUNT(*) FROM user_interests WHERE user_id=?", (uid,))
    ic = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM user_skills WHERE user_id=?", (uid,))
    sc = c.fetchone()[0]
    conn.close()

    if viewer == uid:
        full = load_profile(uid)
        return jsonify({"relation": "self", **full})

    if _friends_linked(viewer, uid):
        full = load_profile(uid)
        return jsonify(
            {
                "relation": "friend",
                "id": full["id"],
                "account": full["account"],
                "username": full["username"],
                "gender": full["gender"],
                "grade": full["grade"],
                "major": full["major"],
                "interests": full["interests"],
                "skills": full["skills"],
                "projects": full["projects"],
                "traits": full["traits"],
            }
        )

    return jsonify(
        {
            "relation": "stranger",
            "id": uid,
            "username": username,
            "gender": gender or "",
            "grade": grade or "",
            "major": major or "",
            "stats": {"interest_count": ic, "skill_count": sc},
            "privacy_note": "非好友仅展示基础信息与标签数量，具体兴趣/技能在建立好友关系后可见。",
        }
    )
