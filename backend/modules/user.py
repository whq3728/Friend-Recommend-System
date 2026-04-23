# modules/user.py — 认证 API（登录、注册、登出、当前用户）
# 登录使用 account + password；username 仅作昵称显示，不参与登录
# 手机验证码：使用阿里云短信服务（需配置环境变量）
import sqlite3
import time

from flask import Blueprint, jsonify, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from config import DATABASE_PATH, SMS_CODE_EXPIRE_SECONDS, SMS_SEND_INTERVAL_SECONDS
from modules.personality import (
    bigfive_from_questionnaire_1to5,
    bigfive_from_quick_1to5,
    upsert_personality_bigfive,
)
from modules.sms import send_sms, store_code, verify_code

user_bp = Blueprint("user", __name__)

# 发送记录：手机号 -> 上次发送时间（用于频率限制）
_sms_send_times: dict[str, float] = {}


def _conn():
    """获取数据库连接。"""
    return sqlite3.connect(DATABASE_PATH)


def update_last_active(user_id):
    """更新用户最后活跃时间（北京时间）。"""
    from datetime import datetime, timezone, timedelta
    beijing_tz = timezone(timedelta(hours=8))
    now_beijing = datetime.now(beijing_tz).strftime("%Y-%m-%d %H:%M:%S")
    conn = _conn()
    conn.execute("UPDATE users SET last_active=? WHERE id=?", (now_beijing, user_id))
    conn.commit()
    conn.close()


def _normalize_phone(p):
    p = (p or "").strip().replace(" ", "")
    return p if p else ""


def _normalize_interests(raw, max_items=20):
    if raw is None:
        return []
    if isinstance(raw, str):
        items = [s.strip() for s in raw.replace(",", "\n").split("\n") if s.strip()]
    elif isinstance(raw, list):
        items = [str(x).strip() for x in raw if x is not None and str(x).strip()]
    else:
        return []
    out, seen = [], set()
    for s in items[:max_items]:
        if s not in seen and len(s) <= 64:
            seen.add(s)
            out.append(s)
    return out


@user_bp.route("/api/auth/login", methods=["POST"])
def api_auth_login():
    """
    登录接口：使用账号 + 密码。
    account 为登录用标识，username 为昵称，不参与登录。
    """
    data = request.get_json(silent=True) or {}
    account = (data.get("account") or "").strip()
    password = data.get("password") or ""
    if not account or not password:
        return jsonify({"error": "请输入账号和密码"}), 400

    conn = _conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, account, username, password FROM users WHERE account=?",
        (account,),
    )
    row = cursor.fetchone()
    conn.close()

    if not row or not check_password_hash(row[3], password):
        return jsonify({"error": "账号或密码错误"}), 401

    session["user_id"] = row[0]
    return jsonify({
        "id": row[0],
        "account": row[1],
        "username": row[2],
    })


@user_bp.route("/api/auth/login-phone", methods=["POST"])
def api_auth_login_phone():
    """手机号 + 验证码登录（验证码先发 /api/auth/sms/send）。"""
    data = request.get_json(silent=True) or {}
    phone = _normalize_phone(data.get("phone"))
    code = (data.get("code") or "").strip()
    if len(phone) < 11:
        return jsonify({"error": "请输入有效手机号"}), 400
    if not verify_code(phone, code, SMS_CODE_EXPIRE_SECONDS):
        return jsonify({"error": "验证码无效或已过期，请先获取验证码"}), 400

    conn = _conn()
    c = conn.cursor()
    c.execute(
        "SELECT id, account, username FROM users WHERE phone=? AND phone IS NOT NULL AND phone != ''",
        (phone,),
    )
    row = c.fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "该手机号未注册，请先注册并绑定手机号"}), 404

    session["user_id"] = row[0]
    return jsonify({"id": row[0], "account": row[1], "username": row[2]})


@user_bp.route("/api/auth/sms/send", methods=["POST"])
def api_auth_sms_send():
    """发送短信验证码（通过阿里云短信服务）。"""
    data = request.get_json(silent=True) or {}
    phone = _normalize_phone(data.get("phone"))
    if len(phone) < 11:
        return jsonify({"error": "请输入有效手机号"}), 400

    # 频率限制：同一手机号60秒内只能发送一次
    current_time = time.time()
    last_send_time = _sms_send_times.get(phone, 0)
    if current_time - last_send_time < SMS_SEND_INTERVAL_SECONDS:
        remaining = int(SMS_SEND_INTERVAL_SECONDS - (current_time - last_send_time))
        return jsonify({
            "error": f"发送太频繁，请 {remaining} 秒后再试",
            "remaining_seconds": remaining,
        }), 429

    # 发送短信
    success, message, code = send_sms(phone)

    if success:
        # 真实发送成功，存储验证码用于校验
        store_code(phone, code)
        _sms_send_times[phone] = current_time
        return jsonify({
            "ok": True,
            "message": "验证码已发送",
        })
    else:
        # 演示模式或发送失败
        if code:
            # 演示模式：存储验证码并返回提示
            store_code(phone, code)
            _sms_send_times[phone] = current_time
            return jsonify({
                "ok": True,
                "hint": message,
                "demo_mode": True,
            })
        else:
            return jsonify({"error": message}), 500


@user_bp.route("/api/auth/forgot-reset", methods=["POST"])
def api_auth_forgot_reset():
    """手机号 + 验证码重置密码。"""
    data = request.get_json(silent=True) or {}
    phone = _normalize_phone(data.get("phone"))
    code = (data.get("code") or "").strip()
    new_password = data.get("new_password") or ""
    if len(phone) < 11:
        return jsonify({"error": "请输入有效手机号"}), 400
    if not verify_code(phone, code, SMS_CODE_EXPIRE_SECONDS):
        return jsonify({"error": "验证码无效或已过期"}), 400
    if len(new_password) < 4:
        return jsonify({"error": "新密码至少 4 位"}), 400

    pwd_hash = generate_password_hash(new_password)
    conn = _conn()
    c = conn.cursor()
    c.execute(
        "UPDATE users SET password=? WHERE phone=? AND phone IS NOT NULL AND phone != ''",
        (pwd_hash, phone),
    )
    conn.commit()
    updated = c.rowcount
    conn.close()
    if not updated:
        return jsonify({"error": "该手机号未绑定账号"}), 404
    return jsonify({"ok": True})


@user_bp.route("/api/auth/register", methods=["POST"])
def api_auth_register():
    """
    注册接口：account 用于登录，username 为昵称，password 会哈希存储。
    可选：phone、gender、grade、interests（兴趣标签列表）、skills（技能标签列表）。
    可选：personality_mode（skip/quick/questionnaire），用于 Big Five 性格建模。
    """
    data = request.get_json(silent=True) or {}
    account = (data.get("account") or "").strip()
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    phone = _normalize_phone(data.get("phone"))
    gender = (data.get("gender") or "").strip() or None
    grade = (data.get("grade") or "").strip() or None
    reg_code = (data.get("sms_code") or "").strip()
    interests = _normalize_interests(data.get("interests"))
    skills = _normalize_interests(data.get("skills"))
    personality_mode = (data.get("personality_mode") or "skip").strip()
    bigfive_quick = data.get("bigfive_quick") or {}
    bigfive_answers = data.get("bigfive_answers") or []

    if not account or not username or not password:
        return jsonify({"error": "请输入账号、昵称和密码"}), 400
    if len(account) > 64:
        return jsonify({"error": "账号过长"}), 400
    if len(username) > 64:
        return jsonify({"error": "昵称过长"}), 400
    if len(password) < 4:
        return jsonify({"error": "密码至少 4 位"}), 400
    if len(password) > 128:
        return jsonify({"error": "密码过长"}), 400

    if phone:
        if len(phone) < 11:
            return jsonify({"error": "手机号格式不正确"}), 400
        if not verify_code(phone, reg_code, SMS_CODE_EXPIRE_SECONDS):
            return jsonify({"error": "短信验证码无效，请先获取并填写正确验证码"}), 400

    pwd_hash = generate_password_hash(password)
    conn = _conn()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username=?", (username,))
    if cursor.fetchone():
        conn.close()
        return jsonify({"error": "该昵称已被使用"}), 400
    if phone:
        cursor.execute(
            "SELECT id FROM users WHERE phone=? AND phone IS NOT NULL AND phone != ''",
            (phone,),
        )
        if cursor.fetchone():
            conn.close()
            return jsonify({"error": "该手机号已被绑定"}), 400
    try:
        cursor.execute(
            """
            INSERT INTO users (account, username, password, gender, grade, phone)
            VALUES (?,?,?,?,?,?)
            """,
            (account, username, pwd_hash, gender, grade, phone or None),
        )
        uid = cursor.lastrowid
        for it in interests:
            cursor.execute(
                "INSERT OR IGNORE INTO user_interests (user_id, interest) VALUES (?,?)",
                (uid, it),
            )
        for s in skills:
            cursor.execute(
                "INSERT OR IGNORE INTO user_skills (user_id, skill) VALUES (?,?)",
                (uid, s),
            )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"error": "该账号已存在"}), 400
    except sqlite3.OperationalError as e:
        conn.close()
        if "phone" in str(e).lower():
            return jsonify({"error": "数据库缺少 phone 列，请运行 python init_db.py 升级"}), 500
        raise
    conn.close()

    # ---------------------------
    # Big Five 性格建模（可选）
    # ---------------------------
    try:
        vec_0to1 = None
        if personality_mode in ("skip", "none", "", None):
            vec_0to1 = None
        elif personality_mode == "quick":
            vec_0to1 = bigfive_from_quick_1to5(bigfive_quick)
        elif personality_mode == "questionnaire":
            # 前端传 10 题答案：每题 1..5
            vec_0to1 = bigfive_from_questionnaire_1to5(list(bigfive_answers))
        else:
            return jsonify({"error": "personality_mode 无效"}), 400

        if vec_0to1 is not None:
            upsert_personality_bigfive(uid, vec_0to1)
    except ValueError as e:
        return jsonify({"error": f"性格信息不合法：{e}"}), 400

    return jsonify({"ok": True}), 201


@user_bp.route("/api/auth/logout", methods=["POST"])
def api_auth_logout():
    """登出，清除 session。"""
    session.pop("user_id", None)
    return jsonify({"ok": True})


@user_bp.route("/api/auth/me", methods=["GET"])
def api_auth_me():
    """获取当前登录用户信息（含 account、username）。"""
    if "user_id" not in session:
        return jsonify({"error": "未登录"}), 401

    uid = session["user_id"]
    conn = _conn()
    cursor = conn.cursor()
    cursor.execute("SELECT id, account, username FROM users WHERE id=?", (uid,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        session.pop("user_id", None)
        return jsonify({"error": "未登录"}), 401
    return jsonify({
        "id": row[0],
        "account": row[1],
        "username": row[2],
    })


@user_bp.route("/api/me/summary", methods=["GET"])
def api_me_summary():
    """导航栏用：好友数、推荐次数、简单活跃度分（前端展示徽章）。"""
    if "user_id" not in session:
        return jsonify({"error": "未登录"}), 401
    uid = session["user_id"]
    conn = _conn()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM friendships WHERE user_id=?", (uid,))
    friend_n = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM user_interests WHERE user_id=?", (uid,))
    interest_n = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM user_skills WHERE user_id=?", (uid,))
    skill_n = c.fetchone()[0]
    try:
        c.execute("SELECT COUNT(*) FROM recommendation_history WHERE user_id=?", (uid,))
        rec_n = c.fetchone()[0]
    except sqlite3.OperationalError:
        rec_n = 0
    try:
        c.execute(
            "SELECT COUNT(*) FROM friend_requests WHERE to_id=? AND status='pending'",
            (uid,),
        )
        pending_in = c.fetchone()[0]
    except sqlite3.OperationalError:
        pending_in = 0
    conn.close()
    activity = min(100, friend_n * 3 + interest_n * 2 + skill_n * 2 + min(rec_n, 20))
    return jsonify({
        "friend_count": friend_n,
        "recommend_runs": rec_n,
        "pending_incoming_requests": pending_in,
        "activity_score": activity,
    })
