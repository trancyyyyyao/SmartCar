import sys
import os
import yaml
import json
import argparse
import random
import time
from collections import deque


MAX_ATTEMPTS = 3 


# 状态 → ANSI 颜色码
COLORS = {
    "SUCCESS": "\033[32m",   # 绿
    "FAILED":  "\033[31m",   # 红
    "RETRY":   "\033[33m",   # 黄
    "SKIPPED": "\033[34m",   # 蓝
    "TIMEOUT": "\033[35m",   # 紫
}
RESET = "\033[0m"
USE_COLOR = sys.stdout.isatty()   # 只有终端才上色；重定向到文件时自动降级


def log(name, status, detail=""):
    """实时打印一条任务状态；非终端环境自动去掉颜色码。"""
    if USE_COLOR:
        状态 = f"{COLORS.get(status, '')}{status:<8}{RESET}"
    else:
        状态 = f"{status:<8}"
    print(f"  {name:16} {状态}  {detail}".rstrip())


def load_config(path):
    """读取 yaml / json 配置文件，返回配置字典。"""
    ext = os.path.splitext(path)[1].lower()

    # 检查 1：文件不存在
    if not os.path.exists(path):
        print(f"错误：找不到配置文件「{path}」", file=sys.stderr)
        sys.exit(1)

    # 格式不支持
    if ext not in (".yaml", ".yml", ".json"):
        print(f"错误：不支持的配置格式「{ext}」，请用 .yaml / .yml / .json", file=sys.stderr)
        sys.exit(1)

    # 检查 2：语法错误（yaml 和 json 抛的异常类型不一样）
    try:
        with open(path, "r", encoding="UTF-8") as f:
            if ext == ".json":
                cfg = json.load(f)
            else:
                cfg = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"错误：YAML 语法有问题 —— {e}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"错误：JSON 语法有问题 —— {e}", file=sys.stderr)
        sys.exit(1)

    return cfg


def validate_config(cfg):
    """检查配置内容是否合法；不合法就提示并退出，合法则返回任务列表。"""
    if cfg is None:
        print("错误：配置文件是空的", file=sys.stderr)
        sys.exit(1)

    if not isinstance(cfg, dict) or not cfg.get("tasks"):
        print("错误：配置文件里没有任何任务", file=sys.stderr)
        sys.exit(1)

    tasks = cfg["tasks"]

    # 先建一份「任务名 → 任务」的索引，顺便查重名
    by_name = {}
    for t in tasks:
        name = t.get("name")
        if not name:
            print("错误：有任务缺少 name 字段", file=sys.stderr)
            sys.exit(1)
        if name in by_name:
            print(f"错误：任务名重复「{name}」", file=sys.stderr)
            sys.exit(1)
        by_name[name] = t

    # 再逐个检查每个任务的字段和取值
    for t in tasks:
        name = t["name"]

        for field in ("duration", "success_rate", "dependencies"):
            if field not in t:
                print(f"错误：任务「{name}」缺少 {field} 字段", file=sys.stderr)
                sys.exit(1)

        rate = t["success_rate"]
        if not (0.0 <= rate <= 1.0):
            print(f"错误：任务「{name}」的 success_rate={rate} 越界，必须在 0~1 之间", file=sys.stderr)
            sys.exit(1)

        for dep in t["dependencies"]:
            if dep == name:
                print(f"错误：任务「{name}」不能依赖自己", file=sys.stderr)
                sys.exit(1)
            if dep not in by_name:
                print(f"错误：任务「{name}」依赖了不存在的任务「{dep}」", file=sys.stderr)
                sys.exit(1)

    return tasks

def topological_order(tasks):
    indegree={}
    downstream={}
    for t in tasks:
        indegree[t["name"]]=len(t["dependencies"])
        downstream[t["name"]] = []
    for t in tasks:
        for dep in t["dependencies"]:
            downstream[dep].append(t["name"])      
    queue = deque()
    for name, deg in indegree.items():
        if deg == 0:
            queue.append(name)
    order=[]
    while queue:
        name=queue.popleft()
        order.append(name)
        for next_name in downstream[name]:
            indegree[next_name]-=1
            if indegree[next_name]==0:
                queue.append(next_name)
    if len(order) != len(tasks):
        卡住的任务 = []
        for 名字, 度数 in indegree.items():
            if 度数 > 0:
                卡住的任务.append(名字)
        print(f"错误：任务之间存在依赖环，涉及：{'、'.join(卡住的任务)}", file=sys.stderr)
        sys.exit(1)
    return order


def run_task(tasks,order,seed=None,timeout=None):
    rng = random.Random(seed)
    by_name = {t["name"]: t for t in tasks}
    results = []
    status_by_name = {} 
    started_at = time.time()          
    timed_out = False                 
    stop_index = len(order) 
    for i,name in enumerate(order):
        if timeout is not None and time.time() - started_at > timeout:
            timed_out = True
            stop_index = i
            log("[全局]", "TIMEOUT", f"已用时 {time.time() - started_at:.2f}s，超过上限 {timeout}s")
            break
        t = by_name[name]
        blocked = []
        for d in t["dependencies"]:
            if status_by_name.get(d) != "SUCCESS":
                blocked.append(d)
        if blocked:                           
            log(name, "SKIPPED", f"(前置未成功：{'、'.join(blocked)})")
            status_by_name[name] = "SKIPPED"
            now = time.time()
            results.append({
                "name": name, "status": "SKIPPED", "attempts": 0,
                "duration": 0.0,
                "started_at": round(now, 3),
                "ended_at": round(now, 3),
            })
            continue

        # 前置检查通过，开始执行，记下开始时刻
        task_started = time.time()
        status = "SKIPPED"
        for attempts in range(1, MAX_ATTEMPTS + 1):
            time.sleep(t["duration"])

            # 睡完之后再检查一次：这个任务本身有没有超时
            if timeout is not None and time.time() - started_at > timeout:
                timed_out = True
                stop_index = i
                log("[全局]", "TIMEOUT", f"已用时 {time.time() - started_at:.2f}s，超过上限 {timeout}s")
                break

            if rng.random() < t["success_rate"]:
                status = "SUCCESS"
                log(name, "SUCCESS", f"(第 {attempts} 次尝试)")
                break
            else:
                log(name, "FAILED", f"(第 {attempts} 次尝试)")
                if attempts < MAX_ATTEMPTS:
                    log(name, "RETRY")
        if timed_out:            # ← 新增：内层因超时退出，外层也停
            break
        if status != "SUCCESS":
            log(name, "SKIPPED", f"(尝试 {MAX_ATTEMPTS} 次仍失败)")
        task_ended = time.time()
        status_by_name[name] = status
        results.append({
            "name": name, "status": status, "attempts": attempts,
            "duration": round(task_ended - task_started, 3),
            "started_at": round(task_started, 3),
            "ended_at": round(task_ended, 3),
        })
    if timed_out:
        now = time.time()
        for name in order[stop_index:]:
            results.append({
                "name": name, "status": "TIMEOUT", "attempts": 0,
                "duration": 0.0,
                "started_at": round(now, 3),
                "ended_at": round(now, 3),
            })
    total_duration = time.time() - started_at
    return results, timed_out, total_duration


def write_report(path, results, timed_out, total_duration):
    """把执行结果写成 JSON 报告。"""
    report = {
        "timeout": timed_out,
        "total_duration": round(total_duration, 3),
        "tasks": results,
    }
    with open(path, "w", encoding="UTF-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"报告已写入 {path}")




def main(argv=None):
    parser = argparse.ArgumentParser(description="按依赖顺序执行任务，模拟成功/失败，输出报告")
    parser.add_argument("--config",  required=True,           help="任务配置文件（.yaml / .yml / .json）")
    parser.add_argument("--timeout", type=float, default=None, help="覆盖配置文件中的超时（秒）")
    parser.add_argument("--report",  default="report.json",   help="报告输出路径（默认 report.json）")
    parser.add_argument("--seed",    type=int,   default=None, help="随机种子，便于复现结果")
    args = parser.parse_args(argv)

    cfg = load_config(args.config)
    tasks = validate_config(cfg)
    order = topological_order(tasks)

    # 超时：命令行 --timeout 优先，没传就用配置文件里的
    timeout = args.timeout if args.timeout is not None else cfg.get("timeout")

    print("=== 开始执行 ===")
    results, timed_out, total = run_task(tasks, order, args.seed, timeout)

    write_report(args.report, results, timed_out, total)

    if timed_out:
        print(f"=== 超时中断（总耗时 {total:.2f}s）===")
    else:
        print(f"=== 执行完毕（总耗时 {total:.2f}s，共 {len(results)} 个任务）===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
