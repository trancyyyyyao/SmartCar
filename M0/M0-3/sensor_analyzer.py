import argparse
import csv
import math
import os
import sys



def die(message):
    """打印错误信息，并以非 0 退出码结束程序。"""
    print(message, file=sys.stderr)
    sys.exit(1)


# --- 解析命令行参数 ---
parser = argparse.ArgumentParser(description="分析传感器数据：计算均值和标准差，剔除离群值")
parser.add_argument("--input", default="sensor_data.csv", help="输入 csv 的路径（默认 sensor_data.csv）")
parser.add_argument("--output", default="cleaned_data.csv", help="输出 csv 的路径（默认 cleaned_data.csv）")
args = parser.parse_args()


data = []
times = []
cleaned = []

print("=== 传感器数据分析 ===")

# --- 读取数据 ---
if not os.path.exists(args.input):
    die(f"错误：找不到文件「{args.input}」")

reader = csv.DictReader(open(args.input, "r"))

if "time" not in reader.fieldnames or "value" not in reader.fieldnames:
    die(f"错误：csv 需要 time 和 value 两列，实际列名是 {reader.fieldnames}")

for row in reader:
    try:
        t = float(row["time"])
        v = float(row["value"])
    except ValueError:
        die(f"错误：这行数据不是数字：{row}")
    times.append(t)
    data.append(v)

if not data:
    die("错误：文件里没有任何数据行")

print("共读取 %d 条数据" % len(data))

# --- 计算平均值 ---
total = 0
for v in data:
    total += v
mean = total / len(data)

# --- 计算标准差 ---
acc = 0
for v in data:
    acc += (v - mean)*(v-mean)
std = math.sqrt(acc / len(data))

# --- 剔除离群值 ---
for t,v in zip(times,data):
    if abs(v-mean)<std*2:
        cleaned.append((t,v))

# --- 输出清洗后的数据 ---
output_path = args.output
f = open(output_path, "w")
writer = csv.writer(f)
writer.writerow(["time", "value"])
for t,v in cleaned:
    writer.writerow((t,v))

print("均值 mean = %.4f" % mean)
print("标准差 std = %.4f" % std)
print("清洗后剩余 %d 条" % len(cleaned))
print("已保存到 %s" % output_path)

