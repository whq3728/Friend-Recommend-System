# modules/psi.py
"""
OKVS-PSI 协议实现
基于论文风格的轻量级 OKVS（Oblivious Key-Value Store）

核心思想：
1. 对每个元素 x，使用 PRF 生成 value = F(k1, x) ^ F(k2, x)
2. 将 (x, value) 键值对通过多哈希编码存入 OKVS
3. 查询时通过 decode 恢复 value
4. 多方结果异或聚合：交集元素 x 会满足 F_A(x) ^ F_B(x) ^ ... = 0
"""
import hashlib
import random
import os


# =========================
# 协议配置（可从环境变量覆盖）
# =========================
_PROTOCOL_KEY = None  # 全局密钥，模拟协议执行


def _get_protocol_key():
    """获取协议密钥，支持环境变量配置"""
    global _PROTOCOL_KEY
    if _PROTOCOL_KEY is None:
        env_key = os.environ.get("PSI_PROTOCOL_KEY")
        if env_key:
            _PROTOCOL_KEY = int(env_key)
        else:
            _PROTOCOL_KEY = random.randint(1, 1_000_000)
    return _PROTOCOL_KEY


def reset_protocol_key(new_key=None):
    """重置协议密钥（用于测试或重新初始化）"""
    global _PROTOCOL_KEY
    if new_key is not None:
        _PROTOCOL_KEY = new_key
    else:
        _PROTOCOL_KEY = None


# =========================
# PRF（伪随机函数）
# =========================
def _prf(secret, item):
    """基于 SHA256 的伪随机函数"""
    h = hashlib.sha256((str(secret) + str(item)).encode()).hexdigest()
    return int(h[:16], 16)  # 使用更多位提高随机性


# =========================
# LightweightOKVS（论文风格🔥）
# =========================
class LightweightOKVS:
    """
    轻量级 OKVS 实现（基于 PaXoS 风格的多哈希映射）

    特性：
    - 多哈希分散存储，避免单点冲突
    - XOR 编码，支持解码恢复
    - 固定长度的向量存储，压缩率高
    """

    def __init__(self, m: int = 10007, k: int = 3):
        """
        初始化 OKVS

        Args:
            m: 哈希表大小（建议选大素数）
            k: 每个元素分散到的位置数（k 越大冲突越少）
        """
        self.m = m
        self.k = k
        self.table = [0] * m
        # 多组 salts 用于生成 k 个哈希位置
        self.salts = [str(i) for i in range(k)]

    def _hash_positions(self, item) -> list:
        """
        计算元素 item 在哈希表中的 k 个位置

        Args:
            item: 要哈希的元素

        Returns:
            k 个位置的列表
        """
        positions = []
        for salt in self.salts:
            h = hashlib.sha256((str(item) + salt).encode()).hexdigest()
            positions.append(int(h, 16) % self.m)
        return positions

    def encode(self, kv_pairs: list):
        """
        将键值对集合编码到 OKVS

        Args:
            kv_pairs: [(key, value), ...] 键值对列表
        """
        for key, value in kv_pairs:
            positions = self._hash_positions(key)
            # 将 value 通过 XOR 分散到多个位置
            for pos in positions:
                self.table[pos] ^= value

    def decode(self, key) -> int:
        """
        根据 key 恢复其对应的 value

        Args:
            key: 要查询的键

        Returns:
            恢复的 value
        """
        positions = self._hash_positions(key)
        val = 0
        for pos in positions:
            val ^= self.table[pos]
        return val

    def get_table(self) -> list:
        """返回内部表（用于调试或序列化）"""
        return self.table.copy()


# =========================
# PSI 协议核心（论文风格🔥）
# =========================
def _build_kv_pairs(data_set: set, k1: int, k2: int) -> list:
    """
    构建键值对集合（协议预处理步骤）

    对于集合中的每个元素 x，生成：
        value = PRF(k1, x) ^ PRF(k2, x)

    Args:
        data_set: 输入集合
        k1, k2: PRF 密钥

    Returns:
        [(x, value), ...] 键值对列表
    """
    kv_pairs = []
    for x in data_set:
        v = _prf(k1, x) ^ _prf(k2, x)
        kv_pairs.append((x, v))
    return kv_pairs


def psi_intersection(setA: set, setB: set) -> set:
    """
    OKVS-PSI 交集协议（对称版本）

    协议流程：
    1. 双方使用相同的 PRF 密钥
    2. 各自构建 OKVS
    3. 交集判定：若 x ∈ setA ∩ setB，则两边解码出的值相同

    Args:
        setA: 集合 A
        setB: 集合 B

    Returns:
        交集集合
    """
    # 获取协议密钥
    k = _get_protocol_key()

    # =========================
    # A方：构造 KV 并编码
    # =========================
    kv_A = _build_kv_pairs(setA, k, k + 1)
    okvs_A = LightweightOKVS()
    okvs_A.encode(kv_A)

    # =========================
    # B方：构造 KV 并编码
    # =========================
    kv_B = _build_kv_pairs(setB, k, k + 1)
    okvs_B = LightweightOKVS()
    okvs_B.encode(kv_B)

    # =========================
    # 交集判定（核心🔥）
    # =========================
    # 理论上：交集元素满足 vA = vB，即 vA ^ vB = 0
    # 但由于 XOR 是线性的，我们需要检查元素是否在两边都能被正确"解码"
    intersection = set()

    for x in setB:
        vA = okvs_A.decode(x)
        vB = okvs_B.decode(x)
        # XOR 判定：交集元素在双方解码后值应一致
        if vA == vB:
            intersection.add(x)

    return intersection


def psi_intersection_weighted(setA: set, setB: set) -> tuple:
    """
    带权重的 PSI：返回交集和每个交集元素的权重（用于推荐评分）

    权重定义：value = PRF(k1, x) ^ PRF(k2, x)
    交集元素的权重 = 该值的某种归一化表示
    """
    k = _get_protocol_key()

    kv_A = _build_kv_pairs(setA, k, k + 1)
    okvs_A = LightweightOKVS()
    okvs_A.encode(kv_A)

    kv_B = _build_kv_pairs(setB, k, k + 1)
    okvs_B = LightweightOKVS()
    okvs_B.encode(kv_B)

    intersection = set()
    weights = {}

    for x in setB:
        vA = okvs_A.decode(x)
        vB = okvs_B.decode(x)
        if vA == vB:
            intersection.add(x)
            # 使用解码值的某种映射作为权重
            weights[x] = abs(vA) % 100 / 100.0

    return intersection, weights
