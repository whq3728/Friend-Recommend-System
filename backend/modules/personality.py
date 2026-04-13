"""
Big Five 性格建模（5 维向量）与相似度计算。

约定：
- 每个维度取值范围为 0..1（由问卷 1..5 映射而来）
- 推荐中使用 L2 归一化后计算余弦相似度
- “互补”策略：对候选人的向量做 (1 - x) 后再计算余弦相似度
"""

from __future__ import annotations

import sqlite3
import threading
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np

from config import DATABASE_PATH


DIM_KEYS = ("extro", "agreeableness", "conscientiousness", "neuroticism", "openness")
DIM_COUNT = 5

# 10 题到 5 维的映射：每一维两题
# 题目顺序由前端一致维护（问卷或问卷答案）
QUESTION_DIM_INDEX = (0, 0, 1, 1, 2, 2, 3, 3, 4, 4)

# 性格表：用于推荐与资料补全
PERSONALITY_TABLE = "user_personality_bigfive"

# 推荐中性格“相似/互补”混合比例（alpha 表示相似权重）
TRAIT_SIMILAR_ALPHA = {
    "friend": 0.7,
    "team": 0.5,
    "love": 0.6,
}

_cache_lock = threading.Lock()
_personality_norm_cache: Dict[int, Optional[Tuple[np.ndarray, np.ndarray]]] = {}
# user_id -> (vec_norm, vec_comp_norm)


def _conn() -> sqlite3.Connection:
    return sqlite3.connect(DATABASE_PATH)


def ensure_personality_table() -> None:
    """确保 Big Five 性格表存在（向后兼容）。"""
    conn = _conn()
    try:
        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {PERSONALITY_TABLE} (
                user_id INTEGER PRIMARY KEY,
                extro REAL NOT NULL,
                agreeableness REAL NOT NULL,
                conscientiousness REAL NOT NULL,
                neuroticism REAL NOT NULL,
                openness REAL NOT NULL
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


def bigfive_from_quick_1to5(values_1to5: Dict[str, int | float]) -> Dict[str, float]:
    """
    快速选择：每维提供 1..5 的值，转换到 0..1。
    """
    out: Dict[str, float] = {}
    for k in DIM_KEYS:
        v = values_1to5.get(k)
        if v is None or v == "":
            raise ValueError(f"缺少维度：{k}")
        v = float(v)
        if v < 1 or v > 5:
            raise ValueError(f"{k} 取值必须在 1..5")
        out[k] = _clamp01((v - 1.0) / 4.0)
    return out


def bigfive_from_questionnaire_1to5(answers_1to5: List[int | float]) -> Dict[str, float]:
    """
    问卷：10 题，每题 1..5，按维度平均后转换到 0..1。
    """
    if len(answers_1to5) != 10:
        raise ValueError("问卷答案必须为 10 个值")
    # 先在 1..5 空间做每维平均
    dim_sum = [0.0] * DIM_COUNT
    dim_cnt = [0] * DIM_COUNT
    for i, a in enumerate(answers_1to5):
        v = float(a)
        if v < 1 or v > 5:
            raise ValueError(f"第 {i + 1} 题取值必须在 1..5")
        dim = QUESTION_DIM_INDEX[i]
        dim_sum[dim] += v
        dim_cnt[dim] += 1
    out: Dict[str, float] = {}
    for dim, key in enumerate(DIM_KEYS):
        avg_1to5 = dim_sum[dim] / max(1, dim_cnt[dim])
        out[key] = _clamp01((avg_1to5 - 1.0) / 4.0)
    return out


def upsert_personality_bigfive(user_id: int, vec_0to1: Dict[str, float]) -> None:
    """写入/更新 Big Five 向量（0..1）。"""
    ensure_personality_table()
    conn = _conn()
    try:
        vals = [vec_0to1.get(k) for k in DIM_KEYS]
        if any(v is None for v in vals):
            raise ValueError("bigfive 向量缺失维度")
        conn.execute(
            f"""
            INSERT INTO {PERSONALITY_TABLE}
                (user_id, extro, agreeableness, conscientiousness, neuroticism, openness)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                extro=excluded.extro,
                agreeableness=excluded.agreeableness,
                conscientiousness=excluded.conscientiousness,
                neuroticism=excluded.neuroticism,
                openness=excluded.openness
            """,
            (user_id, *[float(_clamp01(v)) for v in vals]),
        )
        conn.commit()
    finally:
        conn.close()

    # 更新后清空缓存，避免脏读
    with _cache_lock:
        _personality_norm_cache.pop(int(user_id), None)


def load_personality_bigfive(user_id: int) -> Optional[Dict[str, float]]:
    """读取 Big Five 向量（0..1）。"""
    ensure_personality_table()
    conn = _conn()
    try:
        c = conn.cursor()
        c.execute(
            f"""
            SELECT extro, agreeableness, conscientiousness, neuroticism, openness
            FROM {PERSONALITY_TABLE}
            WHERE user_id=?
            """,
            (user_id,),
        )
        row = c.fetchone()
        if not row:
            return None
        return {k: float(row[i]) for i, k in enumerate(DIM_KEYS)}
    finally:
        conn.close()


def _vec_to_norm_and_comp(vec: np.ndarray) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
    """
    返回 (vec_norm, comp_norm)：
    - vec_norm：vec 的 L2 归一化版本（cosine 需要）
    - comp_norm：(1 - vec) 的 L2 归一化版本
    """
    norm = float(np.linalg.norm(vec))
    vec_norm = vec / norm if norm > 0 else None
    comp = 1.0 - vec
    comp_norm_val = float(np.linalg.norm(comp))
    comp_norm = comp / comp_norm_val if comp_norm_val > 0 else None
    return vec_norm, comp_norm


def get_personality_norm_pair_cached(user_id: int) -> Optional[Tuple[np.ndarray, np.ndarray]]:
    """
    返回 (vec_norm, vec_comp_norm)：
    - 若用户未填写性格，则返回 None
    - 结果会进行缓存，避免重复查询与重复归一化
    """
    uid = int(user_id)
    with _cache_lock:
        if uid in _personality_norm_cache:
            return _personality_norm_cache[uid]

    ensure_personality_table()
    conn = _conn()
    try:
        c = conn.cursor()
        c.execute(
            f"""
            SELECT extro, agreeableness, conscientiousness, neuroticism, openness
            FROM {PERSONALITY_TABLE}
            WHERE user_id=?
            """,
            (uid,),
        )
        row = c.fetchone()
        if not row:
            with _cache_lock:
                _personality_norm_cache[uid] = None
            return None

        vec = np.array([float(x) for x in row], dtype=np.float32)
        vec_norm, comp_norm = _vec_to_norm_and_comp(vec)
        if vec_norm is None or comp_norm is None:
            # 若任一侧归一化失败（除 0），按 0 相似处理，因此也缓存为 None
            with _cache_lock:
                _personality_norm_cache[uid] = None
            return None

        pair = (vec_norm.astype(np.float32), comp_norm.astype(np.float32))
        with _cache_lock:
            _personality_norm_cache[uid] = pair
        return pair
    finally:
        conn.close()


def cosine_from_normed(vec_a_norm: Optional[np.ndarray], vec_b_norm: Optional[np.ndarray]) -> float:
    if vec_a_norm is None or vec_b_norm is None:
        return 0.0
    # vec_norm 已归一化，因此点积即余弦相似度
    v = float(np.dot(vec_a_norm, vec_b_norm))
    # 非负向量下理论上应为 0..1，这里做安全裁剪
    return max(0.0, min(1.0, v))


def trait_similarity_mixed(
    user_norm_pair: Optional[Tuple[np.ndarray, np.ndarray]],
    other_norm_pair: Optional[Tuple[np.ndarray, np.ndarray]],
    mode: str,
) -> Tuple[float, float, float]:
    """
    返回 (trait_mix_score, trait_sim_score, trait_complement_score)
    - trait_sim_score：cos(user_vec, other_vec)
    - trait_complement_score：cos(user_vec, (1 - other_vec))
    - trait_mix_score：alpha * sim + (1 - alpha) * complement
    """
    if not user_norm_pair or not other_norm_pair:
        return 0.0, 0.0, 0.0

    alpha = float(TRAIT_SIMILAR_ALPHA.get(mode, 0.6))
    user_vec_norm, _ = user_norm_pair
    other_vec_norm, other_comp_norm = other_norm_pair

    sim = cosine_from_normed(user_vec_norm, other_vec_norm)
    comp = cosine_from_normed(user_vec_norm, other_comp_norm)
    mix = alpha * sim + (1.0 - alpha) * comp
    return mix, sim, comp


def bigfive_completion_ratio(vec_0to1: Optional[Dict[str, float]]) -> int:
    """用于前端展示：有向量则视为 100%。"""
    return 100 if vec_0to1 else 0


