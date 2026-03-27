"""
测试 s07 TaskManager 的两个问题：
1. addBlockedBy 是否双向维护 blocks？
2. _clear_dependency 是否正确工作？
"""

import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "agents"))
from s07_task_system import TaskManager

TEST_DIR = Path(__file__).parent / ".test_tasks"


def setup():
    if TEST_DIR.exists():
        shutil.rmtree(TEST_DIR)
    return TaskManager(TEST_DIR)


def show(tm, label):
    print(f"\n--- {label} ---")
    print(tm.list_all())
    for f in sorted(TEST_DIR.glob("task_*.json")):
        t = json.loads(f.read_text())
        print(f"  task_{t['id']}: blockedBy={t['blockedBy']} blocks={t['blocks']}")


def test_addblockedby_asymmetry():
    """验证 addBlockedBy 是否双向维护"""
    print("\n====== 测试1：addBlockedBy 是否双向维护 ======")
    tm = setup()

    tm.create("任务A")  # id=1
    tm.create("任务B")  # id=2

    # 用 addBlockedBy 建依赖：任务B 被 任务A 阻塞
    tm.update(2, add_blocked_by=[1])

    show(tm, "addBlockedBy([1]) 加到任务B 后")

    t1 = json.loads(tm.get(1))
    t2 = json.loads(tm.get(2))

    print(f"\n任务A.blocks = {t1['blocks']}  ← 期望 [2]，实际是？")
    print(f"任务B.blockedBy = {t2['blockedBy']}  ← 期望 [1]")

    if 2 not in t1['blocks']:
        print("❌ addBlockedBy 没有反向更新 blocks —— 不对称，是 bug")
    else:
        print("✅ addBlockedBy 双向维护正常")


def test_clear_dependency():
    """验证完成任务后 _clear_dependency 正确解锁下游"""
    print("\n====== 测试2：_clear_dependency 正确工作 ======")
    tm = setup()

    tm.create("任务1")  # id=1
    tm.create("任务2")  # id=2
    tm.create("任务3")  # id=3

    # 用 addBlocks 建链：1→2→3
    tm.update(1, add_blocks=[2])
    tm.update(2, add_blocks=[3])

    show(tm, "建完依赖后")

    # 完成任务1
    tm.update(1, status="completed")
    show(tm, "完成任务1 后")

    t2 = json.loads(tm.get(2))
    t3 = json.loads(tm.get(3))

    print(f"\n任务2.blockedBy = {t2['blockedBy']}  ← 期望 []")
    print(f"任务3.blockedBy = {t3['blockedBy']}  ← 期望 [2]（还没完成2）")

    if t2['blockedBy'] == [] and t3['blockedBy'] == [2]:
        print("✅ _clear_dependency 正确")
    else:
        print("❌ _clear_dependency 有问题")


def test_clear_dependency_via_addblockedby():
    """验证通过 addBlockedBy 建依赖后，_clear_dependency 也能正确解锁"""
    print("\n====== 测试3：addBlockedBy + _clear_dependency 联合测试 ======")
    tm = setup()

    tm.create("任务A")  # id=1
    tm.create("任务B")  # id=2

    # 用 addBlockedBy 建依赖：任务B 被 任务A 阻塞
    tm.update(2, add_blocked_by=[1])

    show(tm, "建完依赖后")

    # 完成任务A，应该解锁任务B
    tm.update(1, status="completed")
    show(tm, "完成任务A 后")

    t2 = json.loads(tm.get(2))
    print(f"\n任务B.blockedBy = {t2['blockedBy']}  ← 期望 []")

    if t2['blockedBy'] == []:
        print("✅ addBlockedBy + _clear_dependency 联合正确")
    else:
        print("❌ 任务B 没有被正确解锁")


if __name__ == "__main__":
    test_addblockedby_asymmetry()
    test_clear_dependency()
    test_clear_dependency_via_addblockedby()

    # 清理
    if TEST_DIR.exists():
        shutil.rmtree(TEST_DIR)
    print("\n====== 测试完成，临时文件已清理 ======")
