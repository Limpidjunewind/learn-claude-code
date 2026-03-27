"""
性能对比测试：O(n) vs O(k) 的 _clear_dependency 实现

设计：
- 固定 k=2（任务1 只阻塞 2 个下游任务）
- 增大 n（总任务数：100 / 1000 / 5000）
- 观察：原版随 n 增长，优化版不随 n 增长
"""

import json
import shutil
import time
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "agents"))
from s07_task_system import TaskManager

TEST_DIR = Path(__file__).parent / ".perf_tasks"


def setup(n: int, k: int) -> tuple[TaskManager, int]:
    """创建 n 个任务，其中 task_1 阻塞 k 个下游任务，其余 n-k-1 个任务无依赖。"""
    if TEST_DIR.exists():
        shutil.rmtree(TEST_DIR)
    tm = TaskManager(TEST_DIR)

    # 创建所有任务
    for i in range(n):
        tm.create(f"任务{i+1}")

    # task_1 阻塞 task_2 到 task_(k+1)
    tm.update(1, add_blocks=list(range(2, k + 2)))

    return tm


def strategy_original(tm: TaskManager, completed_id: int):
    """O(n)：扫所有文件"""
    for f in TEST_DIR.glob("task_*.json"):
        task = json.loads(f.read_text())
        if completed_id in task.get("blockedBy", []):
            task["blockedBy"].remove(completed_id)
            path = TEST_DIR / f"task_{task['id']}.json"
            path.write_text(json.dumps(task, indent=2))


def strategy_optimized(tm: TaskManager, completed_id: int):
    """O(k)：只看 blocks 列表"""
    completed = json.loads((TEST_DIR / f"task_{completed_id}.json").read_text())
    for blocked_id in completed.get("blocks", []):
        path = TEST_DIR / f"task_{blocked_id}.json"
        if path.exists():
            blocked = json.loads(path.read_text())
            if completed_id in blocked["blockedBy"]:
                blocked["blockedBy"].remove(completed_id)
                path.write_text(json.dumps(blocked, indent=2))


def run_test(n: int, k: int):
    print(f"\n{'='*50}")
    print(f"n={n} 个任务，k={k} 个下游")
    print(f"{'='*50}")

    # 测试原版
    tm = setup(n, k)
    start = time.perf_counter()
    strategy_original(tm, 1)
    t_original = (time.perf_counter() - start) * 1000
    files_scanned = n  # 扫了所有文件
    print(f"[原版 O(n)]    耗时: {t_original:.3f}ms  扫描文件数: {files_scanned}")

    # 测试优化版
    tm = setup(n, k)
    start = time.perf_counter()
    strategy_optimized(tm, 1)
    t_optimized = (time.perf_counter() - start) * 1000
    files_scanned_opt = k  # 只看 k 个下游
    print(f"[优化版 O(k)]  耗时: {t_optimized:.3f}ms  扫描文件数: {files_scanned_opt}")
    print(f"提速: {t_original/t_optimized:.1f}x")


if __name__ == "__main__":
    K = 2  # 固定下游数量为 2

    print("固定 k=2（task_1 只阻塞 2 个下游），增大 n 观察差异")
    run_test(n=100,  k=K)
    run_test(n=1000, k=K)
    run_test(n=5000, k=K)

    if TEST_DIR.exists():
        shutil.rmtree(TEST_DIR)
    print("\n====== 清理完毕 ======")
