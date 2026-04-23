# modules/chat.py — 好友私信 API（页面由 Vue 提供）
import os
import sqlite3
from datetime import datetime, timedelta, timezone

from flask import Blueprint, jsonify, request, session

from config import DATABASE_PATH

chat_bp = Blueprint("chat", __name__)

_messages_schema_ok = False


def ensure_messages_table():
    global _messages_schema_ok
    if _messages_schema_ok:
        return
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id INTEGER NOT NULL,
                receiver_id INTEGER NOT NULL,
                body TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        conn.commit()
    finally:
        conn.close()
    _messages_schema_ok = True


def _conn():
    ensure_messages_table()
    return sqlite3.connect(DATABASE_PATH)


def _to_beijing_time(stored_str):
    """返回北京时间（数据已迁移为北京时间，直接返回）。"""
    return stored_str if stored_str else None


def _format_message(r):
    """格式化消息记录，时间转换为北京时间。"""
    return {
        "id": r[0],
        "sender_id": r[1],
        "receiver_id": r[2],
        "body": r[3],
        "created_at": _to_beijing_time(r[4]),
    }


@chat_bp.route("/api/chat/<int:peer_id>/info", methods=["GET"])
def api_chat_info(peer_id):
    """获取与某好友的聊天信息（如对方最后活跃时间）。"""
    if "user_id" not in session:
        return jsonify({"error": "未登录"}), 401
    me = session["user_id"]
    if not can_chat_with(me, peer_id):
        return jsonify({"error": "非好友"}), 403
    conn = _conn()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT created_at FROM messages
        WHERE sender_id=? AND receiver_id=?
        ORDER BY id DESC LIMIT 1
        """,
        (peer_id, me),
    )
    row = cursor.fetchone()
    conn.close()
    return jsonify({
        "peer_id": peer_id,
        "last_message_from_peer_at": _to_beijing_time(row[0]) if row else None,
    })


def can_chat_with(user_id, other_id):
    if user_id == other_id:
        return False
    conn = _conn()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT 1 FROM friendships
        WHERE (user_id=? AND friend_id=?) OR (user_id=? AND friend_id=?)
        """,
        (user_id, other_id, other_id, user_id),
    )
    ok = cursor.fetchone() is not None
    conn.close()
    return ok


@chat_bp.route("/api/chat/<int:peer_id>/messages", methods=["GET"])
def api_messages_get(peer_id):
    if "user_id" not in session:
        return jsonify({"error": "未登录"}), 401
    me = session["user_id"]
    if not can_chat_with(me, peer_id):
        return jsonify({"error": "非好友"}), 403

    after_id = request.args.get("after_id", type=int)

    conn = _conn()
    cursor = conn.cursor()
    if after_id is not None and after_id > 0:
        cursor.execute(
            """
            SELECT id, sender_id, receiver_id, body, created_at
            FROM messages
            WHERE ((sender_id=? AND receiver_id=?) OR (sender_id=? AND receiver_id=?))
              AND id > ?
            ORDER BY id ASC
            """,
            (me, peer_id, peer_id, me, after_id),
        )
    else:
        cursor.execute(
            """
            SELECT id, sender_id, receiver_id, body, created_at
            FROM messages
            WHERE (sender_id=? AND receiver_id=?) OR (sender_id=? AND receiver_id=?)
            ORDER BY id ASC
            LIMIT 500
            """,
            (me, peer_id, peer_id, me),
        )
    rows = cursor.fetchall()
    conn.close()

    return jsonify([_format_message(r) for r in rows])


@chat_bp.route("/api/chat/<int:peer_id>/messages", methods=["POST"])
def api_messages_post(peer_id):
    if "user_id" not in session:
        return jsonify({"error": "未登录"}), 401
    me = session["user_id"]
    if not can_chat_with(me, peer_id):
        return jsonify({"error": "非好友"}), 403

    data = request.get_json(silent=True) or {}
    body = (data.get("body") or "").strip()
    if not body:
        return jsonify({"error": "消息不能为空"}), 400
    if len(body) > 4000:
        return jsonify({"error": "消息过长"}), 400

    conn = None
    row = None
    try:
        beijing_tz = timezone(timedelta(hours=8))
        now_beijing = datetime.now(beijing_tz).strftime("%Y-%m-%d %H:%M:%S")
        conn = _conn()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO messages (sender_id, receiver_id, body, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (me, peer_id, body, now_beijing),
        )
        conn.commit()
        mid = cursor.lastrowid
        cursor.execute(
            "SELECT id, sender_id, receiver_id, body, created_at FROM messages WHERE id=?",
            (mid,),
        )
        row = cursor.fetchone()
    except sqlite3.Error as e:
        return jsonify({"error": f"数据库写入失败：{e}"}), 500
    finally:
        if conn is not None:
            conn.close()

    if not row:
        return jsonify({"error": "保存消息失败"}), 500

    return jsonify(_format_message(row)), 201
