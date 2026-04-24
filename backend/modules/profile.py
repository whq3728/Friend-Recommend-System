# modules/profile.py — 个人资料、匹配隐私偏好、他人公开资料
# 资料页展示 account（只读）、username（昵称可改）；修改密码时使用哈希存储
import sqlite3

from flask import Blueprint, jsonify, request, session
from werkzeug.security import generate_password_hash

from config import DATABASE_PATH
from modules.personality import (
    DIM_KEYS,
    bigfive_from_questionnaire_1to5,
    bigfive_from_quick_1to5,
    ensure_personality_table,
    upsert_personality_bigfive,
)

profile_bp = Blueprint("profile", __name__)

# 多值列表表：(表名, 列名, 前端 key)
_LIST_SPECS = (
    ("user_interests", "interest", "interests"),
    ("user_skills", "skill", "skills"),
    ("user_projects", "project_name", "projects"),
    ("user_traits", "trait", "traits"),
)

# 隐私可见性设置字段定义
_STRANGER_VISIBILITY_FIELDS = [
    "show_gender", "show_grade", "show_major",
    "show_interests", "show_skills", "show_projects", "show_personality"
]

_FRIEND_VISIBILITY_FIELDS = [
    "show_phone", "show_gender", "show_grade", "show_major",
    "show_interests", "show_skills", "show_projects", "show_personality"
]

_FRIEND_OVERRIDE_FIELDS = _FRIEND_VISIBILITY_FIELDS

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
            share_friend_graph INTEGER NOT NULL DEFAULT 1,
            share_personality INTEGER NOT NULL DEFAULT 1
        )
        """
    )
    try:
        conn.execute("ALTER TABLE user_matching_prefs ADD COLUMN share_personality INTEGER NOT NULL DEFAULT 1")
        conn.commit()
    except sqlite3.OperationalError:
        pass

    # 陌生人可见设置表
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_stranger_visibility (
            user_id INTEGER PRIMARY KEY,
            show_gender INTEGER NOT NULL DEFAULT 1,
            show_grade INTEGER NOT NULL DEFAULT 1,
            show_major INTEGER NOT NULL DEFAULT 1,
            show_interests INTEGER NOT NULL DEFAULT 1,
            show_skills INTEGER NOT NULL DEFAULT 1,
            show_projects INTEGER NOT NULL DEFAULT 0,
            show_personality INTEGER NOT NULL DEFAULT 0
        )
    """)

    # 好友可见设置表（全局默认）
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_friend_visibility (
            user_id INTEGER PRIMARY KEY,
            show_phone INTEGER NOT NULL DEFAULT 0,
            show_gender INTEGER NOT NULL DEFAULT 1,
            show_grade INTEGER NOT NULL DEFAULT 1,
            show_major INTEGER NOT NULL DEFAULT 1,
            show_interests INTEGER NOT NULL DEFAULT 1,
            show_skills INTEGER NOT NULL DEFAULT 1,
            show_projects INTEGER NOT NULL DEFAULT 1,
            show_personality INTEGER NOT NULL DEFAULT 1
        )
    """)

    # 好友独立隐私覆盖表
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_friend_privacy_override (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            friend_id INTEGER NOT NULL,
            show_phone INTEGER,
            show_gender INTEGER,
            show_grade INTEGER,
            show_major INTEGER,
            show_interests INTEGER,
            show_skills INTEGER,
            show_projects INTEGER,
            show_personality INTEGER,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(user_id, friend_id)
        )
    """)

    _prefs_table_ok = True


def load_matching_prefs(user_id):
    """加载用户的匹配隐私偏好。"""
    conn = _conn()
    _ensure_prefs_table(conn)
    c = conn.cursor()
    c.execute(
        "SELECT share_interests, share_skills, share_friend_graph, share_personality FROM user_matching_prefs WHERE user_id=?",
        (user_id,),
    )
    row = c.fetchone()
    if not row:
        c.execute("INSERT INTO user_matching_prefs (user_id) VALUES (?)", (user_id,))
        conn.commit()
        row = (1, 1, 1, 1)
    conn.close()
    return {
        "share_interests": bool(row[0]),
        "share_skills": bool(row[1]),
        "share_friend_graph": bool(row[2]),
        "share_personality": bool(row[3]),
    }


def save_matching_prefs(user_id, data):
    """保存匹配隐私偏好。"""
    share_i = 1 if data.get("share_interests", True) else 0
    share_s = 1 if data.get("share_skills", True) else 0
    share_f = 1 if data.get("share_friend_graph", True) else 0
    share_p = 1 if data.get("share_personality", True) else 0
    conn = _conn()
    _ensure_prefs_table(conn)
    c = conn.cursor()
    c.execute("SELECT user_id FROM user_matching_prefs WHERE user_id=?", (user_id,))
    if c.fetchone():
        c.execute(
            """
            UPDATE user_matching_prefs
            SET share_interests=?, share_skills=?, share_friend_graph=?, share_personality=?
            WHERE user_id=?
            """,
            (share_i, share_s, share_f, share_p, user_id),
        )
    else:
        c.execute(
            """
            INSERT INTO user_matching_prefs (user_id, share_interests, share_skills, share_friend_graph, share_personality)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, share_i, share_s, share_f, share_p),
        )
    conn.commit()
    conn.close()
    return load_matching_prefs(user_id)


def _default_stranger_visibility():
    """返回陌生人可见设置的默认值。"""
    return {
        "show_gender": True,
        "show_grade": True,
        "show_major": True,
        "show_interests": True,
        "show_skills": True,
        "show_projects": False,
        "show_personality": False,
    }


def _default_friend_visibility():
    """返回好友可见设置的默认值。"""
    return {
        "show_phone": False,
        "show_gender": True,
        "show_grade": True,
        "show_major": True,
        "show_interests": True,
        "show_skills": True,
        "show_projects": True,
        "show_personality": True,
    }


def load_stranger_visibility(user_id):
    """加载陌生人的可见设置。"""
    conn = _conn()
    _ensure_prefs_table(conn)
    c = conn.cursor()
    c.execute(
        """
        SELECT show_gender, show_grade, show_major, show_interests, show_skills, show_projects, show_personality
        FROM user_stranger_visibility WHERE user_id=?
        """,
        (user_id,),
    )
    row = c.fetchone()
    if not row:
        conn.close()
        return _default_stranger_visibility()
    conn.close()
    return {
        "show_gender": bool(row[0]),
        "show_grade": bool(row[1]),
        "show_major": bool(row[2]),
        "show_interests": bool(row[3]),
        "show_skills": bool(row[4]),
        "show_projects": bool(row[5]),
        "show_personality": bool(row[6]),
    }


def save_stranger_visibility(user_id, data):
    """保存陌生人可见设置。"""
    defaults = _default_stranger_visibility()
    values = {}
    for field in _STRANGER_VISIBILITY_FIELDS:
        values[field] = 1 if data.get(field, defaults[field]) else 0

    conn = _conn()
    _ensure_prefs_table(conn)
    c = conn.cursor()
    c.execute("SELECT user_id FROM user_stranger_visibility WHERE user_id=?", (user_id,))
    if c.fetchone():
        c.execute(
            """
            UPDATE user_stranger_visibility
            SET show_gender=?, show_grade=?, show_major=?, show_interests=?, show_skills=?, show_projects=?, show_personality=?
            WHERE user_id=?
            """,
            (values["show_gender"], values["show_grade"], values["show_major"],
             values["show_interests"], values["show_skills"], values["show_projects"],
             values["show_personality"], user_id),
        )
    else:
        c.execute(
            """
            INSERT INTO user_stranger_visibility (user_id, show_gender, show_grade, show_major, show_interests, show_skills, show_projects, show_personality)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, values["show_gender"], values["show_grade"], values["show_major"],
             values["show_interests"], values["show_skills"], values["show_projects"],
             values["show_personality"]),
        )
    conn.commit()
    conn.close()
    return load_stranger_visibility(user_id)


def load_friend_visibility(user_id):
    """加载好友可见设置（全局默认）。"""
    conn = _conn()
    _ensure_prefs_table(conn)
    c = conn.cursor()
    c.execute(
        """
        SELECT show_phone, show_gender, show_grade, show_major, show_interests, show_skills, show_projects, show_personality
        FROM user_friend_visibility WHERE user_id=?
        """,
        (user_id,),
    )
    row = c.fetchone()
    if not row:
        conn.close()
        return _default_friend_visibility()
    conn.close()
    return {
        "show_phone": bool(row[0]),
        "show_gender": bool(row[1]),
        "show_grade": bool(row[2]),
        "show_major": bool(row[3]),
        "show_interests": bool(row[4]),
        "show_skills": bool(row[5]),
        "show_projects": bool(row[6]),
        "show_personality": bool(row[7]),
    }


def save_friend_visibility(user_id, data):
    """保存好友可见设置（全局默认）。"""
    defaults = _default_friend_visibility()
    values = {}
    for field in _FRIEND_VISIBILITY_FIELDS:
        values[field] = 1 if data.get(field, defaults[field]) else 0

    conn = _conn()
    _ensure_prefs_table(conn)
    c = conn.cursor()
    c.execute("SELECT user_id FROM user_friend_visibility WHERE user_id=?", (user_id,))
    if c.fetchone():
        c.execute(
            """
            UPDATE user_friend_visibility
            SET show_phone=?, show_gender=?, show_grade=?, show_major=?, show_interests=?, show_skills=?, show_projects=?, show_personality=?
            WHERE user_id=?
            """,
            (values["show_phone"], values["show_gender"], values["show_grade"], values["show_major"],
             values["show_interests"], values["show_skills"], values["show_projects"], values["show_personality"], user_id),
        )
    else:
        c.execute(
            """
            INSERT INTO user_friend_visibility (user_id, show_phone, show_gender, show_grade, show_major, show_interests, show_skills, show_projects, show_personality)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, values["show_phone"], values["show_gender"], values["show_grade"], values["show_major"],
             values["show_interests"], values["show_skills"], values["show_projects"], values["show_personality"]),
        )
    conn.commit()
    conn.close()
    return load_friend_visibility(user_id)


def load_friend_visibility_override(user_id, friend_id):
    """加载针对特定好友的可见覆盖设置（如果有）。"""
    conn = _conn()
    _ensure_prefs_table(conn)
    c = conn.cursor()
    c.execute(
        """
        SELECT show_phone, show_gender, show_grade, show_major, show_interests, show_skills, show_projects, show_personality
        FROM user_friend_privacy_override WHERE user_id=? AND friend_id=?
        """,
        (user_id, friend_id),
    )
    row = c.fetchone()
    if not row:
        conn.close()
        return None
    result = {
        "friend_id": friend_id,
        "show_phone": bool(row[0]) if row[0] is not None else None,
        "show_gender": bool(row[1]) if row[1] is not None else None,
        "show_grade": bool(row[2]) if row[2] is not None else None,
        "show_major": bool(row[3]) if row[3] is not None else None,
        "show_interests": bool(row[4]) if row[4] is not None else None,
        "show_skills": bool(row[5]) if row[5] is not None else None,
        "show_projects": bool(row[6]) if row[6] is not None else None,
        "show_personality": bool(row[7]) if row[7] is not None else None,
    }
    conn.close()
    return result


def load_all_friend_overrides(user_id):
    """加载用户所有好友独立隐私设置。"""
    conn = _conn()
    _ensure_prefs_table(conn)
    c = conn.cursor()
    c.execute(
        """
        SELECT friend_id, show_phone, show_gender, show_grade, show_major, show_interests, show_skills, show_projects, show_personality
        FROM user_friend_privacy_override WHERE user_id=?
        """,
        (user_id,),
    )
    rows = c.fetchall()
    conn.close()
    result = {}
    for row in rows:
        result[row[0]] = {
            "friend_id": row[0],
            "show_phone": bool(row[1]) if row[1] is not None else None,
            "show_gender": bool(row[2]) if row[2] is not None else None,
            "show_grade": bool(row[3]) if row[3] is not None else None,
            "show_major": bool(row[4]) if row[4] is not None else None,
            "show_interests": bool(row[5]) if row[5] is not None else None,
            "show_skills": bool(row[6]) if row[6] is not None else None,
            "show_projects": bool(row[7]) if row[7] is not None else None,
            "show_personality": bool(row[8]) if row[8] is not None else None,
        }
    return result


def save_friend_visibility_override(user_id, friend_id, data):
    """保存针对特定好友的可见覆盖设置。"""
    conn = _conn()
    _ensure_prefs_table(conn)
    c = conn.cursor()

    fields = []
    values_list = []
    for field in _FRIEND_OVERRIDE_FIELDS:
        val = data.get(field)
        if val is None:
            fields.append(field)
            values_list.append(None)
        else:
            fields.append(field)
            values_list.append(1 if val else 0)

    c.execute("SELECT id FROM user_friend_privacy_override WHERE user_id=? AND friend_id=?", (user_id, friend_id))
    if c.fetchone():
        set_clause = ", ".join([f"{f}=?" for f in fields])
        values_list.extend([user_id, friend_id])
        c.execute(f"UPDATE user_friend_privacy_override SET {set_clause} WHERE user_id=? AND friend_id=?", values_list)
    else:
        placeholders = ", ".join(["?"] * (len(fields) + 2))
        all_values = [user_id, friend_id] + values_list
        c.execute(
            f"INSERT INTO user_friend_privacy_override (user_id, friend_id, {', '.join(fields)}) VALUES ({placeholders})",
            all_values,
        )
    conn.commit()
    conn.close()
    return load_friend_visibility_override(user_id, friend_id)


def delete_friend_visibility_override(user_id, friend_id):
    """删除针对特定好友的可见覆盖设置（恢复默认）。"""
    conn = _conn()
    _ensure_prefs_table(conn)
    c = conn.cursor()
    c.execute("DELETE FROM user_friend_privacy_override WHERE user_id=? AND friend_id=?", (user_id, friend_id))
    conn.commit()
    conn.close()


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
    ensure_personality_table()
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
        "personality_filled": False,
        "bigfive": None,
    }

    # Big Five 性格向量（0..1）
    try:
        c.execute(
            """
            SELECT extro, agreeableness, conscientiousness, neuroticism, openness
            FROM user_personality_bigfive
            WHERE user_id=?
            """,
            (user_id,),
        )
        p_row = c.fetchone()
        if p_row:
            out["personality_filled"] = True
            out["bigfive"] = {k: float(p_row[i]) for i, k in enumerate(DIM_KEYS)}
    except sqlite3.Error:
        # 兼容旧库：表不存在时，保持为未填写状态
        pass
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
    性格测试可单独更新（不传其他字段时只更新性格数据）。
    """
    if "user_id" not in session:
        return jsonify({"error": "未登录"}), 401
    user_id = session["user_id"]
    data = request.get_json(silent=True) or {}

    # 判断是否传递了 username 字段
    has_username_field = "username" in data
    username = (data.get("username") or "").strip()
    if has_username_field and not username:
        return jsonify({"error": "昵称不能为空"}), 400
    if username and len(username) > 64:
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
        
        # 如果没有传递 username，从数据库获取原有值
        if not username:
            c.execute("SELECT username FROM users WHERE id=?", (user_id,))
            row = c.fetchone()
            username = row[0] if row else ""
        
        # 昵称唯一性检查（不含当前用户）
        if username:
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

    # ---------------------------
    # Big Five 性格建模（可选）
    # ---------------------------
    personality_mode = (data.get("personality_mode") or "").strip()
    bigfive_quick = data.get("bigfive_quick") or {}
    bigfive_answers = data.get("bigfive_answers") or []
    if personality_mode in ("quick", "questionnaire"):
        try:
            if personality_mode == "quick":
                vec = bigfive_from_quick_1to5(bigfive_quick)
            else:
                vec = bigfive_from_questionnaire_1to5(list(bigfive_answers))
            upsert_personality_bigfive(user_id, vec)
        except ValueError as e:
            return jsonify({"error": f"性格信息不合法：{e}"}), 400

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


# ========================================
# 陌生人可见设置 API
# ========================================
@profile_bp.route("/api/visibility/stranger", methods=["GET"])
def api_stranger_visibility_get():
    """获取陌生人可见设置。"""
    if "user_id" not in session:
        return jsonify({"error": "未登录"}), 401
    return jsonify(load_stranger_visibility(session["user_id"]))


@profile_bp.route("/api/visibility/stranger", methods=["PUT"])
def api_stranger_visibility_put():
    """更新陌生人可见设置。"""
    if "user_id" not in session:
        return jsonify({"error": "未登录"}), 401
    data = request.get_json(silent=True) or {}
    return jsonify(save_stranger_visibility(session["user_id"], data))


# ========================================
# 好友可见设置 API（全局默认）
# ========================================
@profile_bp.route("/api/visibility/friend", methods=["GET"])
def api_friend_visibility_get():
    """获取好友可见设置（全局默认）。"""
    if "user_id" not in session:
        return jsonify({"error": "未登录"}), 401
    return jsonify(load_friend_visibility(session["user_id"]))


@profile_bp.route("/api/visibility/friend", methods=["PUT"])
def api_friend_visibility_put():
    """更新好友可见设置（全局默认）。"""
    if "user_id" not in session:
        return jsonify({"error": "未登录"}), 401
    data = request.get_json(silent=True) or {}
    return jsonify(save_friend_visibility(session["user_id"], data))


# ========================================
# 好友独立隐私设置 API
# ========================================
@profile_bp.route("/api/visibility/friend-overrides", methods=["GET"])
def api_friend_overrides_get():
    """获取所有好友独立隐私设置。"""
    if "user_id" not in session:
        return jsonify({"error": "未登录"}), 401
    overrides = load_all_friend_overrides(session["user_id"])
    return jsonify(list(overrides.values()))


@profile_bp.route("/api/visibility/friend-overrides/<int:friend_id>", methods=["GET"])
def api_friend_override_get(friend_id):
    """获取针对特定好友的独立隐私设置。"""
    if "user_id" not in session:
        return jsonify({"error": "未登录"}), 401
    override = load_friend_visibility_override(session["user_id"], friend_id)
    if override is None:
        return jsonify({"error": "未设置独立隐私"}), 404
    return jsonify(override)


@profile_bp.route("/api/visibility/friend-overrides/<int:friend_id>", methods=["PUT"])
def api_friend_override_put(friend_id):
    """设置针对特定好友的独立隐私（传入 null 值表示恢复默认）。"""
    if "user_id" not in session:
        return jsonify({"error": "未登录"}), 401
    data = request.get_json(silent=True) or {}
    return jsonify(save_friend_visibility_override(session["user_id"], friend_id, data))


@profile_bp.route("/api/visibility/friend-overrides/<int:friend_id>", methods=["DELETE"])
def api_friend_override_delete(friend_id):
    """删除针对特定好友的独立隐私设置（恢复全局默认）。"""
    if "user_id" not in session:
        return jsonify({"error": "未登录"}), 401
    delete_friend_visibility_override(session["user_id"], friend_id)
    return jsonify({"ok": True})


@profile_bp.route("/api/users/<int:uid>/public")
def api_user_public(uid):
    """
    获取用户公开资料。
    本人返回完整资料；好友根据隐私设置返回相应内容；陌生人根据隐私设置返回相应内容。
    """
    if "user_id" not in session:
        return jsonify({"error": "未登录"}), 401
    viewer = session["user_id"]
    conn = _conn()
    c = conn.cursor()
    c.execute(
        "SELECT id, account, username, gender, grade, major, phone FROM users WHERE id=?",
        (uid,),
    )
    row = c.fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "用户不存在"}), 404
    uid_val, account, username, gender, grade, major, phone = row

    c.execute("SELECT COUNT(*) FROM user_interests WHERE user_id=?", (uid,))
    ic = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM user_skills WHERE user_id=?", (uid,))
    sc = c.fetchone()[0]
    conn.close()

    if viewer == uid:
        full = load_profile(uid)
        return jsonify({"relation": "self", **full})

    if _friends_linked(viewer, uid):
        # 好友：检查是否有独立覆盖设置
        override = load_friend_visibility_override(uid, viewer)
        if override is None:
            # 使用全局好友可见设置
            vis = load_friend_visibility(uid)
        else:
            # 使用独立覆盖设置
            vis = override

        # 构建返回数据（根据设置决定显示哪些字段）
        result = {
            "relation": "friend",
            "id": uid_val,
            "username": username,
        }

        # 根据设置决定显示内容
        if vis.get("show_phone"):
            result["phone"] = phone or ""
        if vis.get("show_gender"):
            result["gender"] = gender or ""
        if vis.get("show_grade"):
            result["grade"] = grade or ""
        if vis.get("show_major"):
            result["major"] = major or ""

        # 加载完整资料以获取标签
        full = load_profile(uid)
        if vis.get("show_interests"):
            result["interests"] = full.get("interests") or []
        if vis.get("show_skills"):
            result["skills"] = full.get("skills") or []
        if vis.get("show_projects"):
            result["projects"] = full.get("projects") or []
        if vis.get("show_personality"):
            result["traits"] = full.get("traits") or []

        return jsonify(result)

    # 陌生人：使用陌生人可见设置
    vis = load_stranger_visibility(uid)
    result = {
        "relation": "stranger",
        "id": uid_val,
        "username": username,
        "stats": {"interest_count": ic, "skill_count": sc},
    }

    if vis.get("show_gender"):
        result["gender"] = gender or ""
    if vis.get("show_grade"):
        result["grade"] = grade or ""
    if vis.get("show_major"):
        result["major"] = major or ""

    # 加载完整资料以获取标签（如果设置允许显示）
    full = load_profile(uid)
    if vis.get("show_interests"):
        result["interests"] = full.get("interests") or []
        result["interest_count"] = ic
    if vis.get("show_skills"):
        result["skills"] = full.get("skills") or []
        result["skill_count"] = sc

    result["privacy_note"] = "非好友可见范围由对方隐私设置控制。"

    return jsonify(result)
