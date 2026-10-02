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
    r = prod / (dx*dy)
    return r




def main():
    raise NotImplementedError("TODO: 实现入口流程")


if __name__ == "__main__":
    main()
