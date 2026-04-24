# modules/friend.py — 好友列表、快捷互加、好友请求
import sqlite3
from datetime import datetime, timedelta, timezone

from flask import Blueprint, jsonify, request, session

from config import DATABASE_PATH
from modules.chat import ensure_messages_table

friend_bp = Blueprint("friend", __name__)

_requests_table_ok = False


def _conn():
    return sqlite3.connect(DATABASE_PATH)


def _ensure_requests_table():
    global _requests_table_ok
    if _requests_table_ok:
        return
    conn = _conn()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS friend_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_id INTEGER NOT NULL,
            to_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(from_id, to_id)
        )
        """
    )
    conn.commit()
    conn.close()
    _requests_table_ok = True


def _are_friends(a, b):
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


def _get_online_status(fid):
    """根据 last_active 字段判断在线状态（真实追踪）。"""
    beijing_tz = timezone(timedelta(hours=8))
    conn = _conn()
    cursor = conn.cursor()
    cursor.execute("SELECT last_active FROM users WHERE id=?", (fid,))
    row = cursor.fetchone()
    conn.close()

    if not row or not row[0]:
        return "offline"

    last_active = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S").replace(tzinfo=beijing_tz)
    now_beijing = datetime.now(beijing_tz)
    diff = (now_beijing - last_active).total_seconds()

    if diff < 300:  # 5分钟内
        return "online"
    if diff < 1800:  # 30分钟内
        return "away"
    return "offline"


def _recent_chat(cursor, me, fid, days=7):
    ensure_messages_table()
    since = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        """
        SELECT 1 FROM messages
        WHERE created_at >= ? AND (
            (sender_id=? AND receiver_id=?) OR (sender_id=? AND receiver_id=?)
        )
        LIMIT 1
        """,
        (since, me, fid, fid, me),
    )
    return cursor.fetchone() is not None


def _friend_circle_activity(cursor, fid):
    """对方好友数量较多时标记为「圈子活跃」。"""
    cursor.execute("SELECT COUNT(*) FROM friendships WHERE user_id=?", (fid,))
    n = cursor.fetchone()[0]
    return n >= 5


def get_friends_with_ids(user_id):
    ensure_messages_table()
    conn = _conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT friend_id, created_at FROM friendships WHERE user_id=?",
        (user_id,),
    )
    rows = cursor.fetchall()
    out = []
    for fid, created_at in rows:
        cursor.execute(
            "SELECT username, gender, grade FROM users WHERE id=?",
            (fid,),
        )
        u = cursor.fetchone()
        if u:
            username, gender, grade = u[0], u[1] or "", u[2] or ""
            recent = _recent_chat(cursor, user_id, fid)
            active = _friend_circle_activity(cursor, fid)
            badges = []
            if recent:
                badges.append("recent_chat")
            if active:
                badges.append("social_star")
            out.append({
                "id": fid,
                "username": username,
                "friend_since": created_at,
                "gender": gender,
                "grade": grade,
                "online_status": _get_online_status(fid),
                "badges": badges,
            })
    conn.close()
    return out


@friend_bp.route("/api/friends")
def api_friends():
    if "user_id" not in session:
        return jsonify({"error": "未登录"}), 401
    return jsonify(get_friends_with_ids(session["user_id"]))


@friend_bp.route("/api/friends/add", methods=["POST"])
def api_friends_add():
    if "user_id" not in session:
        return jsonify({"error": "未登录"}), 401
    _ensure_requests_table()
    me = session["user_id"]
    data = request.get_json(silent=True) or {}
    try:
        to_id = int(data.get("friend_id"))
    except (TypeError, ValueError):
        return jsonify({"error": "无效的 friend_id"}), 400
    if to_id == me:
        return jsonify({"error": "不能添加自己"}), 400
    conn = _conn()
    c = conn.cursor()
    if not _row_user(c, to_id):
        conn.close()
        return jsonify({"error": "用户不存在"}), 404
    if _are_friends(me, to_id):
        conn.close()
        return jsonify({"error": "已是好友"}), 400
    # 检查是否已有请求（任意方向）
    c.execute(
        "SELECT id, from_id, status FROM friend_requests WHERE (from_id=? AND to_id=?) OR (from_id=? AND to_id=?)",
        (me, to_id, to_id, me),
    )
    ex = c.fetchone()
    if ex:
        rid, from_id, st = ex
        if st == "pending":
            conn.close()
            direction = "发给对方的" if from_id == me else "对方发来的"
            return jsonify({"error": f"已存在{direction}待处理请求", "request_id": rid}), 400
        if st == "rejected":
            # 被拒绝后可重新发起
            c.execute(
                "UPDATE friend_requests SET from_id=?, to_id=?, status='pending', created_at=datetime('now') WHERE id=?",
                (me, to_id, rid),
            )
            conn.commit()
            conn.close()
            return jsonify({"id": rid, "from_id": me, "to_id": to_id, "status": "pending"}), 200
    c.execute(
        "INSERT INTO friend_requests (from_id, to_id, status) VALUES (?,?, 'pending')",
        (me, to_id),
    )
    conn.commit()
    rid = c.lastrowid
    conn.close()
    return jsonify({"id": rid, "from_id": me, "to_id": to_id, "status": "pending"}), 201


def _row_user(c, uid):
    c.execute("SELECT id, username FROM users WHERE id=?", (uid,))
    return c.fetchone()


@friend_bp.route("/api/friend-requests", methods=["POST"])
def create_friend_request():
    if "user_id" not in session:
        return jsonify({"error": "未登录"}), 401
    _ensure_requests_table()
    me = session["user_id"]
    data = request.get_json(silent=True) or {}
    try:
        to_id = int(data.get("to_id"))
    except (TypeError, ValueError):
        return jsonify({"error": "无效的用户 ID"}), 400
    if to_id == me:
        return jsonify({"error": "不能向自己发请求"}), 400
    conn = _conn()
    c = conn.cursor()
    if not _row_user(c, to_id):
        conn.close()
        return jsonify({"error": "用户不存在"}), 404
    if _are_friends(me, to_id):
        conn.close()
        return jsonify({"error": "已是好友"}), 400
    c.execute(
        "SELECT id, status FROM friend_requests WHERE from_id=? AND to_id=?",
        (me, to_id),
    )
    ex = c.fetchone()
    if ex:
        eid, st = ex
        if st == "pending":
            conn.close()
            return jsonify({"error": "已有待处理的请求", "id": eid}), 400
        if st == "accepted":
            conn.close()
            return jsonify({"error": "已是好友"}), 400
        if st == "rejected":
            c.execute(
                "UPDATE friend_requests SET status='pending', created_at=datetime('now') WHERE id=?",
                (eid,),
            )
            conn.commit()
            conn.close()
            return jsonify({"id": eid, "from_id": me, "to_id": to_id, "status": "pending"}), 200
    c.execute(
        "INSERT INTO friend_requests (from_id, to_id, status) VALUES (?,?, 'pending')",
        (me, to_id),
    )
    conn.commit()
    rid = c.lastrowid
    conn.close()
    return jsonify({"id": rid, "from_id": me, "to_id": to_id, "status": "pending"}), 201


@friend_bp.route("/api/friend-requests/incoming")
def list_incoming_requests():
    if "user_id" not in session:
        return jsonify({"error": "未登录"}), 401
    _ensure_requests_table()
    me = session["user_id"]
    conn = _conn()
    c = conn.cursor()
    c.execute(
        """
        SELECT r.id, r.from_id, r.status, r.created_at, u.username
        FROM friend_requests r
        JOIN users u ON u.id = r.from_id
        WHERE r.to_id=? AND r.status='pending'
        ORDER BY r.id DESC
        """,
        (me,),
    )
    rows = c.fetchall()
    conn.close()
    return jsonify(
        [
            {"id": r[0], "from_id": r[1], "status": r[2], "created_at": r[3], "from_username": r[4]}
            for r in rows
        ]
    )


@friend_bp.route("/api/friend-requests/outgoing")
def list_outgoing_requests():
    if "user_id" not in session:
        return jsonify({"error": "未登录"}), 401
    _ensure_requests_table()
    me = session["user_id"]
    conn = _conn()
    c = conn.cursor()
    c.execute(
        """
        SELECT r.id, r.to_id, r.status, r.created_at, u.username
        FROM friend_requests r
        JOIN users u ON u.id = r.to_id
        WHERE r.from_id=? AND r.status='pending'
        ORDER BY r.id DESC
        """,
        (me,),
    )
    rows = c.fetchall()
    conn.close()
    return jsonify(
        [
            {"id": r[0], "to_id": r[1], "status": r[2], "created_at": r[3], "to_username": r[4]}
            for r in rows
        ]
    )


def _get_request_row(c, rid):
    c.execute(
        "SELECT id, from_id, to_id, status FROM friend_requests WHERE id=?",
        (rid,),
    )
    return c.fetchone()


@friend_bp.route("/api/friend-requests/<int:rid>/accept", methods=["POST"])
def accept_friend_request(rid):
    if "user_id" not in session:
        return jsonify({"error": "未登录"}), 401
    _ensure_requests_table()
    me = session["user_id"]
    conn = _conn()
    c = conn.cursor()
    row = _get_request_row(c, rid)
    if not row or row[3] != "pending":
        conn.close()
        return jsonify({"error": "请求不存在或已处理"}), 400
    _, from_id, to_id, _ = row
    if to_id != me:
        conn.close()
        return jsonify({"error": "无权操作"}), 403
    c.execute("UPDATE friend_requests SET status='accepted' WHERE id=?", (rid,))
    for a, b in ((from_id, to_id), (to_id, from_id)):
        c.execute(
            "SELECT 1 FROM friendships WHERE user_id=? AND friend_id=?",
            (a, b),
        )
        if not c.fetchone():
            c.execute(
                "INSERT INTO friendships (user_id, friend_id) VALUES (?,?)",
                (a, b),
            )
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


@friend_bp.route("/api/friend-requests/<int:rid>/reject", methods=["POST"])
def reject_friend_request(rid):
    if "user_id" not in session:
        return jsonify({"error": "未登录"}), 401
    _ensure_requests_table()
    me = session["user_id"]
    conn = _conn()
    c = conn.cursor()
    row = _get_request_row(c, rid)
    if not row or row[3] != "pending":
        conn.close()
        return jsonify({"error": "请求不存在或已处理"}), 400
    _, _from_id, to_id, _ = row
    if to_id != me:
        conn.close()
        return jsonify({"error": "无权操作"}), 403
    c.execute("UPDATE friend_requests SET status='rejected' WHERE id=?", (rid,))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


@friend_bp.route("/api/friends/<int:friend_id>", methods=["DELETE"])
def delete_friend(friend_id):
    """删除好友关系（双向）。"""
    if "user_id" not in session:
        return jsonify({"error": "未登录"}), 401
    user_id = session["user_id"]
    conn = _conn()
    c = conn.cursor()
    # 删除双向 friendship 记录
    c.execute(
        "DELETE FROM friendships WHERE (user_id=? AND friend_id=?) OR (user_id=? AND friend_id=?)",
        (user_id, friend_id, friend_id, user_id),
    )
    deleted = c.rowcount
    conn.commit()
    conn.close()
    if deleted == 0:
        return jsonify({"error": "好友关系不存在"}), 404
    return jsonify({"ok": True})
