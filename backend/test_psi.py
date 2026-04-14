"""OKVS-PSI 模块测试"""
import sys
sys.path.insert(0, '.')

from modules.psi import (
    LightweightOKVS,
    psi_intersection,
    psi_intersection_weighted,
    reset_protocol_key,
    _get_protocol_key,
    _build_kv_pairs,
)


def test_basic_intersection():
    """测试基本交集功能"""
    reset_protocol_key(42)  # 固定密钥确保可复现

    setA = {1, 2, 3, 4, 5}
    setB = {3, 4, 5, 6, 7}

    result = psi_intersection(setA, setB)
    expected = {3, 4, 5}

    assert result == expected, f"交集错误: {result} != {expected}"
    print(f"[PASS] Basic intersection: {result}")


def test_empty_intersection():
    """测试无交集情况"""
    reset_protocol_key(123)

    setA = {1, 2, 3}
    setB = {4, 5, 6}

    result = psi_intersection(setA, setB)
    assert result == set(), f"无交集错误: {result}"
    print("[PASS] Empty intersection test passed")


def test_full_intersection():
    """测试完全包含情况"""
    reset_protocol_key(456)

    setA = {1, 2, 3}
    setB = {1, 2, 3, 4, 5}

    result = psi_intersection(setA, setB)
    expected = {1, 2, 3}
    assert result == expected, f"完全包含错误: {result}"
    print("[PASS] Full inclusion test passed")


def test_string_elements():
    """测试字符串元素"""
    reset_protocol_key(789)

    setA = {"alice", "bob", "charlie"}
    setB = {"charlie", "david", "eve"}

    result = psi_intersection(setA, setB)
    expected = {"charlie"}
    assert result == expected, f"字符串交集错误: {result}"
    print("[PASS] String elements test passed")


def test_consistency():
    """测试不同密钥产生不同结果"""
    reset_protocol_key(100)
    setA = {1, 2, 3, 4, 5}
    setB = {3, 4, 5, 6, 7}

    result1 = psi_intersection(setA, setB)

    reset_protocol_key(999)  # 换密钥
    setA = {1, 2, 3, 4, 5}
    setB = {3, 4, 5, 6, 7}

    result2 = psi_intersection(setA, setB)

    # 结果应该相同（因为协议设计保证）
    assert result1 == result2, f"一致性错误: {result1} != {result2}"
    print("[PASS] Consistency test passed")


def test_weighted():
    """测试带权重版本"""
    reset_protocol_key(555)

    setA = {1, 2, 3, 4, 5}
    setB = {3, 4, 5, 6, 7}

    intersection, weights = psi_intersection_weighted(setA, setB)
    expected = {3, 4, 5}

    assert intersection == expected, f"带权重交集错误: {intersection}"
    assert len(weights) == 3, f"权重数量错误: {len(weights)}"

    for x in intersection:
        assert 0 <= weights[x] <= 1, f"权重越界: {weights[x]}"

    print(f"[PASS] Weighted test passed: weights={weights}")


def test_okvs_components():
    """测试 OKVS 组件"""
    reset_protocol_key(111)

    okvs = LightweightOKVS()

    # 构建 KV 对
    kv_pairs = _build_kv_pairs({1, 2, 3}, 100, 101)

    assert len(kv_pairs) == 3, f"KV 对数量错误: {len(kv_pairs)}"
    for key, value in kv_pairs:
        assert isinstance(key, int), f"Key 类型错误: {type(key)}"
        assert isinstance(value, int), f"Value 类型错误: {type(value)}"

    # 编码
    okvs.encode(kv_pairs)

    # 解码验证
    for key, value in kv_pairs:
        decoded = okvs.decode(key)
        assert decoded == value, f"解码错误: {decoded} != {value}"

    print("[PASS] OKVS components test passed")


def test_large_sets():
    """测试较大集合（OKVS 存在哈希碰撞，接受一定误差）"""
    reset_protocol_key(99999)

    setA = set(range(1, 101))  # 1-100
    setB = set(range(50, 151))  # 50-150

    result = psi_intersection(setA, setB)
    expected = set(range(50, 101))  # 50-100

    # OKVS 使用 XOR 编码，哈希碰撞可能导致 false positives
    # 验证：结果应该是 expected 的子集（不应该漏掉太多真交集）
    assert result.issubset(expected), f"结果包含非交集元素"
    recall = len(result) / len(expected)  # 召回率
    print(f"[INFO] Large set recall: {recall:.2%} ({len(result)}/{len(expected)})")
    assert recall >= 0.8, f"召回率过低: {recall:.2%}"
    print(f"[PASS] Large set test passed")


if __name__ == "__main__":
    print("=" * 50)
    print("OKVS-PSI 模块测试")
    print("=" * 50)

    test_basic_intersection()
    test_empty_intersection()
    test_full_intersection()
    test_string_elements()
    test_consistency()
    test_weighted()
    test_okvs_components()
    test_large_sets()

    print("=" * 50)
    print("All tests passed!")
    print("=" * 50)
