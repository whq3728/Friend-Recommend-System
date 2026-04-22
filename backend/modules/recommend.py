# modules/recommend.py — 多场景推荐 API（好友 PSI + Jaccard；兴趣/技能语义相似）
import json
import os
import random
import sqlite3
import threading
from datetime import datetime

import numpy as np

from flask import Blueprint, jsonify, request, session

from config import DATABASE_PATH
from modules.profile import load_matching_prefs
from modules.psi import psi_intersection
from modules.personality import get_personality_norm_pair_cached, trait_similarity_mixed

recommend_bp = Blueprint("recommend_bp", __name__)

_history_table_ok = False

# ---------------------------
# 语义匹配实现（兴趣/技能）
# ---------------------------
# 说明：
# - 对“用户标签集合 vs 候选用户标签集合”：
#   1) 将每个标签向量化（SentenceTransformer/BERT）
#   2) 计算两集合的余弦相似度矩阵
#   3) 对集合 A 中每个标签取其在集合 B 的最大相似度
#   4) 平均这些最大相似度作为该集合的相似度分数
# - 为了与原有前端字段兼容（common_interests/common_skills），
#   还会统计“最大相似度 >= 阈值”的标签数量作为共同数量。
#
# 性能建议：
# - 标签向量会在进程内做缓存（按标签文本维度缓存）。
# - 如需进一步优化，可缓存“用户->标签向量列表”或预计算全体用户向量（见文末建议）。

_SEMANTIC_MODEL_NAME = os.environ.get(
    "SEMANTIC_MODEL_NAME", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)
_SEMANTIC_MATCH_THRESHOLD = float(os.environ.get("SEMANTIC_MATCH_THRESHOLD", "0.55"))

_semantic_model = None
_semantic_model_lock = threading.Lock()
_tag_vec_cache = {}  # tag_text -> np.ndarray (normalized embedding)

try:
    # SentenceTransformer 内部使用 transformers + torch，通常会比手写 BERT 输入更省心。
    from sentence_transformers import SentenceTransformer  # type: ignore

    _SEMANTIC_AVAILABLE = True
except Exception:
    SentenceTransformer = None  # type: ignore
    _SEMANTIC_AVAILABLE = False


def _get_semantic_model():
    """惰性加载 SentenceTransformer 模型（避免服务启动就加载大模型）。"""
    global _semantic_model
    if not _SEMANTIC_AVAILABLE:
        return None
    if _semantic_model is not None:
        return _semantic_model
    with _semantic_model_lock:
        if _semantic_model is None:
            _semantic_model = SentenceTransformer(_SEMANTIC_MODEL_NAME)
    return _semantic_model


def _encode_tags(tags):
    """
    将多个标签文本向量化并返回二维 numpy 数组。
    - 返回的向量默认使用 normalize_embeddings=True，使得 A @ B.T == cosine_similarity。
    """
    model = _get_semantic_model()
    if model is None:
        return np.zeros((0, 0), dtype=np.float32)

    tags = list(tags or [])
    if not tags:
        return np.zeros((0, 0), dtype=np.float32)

    # 收集缺失标签并批量编码（显著减少 encode 调用次数）。
    missing = [t for t in tags if t not in _tag_vec_cache]
    if missing:
        vecs = model.encode(
            missing,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        for t, v in zip(missing, vecs):
            _tag_vec_cache[t] = v.astype(np.float32)

    # 统一输出顺序：按 tags 列表顺序拼接。
    return np.stack([_tag_vec_cache[t] for t in tags], axis=0)


def _semantic_set_similarity(set_a, set_b):
    """
    计算“标签集合相似度”：
    - score：对 set_a 每个标签取对 set_b 的最大余弦相似度后求均值（0..1 左右）
    - common_cnt：最大相似度 >= 阈值的标签数量（用于前端 reason/chips）
    """
    if not set_a or not set_b:
        return 0.0, 0

    # 为了与缓存/可重复性相关，这里直接转换为 list；集合顺序不影响语义分数的正确性。
    a_tags = list(set_a)
    b_tags = list(set_b)
    A = _encode_tags(a_tags)
    B = _encode_tags(b_tags)
    if A.size == 0 or B.size == 0:
        return 0.0, 0

    # A、B 已归一化，因此点积等价于余弦相似度。
    sim = A @ B.T  # shape: (len(a), len(b))
    max_sim = sim.max(axis=1)  # shape: (len(a),)
    score = float(max_sim.mean())
    common_cnt = int((max_sim >= _SEMANTIC_MATCH_THRESHOLD).sum())
    return score, common_cnt


def _ensure_history_table():
    global _history_table_ok
    if _history_table_ok:
        return
    conn = sqlite3.connect(DATABASE_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS recommendation_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            mode TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            snapshot_json TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()
    _history_table_ok = True


def _mode_weights(mode):
    if mode == "friend":
        # friend / interest / skill / personality
        return 0.4, 0.4, 0.0, 0.2
    if mode == "team":
        return 0.2, 0.1, 0.5, 0.2
    if mode == "love":
        return 0.1, 0.5, 0.1, 0.3
    return 0.4, 0.4, 0.0, 0.2


def _jaccard(a, b, inter):
    u = a | b
    return len(inter) / len(u) if u else 0.0


def _compute_multi_recommendations(user_id, mode, top_n, skip=0, exclude_ids=None):
    if exclude_ids is None:
        exclude_ids = set()
    w_f, w_i, w_s, w_t = _mode_weights(mode)
    prefs = load_matching_prefs(user_id)
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Big Five 性格向量（带缓存，避免重复 DB 查询）
    # 如果用户关闭了性格分享，则不参与匹配
    user_personality = get_personality_norm_pair_cached(user_id) if prefs.get("share_personality", True) else None

    cursor.execute("SELECT friend_id FROM friendships WHERE user_id=?", (user_id,))
    user_friends = set(row[0] for row in cursor.fetchall())
    if not prefs["share_friend_graph"]:
        user_friends = set()

    cursor.execute("SELECT interest FROM user_interests WHERE user_id=?", (user_id,))
    user_interests = set(row[0] for row in cursor.fetchall())
    if not prefs["share_interests"]:
        user_interests = set()

    cursor.execute("SELECT skill FROM user_skills WHERE user_id=?", (user_id,))
    user_skills = set(row[0] for row in cursor.fetchall())
    if not prefs["share_skills"]:
        user_skills = set()

    # 恋爱模式：获取当前用户性别，只推荐异性
    user_gender = None
    target_genders = None  # 恋爱模式要推荐的性别
    if mode == "love":
        cursor.execute("SELECT gender FROM users WHERE id=?", (user_id,))
        user_gender = cursor.fetchone()
        user_gender = user_gender[0] if user_gender else None
        if user_gender == "男":
            target_genders = {"女"}  # 男用户推荐女
        elif user_gender == "女":
            target_genders = {"男"}  # 女用户推荐男

    cursor.execute("SELECT id FROM users WHERE id != ?", (user_id,))
    all_users = [row[0] for row in cursor.fetchall()]

    scored = []
    for other in all_users:
        # 跳过已是好友的用户
        if other in user_friends:
            continue
        # 跳过前端已滑过的用户（暂时过滤）
        if other in exclude_ids:
            continue

        # 恋爱模式：只推荐异性
        if target_genders:
            cursor.execute("SELECT gender FROM users WHERE id=?", (other,))
            other_gender = cursor.fetchone()
            other_gender = other_gender[0] if other_gender else None
            if other_gender not in target_genders:
                continue

        cursor.execute("SELECT friend_id FROM friendships WHERE user_id=?", (other,))
        other_friends = set(row[0] for row in cursor.fetchall())

        cursor.execute("SELECT interest FROM user_interests WHERE user_id=?", (other,))
        other_interests = set(row[0] for row in cursor.fetchall())

        cursor.execute("SELECT skill FROM user_skills WHERE user_id=?", (other,))
        other_skills = set(row[0] for row in cursor.fetchall())

        fi = psi_intersection(user_friends, other_friends)

        f_score = _jaccard(user_friends, other_friends, fi)
        # 兴趣/技能：从“集合交集 + Jaccard”升级为“语义向量相似度”
        if _SEMANTIC_AVAILABLE:
            i_score, ii_cnt = _semantic_set_similarity(user_interests, other_interests)
            s_score, si_cnt = _semantic_set_similarity(user_skills, other_skills)
        else:
            # 若未安装 sentence-transformers，保证系统仍可工作（回退为原始 PSI+Jaccard）。
            ii = psi_intersection(user_interests, other_interests)
            si = psi_intersection(user_skills, other_skills)
            i_score = _jaccard(user_interests, other_interests, ii)
            s_score = _jaccard(user_skills, other_skills, si)
            ii_cnt = len(ii)
            si_cnt = len(si)

        other_personality = get_personality_norm_pair_cached(other) if prefs.get("share_personality", True) else None
        # 双向检查：如果候选人关闭了性格分享，也不使用其性格向量
        if other_personality is not None:
            other_prefs = load_matching_prefs(other)
            if not other_prefs.get("share_personality", True):
                other_personality = None
        trait_mix, trait_sim, trait_comp = trait_similarity_mixed(
            user_personality, other_personality, mode
        )

        total = w_f * f_score + w_i * i_score + w_s * s_score + w_t * trait_mix
        if total > 0:
            scored.append(
                (
                    other,
                    total,
                    f_score,
                    i_score,
                    s_score,
                    len(fi),
                    ii_cnt,
                    si_cnt,
                    trait_mix,
                    trait_sim,
                    trait_comp,
                )
            )

    scored.sort(key=lambda x: -x[1])

    # 按分数分层，随机打乱同档内的候选，实现"换一批"效果
    # 分数差值 < 0.05 视为同一档，保持相对排序稳定
    if len(scored) > 1:
        tiered = []
        current_tier = [scored[0]]
        for i in range(1, len(scored)):
            if abs(scored[i][1] - current_tier[0][1]) < 0.05:
                current_tier.append(scored[i])
            else:
                random.shuffle(current_tier)
                tiered.extend(current_tier)
                current_tier = [scored[i]]
        if current_tier:
            random.shuffle(current_tier)
            tiered.extend(current_tier)
        scored = tiered

    conn.close()
    start = max(0, int(skip))
    end = start + max(1, int(top_n))
    return scored[start:end]


def get_recommendations_multi(user_id, mode="friend", top_n=5, output_mode="id_only"):
    rows = _compute_multi_recommendations(user_id, mode, top_n)
    if output_mode == "id_only":
        return [r[0] for r in rows]
    if output_mode == "full_score":
        return [(r[0], r[1]) for r in rows]
    return [r[0] for r in rows]


def _match_reason_text(
    common_interests,
    common_skills,
    common_friends,
    mode,
    trait_mix=0.0,
):
    """生成可读的匹配理由。"""
    parts = []
    if common_interests > 0:
        parts.append(f"你们有 {common_interests} 个共同兴趣")
    if common_skills > 0:
        parts.append(f"你们有 {common_skills} 项共同技能")
    if common_friends > 0:
        parts.append(f"你们有 {common_friends} 位共同好友")
    if trait_mix and trait_mix > 0:
        parts.append(f"性格匹配 {round(trait_mix * 100)}%")
    return "、".join(parts) if parts else "可能合拍"


_VALID_MODES = frozenset({"friend", "team", "love"})


def _detailed_payload(user_id, mode, top_n=8, skip=0, exclude_ids=None):
    if exclude_ids is None:
        exclude_ids = set()
    w_f, w_i, w_s, w_t = _mode_weights(mode)
    rows = _compute_multi_recommendations(user_id, mode, top_n, skip, exclude_ids)
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    out = []
    for rid, total, f_sc, i_sc, s_sc, fi_cnt, ii_cnt, si_cnt, trait_mix, trait_sim, trait_comp in rows:
        cursor.execute("SELECT username, gender FROM users WHERE id=?", (rid,))
        row = cursor.fetchone()
        if not row:
            continue
        username, gender = row
        cursor.execute(
            "SELECT interest FROM user_interests WHERE user_id=? ORDER BY id LIMIT 6",
            (rid,),
        )
        interest_tags = [r[0] for r in cursor.fetchall()]
        cursor.execute(
            "SELECT skill FROM user_skills WHERE user_id=? ORDER BY id LIMIT 6",
            (rid,),
        )
        skill_tags = [r[0] for r in cursor.fetchall()]
        out.append(
            {
                "id": rid,
                "username": username,
                "gender": gender,
                "score": round(total, 4),
                "reason": _match_reason_text(ii_cnt, si_cnt, fi_cnt, mode, trait_mix),
                "interests_preview": interest_tags,
                "skills_preview": skill_tags,
                "dims": {
                    "friend_jaccard": round(f_sc, 4),
                    "interest_jaccard": round(i_sc, 4),
                    "skill_jaccard": round(s_sc, 4),
                    "common_interests": ii_cnt,
                    "common_skills": si_cnt,
                    "common_friends": fi_cnt,
                    "trait_mix": round(trait_mix, 4),
                    "trait_similar": round(trait_sim, 4),
                    "trait_complement": round(trait_comp, 4),
                    "weights": {
                        "friend": w_f,
                        "interest": w_i,
                        "skill": w_s,
                        "personality": w_t,
                    },
                },
            }
        )
    conn.close()
    return out


def _log_recommendation_snapshot(user_id, mode, payload):
    _ensure_history_table()
    conn = sqlite3.connect(DATABASE_PATH)
    conn.execute(
        "INSERT INTO recommendation_history (user_id, mode, snapshot_json) VALUES (?,?,?)",
        (user_id, mode, json.dumps(payload, ensure_ascii=False)),
    )
    conn.commit()
    conn.close()


@recommend_bp.route("/api/recommend/<mode>")
def api_recommend(mode):
    if "user_id" not in session:
        return jsonify({"error": "未登录"}), 401
    if mode not in _VALID_MODES:
        return jsonify({"error": "无效模式"}), 400
    uid = session["user_id"]
    rec_ids = get_recommendations_multi(uid, mode=mode, output_mode="id_only")
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    result = []
    for rid in rec_ids:
        cursor.execute("SELECT username FROM users WHERE id=?", (rid,))
        row = cursor.fetchone()
        if row:
            result.append({"id": rid, "username": row[0]})
    conn.close()
    return jsonify(result)


@recommend_bp.route("/api/recommend/<mode>/detailed")
def api_recommend_detailed(mode):
    if "user_id" not in session:
        return jsonify({"error": "未登录"}), 401
    if mode not in _VALID_MODES:
        return jsonify({"error": "无效模式"}), 400
    uid = session["user_id"]
    top_n = request.args.get("top", default=8, type=int) or 8
    top_n = max(1, min(top_n, 20))
    skip = request.args.get("skip", default=0, type=int) or 0
    skip = max(0, min(skip, 100))
    # 支持 exclude 参数，排除指定用户（前端已滑过的用户）
    exclude_str = request.args.get("exclude", default="", type=str) or ""
    exclude_ids = set()
    if exclude_str:
        for eid in exclude_str.split(","):
            try:
                exclude_ids.add(int(eid.strip()))
            except (ValueError, TypeError):
                pass
    payload = _detailed_payload(uid, mode, top_n, skip, exclude_ids)
    if skip == 0:
        _log_recommendation_snapshot(uid, mode, payload)
    return jsonify(
        {
            "mode": mode,
            "items": payload,
            "privacy_note": "综合分由四部分组成：好友维度使用 PSI 交集原型并计算 Jaccard；兴趣与技能维度使用标签语义向量的余弦相似度；性格维度使用 Big Five 向量余弦相似度，并支持相似+互补混合策略。您可在隐私设置中关闭部分维度参与匹配。",
        }
    )


@recommend_bp.route("/api/recommend/history")
def api_recommend_history():
    if "user_id" not in session:
        return jsonify({"error": "未登录"}), 401
    _ensure_history_table()
    uid = session["user_id"]
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    c.execute(
        """
        SELECT id, mode, created_at, snapshot_json
        FROM recommendation_history
        WHERE user_id=?
        ORDER BY id DESC
        LIMIT 40
        """,
        (uid,),
    )
    rows = c.fetchall()
    conn.close()
    out = []
    for hid, m, created, snap in rows:
        try:
            items = json.loads(snap)
        except json.JSONDecodeError:
            items = []
        out.append({"id": hid, "mode": m, "created_at": created, "items": items})
    return jsonify(out)


@recommend_bp.route("/api/recommend/history/<int:hid>", methods=["DELETE"])
def api_recommend_history_delete(hid):
    """删除单条推荐记录。"""
    if "user_id" not in session:
        return jsonify({"error": "未登录"}), 401
    uid = session["user_id"]
    _ensure_history_table()
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    c.execute(
        "DELETE FROM recommendation_history WHERE id=? AND user_id=?",
        (hid, uid),
    )
    conn.commit()
    deleted = c.rowcount
    conn.close()
    if not deleted:
        return jsonify({"error": "记录不存在或无权删除"}), 404
    return jsonify({"ok": True})
