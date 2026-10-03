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



#求平均值
def mean(target_list):
    length=len(target_list)
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
    demon=math.sqrt(dx*dy)
    r = prod / demon
    return r



#读取yaml
def load_config(path):
    with open(path) as f:
        cfg = yaml.safe_load(f)
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

    # 2. 读配置
    cfg = load_config(args.config)

    # 3. 读数据
    xs, ys = load_columns(cfg["input_csv"], cfg["columns"]["x"], cfg["columns"]["y"])

    # 4. 计算相关系数
    r = pearson_r(xs, ys)

    # 5. 打印结果
    print("n =", len(xs))
    print("mean_x =", mean(xs))
    print("mean_y =", mean(ys))
    print("r =", r)

    return 0


if __name__ == "__main__":
    sys.exit(main())
