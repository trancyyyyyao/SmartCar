# M0-4 ｜ 任务调度模拟器（TaskScheduler）

按依赖顺序执行一组任务，模拟随机成功/失败，支持失败重试、超时中断，
最后输出结构化报告。不依赖 ROS 或 GUI，全程在终端运行。

示例配置：`tasks_demo.yaml` 与 `tasks_demo.json`（内容等价）。

## 一、参数说明

| 参数 | 必填 | 默认值 | 说明 |
| :-- | :--: | :-- | :-- |
| `--config <path>` | 是 | — | 任务配置文件，支持 `.yaml` / `.yml` / `.json` |
| `--timeout <float>` | 否 | 取配置文件里的 `timeout` | 覆盖配置文件中的全局超时（秒） |
| `--report <path>` | 否 | `report.json` | 报告输出路径 |
| `--seed <int>` | 否 | 无 | 随机种子，用于复现同一组随机结果 |

TODO：补充 `--help` 的说明，以及退出码约定

## 二、运行示例

TODO：至少写 3 个，每个都要有命令 + 关键输出

```bash
# 示例 1：最基本用法——用默认超时和报告路径
python3 scheduler.py --config tasks_demo.yaml

# 示例 2：用固定随机种子复现结果
python3 scheduler.py --config tasks_demo.yaml --seed 42

# 示例 3：覆盖超时，缩短到 5 秒观察 TIMEOUT
python3 scheduler.py --config tasks_demo.yaml --timeout 5 --report timeout_report.json
```

TODO：把每个示例的实际输出贴上来

## 三、report.json 结构

```json
{
  "timeout": false,
  "total_duration": 11.01,
  "tasks": [
    {
      "name": "Init",
      "status": "SUCCESS",
      "attempts": 1,
      "duration": 0.5,
      "started_at": 1699999999.12,
      "ended_at": 1699999999.62
    }
  ]
}
```

`status` 取值：`SUCCESS` / `FAILED` / `SKIPPED` / `TIMEOUT`。
TODO：说明 `attempts`、`duration`、`started_at` / `ended_at` 的含义

## 四、设计说明

TODO（可选但强烈建议）：写清这几条规则你是怎么定的

- 依赖拓扑的顺序是怎么确定的
- 依赖环怎么检测
- 前置任务失败/跳过时，下游任务应该是什么状态
- 超时在哪些时间点检查
- 彩色输出在非 TTY 环境下怎么降级

## 五、AI 使用声明

> 题目要求：若使用 AI 辅助，必须如实说明哪些部分用了 AI、是否逐行研究并验证过。

- 使用 AI 的部分：
- 是否逐行研究并验证：
