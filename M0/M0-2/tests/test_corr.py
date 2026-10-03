
import os
import sys

# 把上级目录（corr_tool.py 所在的地方）加入模块搜索路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from corr_tool import pearson_r


def test_完全正相关():
    r = pearson_r([1, 2, 3], [2, 4, 6])
    assert abs(r - 1.0) < 1e-9, f"期望 1.0，实际得到 {r}"


def test_完全负相关():
    r = pearson_r([1, 2, 3], [6, 4, 2])
    assert abs(r + 1.0) < 1e-9, f"期望 -1.0，实际得到 {r}"


def test_平移不变():
    # y = x + 3，仍是完美线性关系，相关系数应为 1.0
    r = pearson_r([1, 2, 3], [4, 5, 6])
    assert abs(r - 1.0) < 1e-9, f"期望 1.0，实际得到 {r}"


if __name__ == "__main__":
    test_完全正相关()
    test_完全负相关()
    test_平移不变()
    print("全部测试通过")