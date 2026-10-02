# M0-2 ｜ 首个代码工具

把考核提供的「祖传脚本」重构为可测试、可交付的命令行工具。

原始脚本见 [`legacy/legacy_corr.py`](legacy/legacy_corr.py)。

## 如何运行

```bash
# 建议在虚拟环境里操作
pip install -r requirements.txt

python3 corr_tool.py --config config.yaml
```

> 入口脚本名可自定；改了之后记得同步更新本节和根目录的说明。

## 输入文件格式

### 配置文件（yaml）

| 字段 | 类型 | 说明 |
| :-- | :-- | :-- |
| `input_csv` | str | 数据文件路径。TODO：写明相对路径以什么为基准 |
| `columns.x` | str | 参与计算的第一列列名 |
| `columns.y` | str | 参与计算的第二列列名 |
| `task.verbose` | bool | TODO：是否打印中间量 |

### 数据文件（csv）

- 必须有表头
- 至少包含 `columns.x` 与 `columns.y` 指定的两列
- 两列取值必须能转成浮点数
- TODO：补充编码要求、空值/非法值的处理约定

## 输出结果的含义

结果打印到 stdout，其中必须包含一行 `r = <数值>`。

| 输出 | 含义 |
| :-- | :-- |
| `n` | 参与计算的有效样本数 |
| `mean_x` / `mean_y` | 两列的算术平均值 |
| `r` | 皮尔逊相关系数，取值范围 -1 ~ 1 |

TODO：补充 r 的解读方式（正负号、绝对值大小各自意味着什么），
以及异常情况下的表现（可读错误信息 + 非 0 退出码，不抛 Traceback）。

## AI 使用声明

> 题目要求：若使用 AI 辅助，必须如实说明哪些部分用了 AI、是否逐行研究并验证过。

- 使用 AI 的部分：
- 是否逐行研究并验证：
