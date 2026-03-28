# modules/psi.py
import hashlib
import random


class OKVS:
    """轻量级 OKVS 模块，原型协议实现"""

    def __init__(self):
        self.table = dict()

    @staticmethod
    def hash_item(item):
        return hashlib.sha256(str(item).encode()).hexdigest()

    def encode(self, items, max_value=1_000_000):
        for item in items:
            h = self.hash_item(item)
            mask = random.randint(1, max_value)
            self.table[h] = mask ^ int(h[:8], 16)

    def query(self, items):
        intersection = set()
        for item in items:
            h = self.hash_item(item)
            if h in self.table:
                stored_val = self.table[h]
                check_val = stored_val ^ int(h[:8], 16)
                if check_val is not None:
                    intersection.add(item)
        return intersection


def psi_intersection(setA, setB):
    """OKVS-PSI 协议原型：对 setA 编码，用 setB 查询交集。"""
    okvs = OKVS()
    okvs.encode(setA)
    return okvs.query(setB)
