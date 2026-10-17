import sys
import os
import yaml
import json
import argparse
from collections import deque

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
    # 阶段 1 先只打印出来，确认读进来的东西是对的
    print("配置校验通过")
    print("  全局 timeout:", cfg.get("timeout"))
    print("  任务数量:", len(tasks))
    print("  执行顺序:")                       # ← 换掉原来打印全部任务的那段
    for name in order:
        print(f"    {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
