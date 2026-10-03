"""M0-2 入口脚本（占位，待实现）。

建议把它拆成几个职责单一的单元，每个都能单独调用、单独测试：

    load_config(path)                     -> dict
    load_columns(csv_path, col_x, col_y)  -> (xs, ys)
    pearson_r(xs, ys)                     -> float
    main(argv)                            -> int   # 解析参数、串联流程、处理异常

验收要求：
- 支持 `python3 corr_tool.py --config config.yaml`
- 正常结果打印到 stdout，且包含一行 `r = <数值>`
- 异常情况打印可读错误信息并以非 0 退出码结束，不把 Traceback 抛给用户
- input_csv 的相对路径，在「以当前目录调用」和「在别处调用」两种方式下都能跑通
"""


import math
import yaml
import csv
import argparse
import sys
import os



#求平均值
def mean(target_list):
    length=len(target_list)
    if length == 0:
        raise ValueError("没有读到任何数据，无法计算平均值")
    sum_list=0
    for i in range(length):
        sum_list+=target_list[i]
    return sum_list/length



#计算皮尔逊相关系数
def pearson_r(xs,ys): 
    length=len(xs)
    mean_x=mean(xs)  
    mean_y=mean(ys)
    dx = 0.0
    dy = 0.0
    prod = 0.0
    for i in range(length):
        a = xs[i] - mean_x
        b = ys[i] - mean_y
        dx = dx + a * a
        dy = dy + b * b
        prod = prod + a * b
    if dx * dy == 0:
        raise ValueError("某一列的数值完全一样（方差为 0），相关系数没有定义")
    demon=math.sqrt(dx*dy)
    r = prod / demon
    return r



#读取yaml
def load_config(path):
    with open(path) as f:
        cfg = yaml.safe_load(f)
    if cfg is None:
        raise ValueError(f"配置文件是空的：{path}")
    return cfg


#获取指定列的数据
def load_columns(csv_path,col_x,col_y):
    xs = []
    ys = []
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            xs.append(float(row[col_x]))
            ys.append(float(row[col_y]))
    return xs,ys



def main(argv=None):
    """程序入口：解析命令行参数，串联整个流程。"""

    # 1. 解析命令行参数
    parser = argparse.ArgumentParser(description="计算 csv 中两列数据的皮尔逊相关系数")
    parser.add_argument("--config", required=True, help="yaml 配置文件的路径")
    args = parser.parse_args(argv)

    # 2. 读配置 → 读数据 → 计算，整条链路包在 try 里统一处理错误
    try:
        cfg = load_config(args.config)

        # input_csv 若写的是相对路径，以「配置文件所在目录」为基准来解析，
        # 这样无论在哪个目录下运行这个程序，都能正确定位到数据文件。
        # （若 input_csv 本身是绝对路径，os.path.join 会直接采用它，不受影响）
        config_dir = os.path.dirname(os.path.abspath(args.config))
        csv_path = os.path.join(config_dir, cfg["input_csv"])

        xs, ys = load_columns(csv_path, cfg["columns"]["x"], cfg["columns"]["y"])
        r = pearson_r(xs, ys)
    except FileNotFoundError as e:
        print(f"错误：找不到文件「{e.filename}」，请检查路径是否正确", file=sys.stderr)
        return 1
    except KeyError as e:
        print(f"错误：缺少必要的字段或列名 {e}", file=sys.stderr)
        return 1
    except (ValueError, yaml.YAMLError) as e:
        print(f"错误：{e}", file=sys.stderr)
        return 1

    # 3. 打印结果
    print("n =", len(xs))
    print("mean_x =", mean(xs))
    print("mean_y =", mean(ys))
    print("r =", r)

    return 0


if __name__ == "__main__":
    sys.exit(main())
