"""
PSI 加密效果演示脚本

演示内容：
1. 原始数据（明文）
2. OKVS 编码后的密文（哈希表内容）
3. 交集计算过程
4. 最终结果
"""
import sys
sys.path.insert(0, '.')

from modules.psi import (
    LightweightOKVS,
    psi_intersection,
    reset_protocol_key,
    _prf,
)


def demo_okvs_encoding():
    """演示 OKVS 编码过程"""
    print("=" * 60)
    print("演示 1: OKVS 编码过程")
    print("=" * 60)

    # 模拟 A 方数据
    print("\n[原始数据] A 方的朋友列表:")
    friends_A = {"alice", "bob", "charlie", "david"}
    for name in sorted(friends_A):
        print(f"  - {name}")

    # 构建 KV 对
    k1, k2 = 100, 101
    print(f"\n[密钥] k1={k1}, k2={k2}")

    print("\n[键值对生成] value = PRF(k1, x) XOR PRF(k2, x)")
    kv_pairs = []
    for name in friends_A:
        v1 = _prf(k1, name)
        v2 = _prf(k2, name)
        v = v1 ^ v2
        kv_pairs.append((name, v))
        print(f"  {name:10} -> PRF({k1}, '{name}')={v1}")
        print(f"              PRF({k2}, '{name}')={v2}")
        print(f"              XOR  = {v}")
        print()

    # OKVS 编码
    okvs = LightweightOKVS(m=100, k=3)
    print(f"[OKVS] 表大小 m={okvs.m}, 哈希函数数 k={okvs.k}")
    okvs.encode(kv_pairs)

    print("\n[编码后] OKVS 哈希表（部分展示）:")
    # 只展示非零位置
    nonzero_count = sum(1 for v in okvs.table if v != 0)
    print(f"  非零位置数: {nonzero_count}/{okvs.m}")
    print(f"  原始数据: {len(friends_A)} 个元素")
    print(f"  压缩比: {len(friends_A) / nonzero_count:.2f}x")

    print("\n  哈希表前 20 个位置:")
    for i in range(20):
        val = okvs.table[i]
        marker = f" <- {kv_pairs[0][0]}" if okvs.table[i] != 0 else ""
        print(f"    [{i:2}]: {val}{marker}")


def demo_psi_protocol():
    """演示完整的 PSI 协议"""
    print("\n" + "=" * 60)
    print("演示 2: 完整 PSI 协议流程")
    print("=" * 60)

    reset_protocol_key(42)  # 固定密钥

    # A 方和 B 方的数据
    friends_A = {"alice", "bob", "charlie"}
    friends_B = {"bob", "charlie", "david", "eve"}

    print("\n[A 方数据]")
    for name in sorted(friends_A):
        print(f"  {name}")

    print("\n[B 方数据]")
    for name in sorted(friends_B):
        print(f"  {name}")

    print("\n[协议执行] 双方独立计算...")
    result = psi_intersection(friends_A, friends_B)

    print("\n[结果] 交集:")
    if result:
        for name in sorted(result):
            print(f"  {name} (同时在 A 和 B 的列表中)")
    else:
        print("  无交集")


def demo_security():
    """演示安全性：无法从 OKVS 反推原始数据"""
    print("\n" + "=" * 60)
    print("演示 3: 安全性说明")
    print("=" * 60)

    reset_protocol_key(12345)

    # 只有 Alice 的数据
    friends_A = {"alice"}
    okvs = LightweightOKVS()

    kv_pairs = [("alice", _prf(12345, "alice") ^ _prf(12346, "alice"))]
    okvs.encode(kv_pairs)

    print("\n[攻击场景] 假设攻击者获得了 OKVS 哈希表:")
    print("  表内容:", okvs.table[:30])

    print("\n[尝试反推]")
    print("  - 攻击者能看到: OKVS 表中的值（异或后的结果）")
    print("  - 攻击者不知道: PRF 密钥 k1, k2")
    print("  - 攻击者无法确定: 具体是哪个用户")
    print("\n[原因]")
    print("  1. 单个位置的 XOR 值 = 多个元素的 PRF 值异或结果")
    print("  2. 攻击者无法从密文判断哪个位置对应哪个元素")
    print("  3. 即使猜测元素，也需要 PRF 密钥才能验证")


def demo_collision():
    """演示哈希碰撞的影响"""
    print("\n" + "=" * 60)
    print("演示 4: 哈希碰撞说明")
    print("=" * 60)

    reset_protocol_key(999)

    # 两个不相关的集合
    setA = {100, 200, 300}
    setB = {400, 500, 600}

    result = psi_intersection(setA, setB)

    print("\n[A 方数据:", setA)
    print("B 方数据:", setB)
    print("真实交集: 空集 (无交集)")

    if result:
        print(f"\n[注意] 由于哈希碰撞，PSI 返回了误报: {result}")
        print("       这是 OKVS 概率性数据结构的固有特性")
    else:
        print("\n[无碰撞] 此次测试没有产生误报")


def demo_comparison():
    """对比原始方法 vs OKVS-PSI"""
    print("\n" + "=" * 60)
    print("演示 5: 方案对比")
    print("=" * 60)

    reset_protocol_key(100)

    friends_A = {"alice", "bob", "charlie", "david", "eve"}
    friends_B = {"bob", "charlie", "frank", "grace"}

    print("\n[方案1] 传统方法（直接比较）")
    print("  A 方发送: 完整列表给 B 方")
    print(f"  数据泄露: {list(friends_A)}")
    print("\n  B 方接收后可以知道 A 方的所有朋友！")

    print("\n[方案2] OKVS-PSI（隐私保护）")
    print("  A 方发送: OKVS 哈希表")
    okvs = LightweightOKVS(m=50)
    k1, k2 = 100, 101
    kv_A = [(x, _prf(k1, x) ^ _prf(k2, x)) for x in friends_A]
    okvs.encode(kv_A)
    print(f"  数据泄露: {okvs.table[:20]}...")
    print("  B 方无法从中得知 A 方的具体朋友！")

    print("\n[结果对比]")
    traditional_result = friends_A & friends_B
    psi_result = psi_intersection(friends_A, friends_B)
    print(f"  传统方法结果: {traditional_result}")
    print(f"  PSI 方法结果: {psi_result}")


def main():
    print("╔════════════════════════════════════════════════════════════╗")
    print("║              PSI 加密效果演示                                ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print()
    print("本演示展示 Private Set Intersection (PSI) 的加密原理和效果")
    print()

    demo_okvs_encoding()
    demo_psi_protocol()
    demo_security()
    demo_collision()
    demo_comparison()

    print("\n" + "=" * 60)
    print("演示结束")
    print("=" * 60)


if __name__ == "__main__":
    main()
