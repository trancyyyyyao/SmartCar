# M0-4 ｜ 任务调度模拟器（TaskScheduler）

按依赖顺序执行一组任务，模拟随机成功/失败，支持失败重试、跳过传播、超时中断，
最后输出结构化的 `report.json`。不依赖 ROS 或 GUI，全程在终端运行。

示例配置：`tasks_demo.yaml` 与 `tasks_demo.json`（内容等价）。

## 一、环境准备

依赖只有一个第三方库：PyYAML。

```bash
cd M0/M0-4

# 创建虚拟环境（任选一种）
uv venv                     # 推荐：本机使用的是 uv
# python3 -m venv .venv     # 或者用标准库的 venv

source .venv/bin/activate

# 安装依赖（任选一种）
uv pip install -r requirements.txt
# pip install -r requirements.txt
```

> 注意：本机的系统 Python 缺少 `ensurepip`（`python3-venv` 未安装），
> 所以用 `python3 -m venv` 创建的虚拟环境里没有 pip。
> 这里改用 `uv venv` + `uv pip install`，能正确把依赖装进 `.venv`。

## 二、参数说明

| 参数 | 必填 | 默认值 | 说明 |
| :-- | :--: | :-- | :-- |
| `--config <path>` | **是** | — | 任务配置文件，支持 `.yaml` / `.yml` / `.json` |
| `--timeout <float>` | 否 | 取配置文件里的 `timeout` | 覆盖配置文件中的全局超时（秒） |
| `--report <path>` | 否 | `report.json` | 报告输出路径 |
| `--seed <int>` | 否 | 无 | 随机种子，传了就能复现同一组结果 |

查看帮助：

```bash
python3 scheduler.py --help
```

**退出码约定：**

| 退出码 | 含义 |
| :-- | :-- |
| `0` | 正常执行完成（任务可能有失败，但程序本身没出错） |
| `1` | 配置错误（文件不存在、语法错误、内容非法、依赖成环等） |
| `2` | 命令行参数错误（由 argparse 自动产生，如缺少 `--config`） |

**输出约定：**

- 任务日志和控制台摘要走 **stdout**
- 错误信息走 **stderr**
- 有终端时状态词带颜色；重定向到文件时自动降级为纯文本

## 三、运行示例

### 示例 1：最基本用法（随机结果）

```bash
python3 scheduler.py --config tasks_demo.yaml
```

不传 `--seed`，每次结果都不同。以下是一次实际运行：

```
=== 开始执行 ===
  Init             SUCCESS   (第 1 次尝试)
  Navigate         SUCCESS   (第 1 次尝试)
  DetectQR         SUCCESS   (第 1 次尝试)
  AvoidObstacle    SUCCESS   (第 1 次尝试)
  Grasp            SUCCESS   (第 1 次尝试)
  Place            SUCCESS   (第 1 次尝试)
  ReturnHome       SUCCESS   (第 1 次尝试)
报告已写入 report.json
=== 执行完毕（总耗时 11.01s，共 7 个任务）===
```

### 示例 2：固定随机种子（结果可复现）

```bash
python3 scheduler.py --config tasks_demo.yaml --seed 42
```

同一个 `--seed` 重复运行，结果完全一致，便于调试和对比。

### 示例 3：缩短超时，观察 TIMEOUT

```bash
python3 scheduler.py --config tasks_demo.yaml --timeout 5 --seed 42
```

实际输出：

```
=== 开始执行 ===
  Init             SUCCESS   (第 1 次尝试)
  Navigate         SUCCESS   (第 1 次尝试)
  DetectQR         SUCCESS   (第 1 次尝试)
  [全局]             TIMEOUT   已用时 6.51s，超过上限 5.0s
报告已写入 report.json
=== 超时中断（总耗时 6.51s）===
```

报告中未执行完的任务都会被标成 `TIMEOUT`：

```
Init           SUCCESS  attempts=1
Navigate       SUCCESS  attempts=1
DetectQR       SUCCESS  attempts=1
AvoidObstacle  TIMEOUT  attempts=0
Grasp          TIMEOUT  attempts=0
Place          TIMEOUT  attempts=0
ReturnHome     TIMEOUT  attempts=0
```

> 实际耗时 6.51s 大于上限 5s 是正常的：超时只能在一个任务 `sleep` 结束后才发现，
> 无法预知下一个任务会跑多久。

### 示例 4：观察失败重试与跳过传播

```bash
python3 scheduler.py --config tasks_demo.yaml --seed 2
```

这一组种子会触发完整的失败链路：

```
=== 开始执行 ===
  Init             SUCCESS   (第 1 次尝试)
  Navigate         FAILED    (第 1 次尝试)
  Navigate         RETRY
  Navigate         SUCCESS   (第 2 次尝试)
  DetectQR         SUCCESS   (第 1 次尝试)
  AvoidObstacle    FAILED    (第 1 次尝试)
  AvoidObstacle    RETRY
  AvoidObstacle    FAILED    (第 2 次尝试)
  AvoidObstacle    RETRY
  AvoidObstacle    FAILED    (第 3 次尝试)
  AvoidObstacle    SKIPPED   (尝试 3 次仍失败)
  Grasp            SUCCESS   (第 1 次尝试)
  Place            SKIPPED   (前置未成功：AvoidObstacle)
  ReturnHome       SKIPPED   (前置未成功：Place)
报告已写入 report.json
=== 执行完毕（总耗时 14.01s，共 7 个任务）===
```

可以看到三种典型现象：

1. `Navigate` 失败一次后**重试成功**
2. `AvoidObstacle` 连续失败 3 次，最终 `SKIPPED`
3. `Place`、`ReturnHome` 被上游连累，**一次都没执行**就直接 `SKIPPED`

## 四、report.json 结构

```json
{
  "timeout": false,
  "total_duration": 14.014,
  "tasks": [
    {
      "name": "Init",
      "status": "SUCCESS",
      "attempts": 1,
      "duration": 0.501,
      "started_at": 1792219337.404,
      "ended_at": 1792219337.905
    }
  ]
}
```

| 字段 | 类型 | 含义 |
| :-- | :-- | :-- |
| `timeout` | bool | 本次运行是否因超时被中断 |
| `total_duration` | float | 整次运行的实际耗时（秒） |
| `tasks` | array | **配置里的每一个任务**，包括被跳过和超时未执行的 |
| `tasks[].name` | str | 任务名 |
| `tasks[].status` | str | `SUCCESS` / `FAILED` / `SKIPPED` / `TIMEOUT` |
| `tasks[].attempts` | int | 实际尝试次数，0~3；被前置挡住的任务为 0 |
| `tasks[].duration` | float | 这个任务的实际耗时（秒），**含重试** |
| `tasks[].started_at` | float | 开始执行的时间戳（Unix 秒） |
| `tasks[].ended_at` | float | 结束执行的时间戳（Unix 秒） |

**关于 `duration`**：取的是 `ended_at - started_at`，所以重试过的任务会比配置里的
`duration` 大。例如 `Navigate` 配置为 2.5 秒、重试一次，报告里是 `5.005` 秒。

**关于 `FAILED`**：它只出现在控制台日志里，表示"某一次尝试失败了"。
任务最终只会是 `SUCCESS`、`SKIPPED` 或 `TIMEOUT`。

## 五、设计说明

### 1. 拓扑排序（Kahn 算法）

先建两张表：

- `indegree`：每个任务还剩几个前置没完成
- `downstream`：每个任务的下游（谁在等它）

然后把入度为 0 的任务放进队列，逐个取出；每取出一个，就把它所有下游的入度减 1，
减到 0 的下游进入队列。

**环检测**：如果处理完的任务数少于总数，说明有任务卡在环里出不来——它们的入度
永远减不到 0。此时直接报错退出，并列出具体是哪几个任务。

选择 Kahn 而不是 DFS 的原因：它天然给出"一层一层推进"的顺序，符合任务调度的直觉，
而且环检测几乎免费（数一数就知道）。

### 2. 失败与跳过的传播规则

- 单次尝试失败 → 打印 `FAILED`
- 还有剩余次数 → 打印 `RETRY`，重新执行
- 3 次都失败 → 任务最终状态 `SKIPPED`
- 执行前检查前置：**只要有一个前置不是 `SUCCESS`**，当前任务直接 `SKIPPED`，
  不进行任何尝试（`attempts = 0`）

因为拓扑排序保证"前置一定排在前面"，所以轮到某个任务时，它的前置结果一定已经
记录在 `status_by_name` 里了。

### 3. 超时的检查点

在两个位置各检查一次：

1. **任务开始前**：如果已经超时，连这个任务都不开始
2. **每次 `sleep` 结束后**：如果这个任务把总时间拖过了上限，立即中断

只检查第一个位置是不够的——那样最后一个任务可能"睡过了头"才被发现。

超时后，正在执行的任务和所有尚未执行的任务都标记为 `TIMEOUT`。

### 4. 彩色日志的降级

用 ANSI 转义码给状态词上色（SUCCESS 绿 / FAILED 红 / RETRY 黄 / SKIPPED 蓝 /
TIMEOUT 紫）。通过 `sys.stdout.isatty()` 判断：

- 输出到真实终端 → 上色
- 输出被管道或重定向 → 纯文本，不带任何转义字符

`report.json` 中**不包含任何颜色码**，它始终是合法的纯 JSON。

### 5. 随机数

用 `random.Random(seed)` 创建独立的随机源，避免影响全局随机状态。
传了 `--seed` 就可复现；不传则每次不同。

注意：随机数是**按执行顺序**依次取的，不是按配置文件里的顺序。所以同一个
种子，如果执行顺序变了，每个任务抽到的随机数也会变。

## 六、AI 使用声明

本题使用 AI 辅助完成，如实说明如下。

**由 AI 生成或大幅协助的部分：**

- 拓扑排序中"入度表 + 下游表"的建法与环检测写法
- 超时检查点的位置与 `stop_index` 的设计
- 彩色日志的 ANSI 码表、`log()` 函数与 `isatty()` 降级逻辑
- `write_report()` 的 JSON 序列化参数
- 本 README 的组织与文字

**由自己编写、AI 仅提示方向的部分：**

- `load_config` / `validate_config` 的参数校验逻辑
- `run_task` 的循环结构、状态记录与结果拼装
- `main` 的参数解析与流程串联

**是否逐行研究并验证：**

已逐行理解全部代码，并用以下场景逐一实测：

| 场景 | 结果 |
| :-- | :-- |
| 正常配置 | 7 个任务按依赖顺序执行，报告结构正确 |
| `--seed 42` | 结果可复现 |
| `--seed 2` | 出现 RETRY、SKIPPED 与跳过传播 |
| `--timeout 5` | 中途中断，剩余任务为 TIMEOUT |
| 文件不存在 / 语法错误 / 缺字段 | 可读提示 + 退出码 1 |
| 依赖不存在 / 依赖成环 / success_rate 越界 | 可读提示 + 退出码 1 |
