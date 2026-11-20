# M1-2 ｜ Launch 编排：从“一个个敲命令”到“一键启动”

本工作区复用 M1-1 的 `sensor_interfaces`、`m1_ultrasonic` 和 A/B/C 三个节点，
通过 Python Launch 文件完成：

- 一键启动 A/B/C；
- 通过 `namespace` 隔离两组实例；
- 从 YAML 加载各节点参数；
- 节点 B 完成启动后再启动节点 C；
- 参数文件不存在时输出清晰错误并停止 Launch。

## 一、目录结构

```text
M1-2/
├── README.md
├── params_robot1.yaml
├── params_robot2.yaml
└── src/
    ├── sensor_interfaces/
    │   ├── msg/SensorData.msg
    │   └── srv/TriggerAlarm.srv
    └── m1_ultrasonic/
        ├── launch/
        │   └── bringup.launch.py
        ├── m1_ultrasonic/
        │   ├── node_a_sensor.py
        │   ├── node_b_filter.py
        │   ├── node_c_alarm.py
        │   └── alarm_server.py
        ├── package.xml
        └── setup.py
```

## 二、构建

```bash
cd /home/tranc/codex/codex_chat/m0-m6-practice/M1/M1-2
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
```

构建结果为：

```text
Summary: 2 packages finished
```

每个新终端都需要重新加载环境：

```bash
source /opt/ros/humble/setup.bash
source install/setup.bash
```

## 三、Launch 参数

| 参数 | 默认值 | 作用 |
| :-- | :-- | :-- |
| `namespace` | `robot1` | A/B/C 共用的命名空间 |
| `params_file` | 空字符串 | 节点参数 YAML 路径 |
| `use_sim_time` | `false` | 是否使用 ROS 仿真时间 |

固定节点名：

```text
node_a_sensor
node_b_filter
node_c_alarm
```

话题和服务均使用相对名称，因此会自动加入命名空间。

## 四、启动 robot1

终端 1：

```bash
cd /home/tranc/codex/codex_chat/m0-m6-practice/M1/M1-2
source /opt/ros/humble/setup.bash
source install/setup.bash

ros2 launch m1_ultrasonic bringup.launch.py \
  namespace:=robot1 \
  params_file:=/home/tranc/codex/codex_chat/m0-m6-practice/M1/M1-2/params_robot1.yaml
```

最终节点：

```text
/robot1/node_a_sensor
/robot1/node_b_filter
/robot1/node_c_alarm
```

话题：

```text
/robot1/sensor_data
/robot1/processed_distance
```

## 五、同时启动 robot2

终端 2 使用同一个 Launch 文件：

```bash
cd /home/tranc/codex/codex_chat/m0-m6-practice/M1/M1-2
source /opt/ros/humble/setup.bash
source install/setup.bash

ros2 launch m1_ultrasonic bringup.launch.py \
  namespace:=robot2 \
  params_file:=/home/tranc/codex/codex_chat/m0-m6-practice/M1/M1-2/params_robot2.yaml
```

两组同时运行时共有六个业务节点：

```text
/robot1/node_a_sensor
/robot1/node_b_filter
/robot1/node_c_alarm
/robot2/node_a_sensor
/robot2/node_b_filter
/robot2/node_c_alarm
```

两套话题互不干扰：

```text
/robot1/sensor_data
/robot1/processed_distance

/robot2/sensor_data
/robot2/processed_distance
```

## 六、参数差异验证

`params_robot1.yaml`：

```text
alpha = 0.3
alarm_threshold = 0.3
service_timeout = 1.0
```

`params_robot2.yaml`：

```text
alpha = 0.6
alarm_threshold = 0.5
service_timeout = 1.0
```

检查命令：

```bash
ros2 param get /robot1/node_b_filter alpha
ros2 param get /robot1/node_c_alarm alarm_threshold
ros2 param get /robot2/node_b_filter alpha
ros2 param get /robot2/node_c_alarm alarm_threshold
```

实测结果：

```text
Double value is: 0.3
Double value is: 0.3
Double value is: 0.6
Double value is: 0.5
```

YAML 使用 `/**/node_b_filter` 和 `/**/node_c_alarm`，可以匹配任意命名空间下的
对应节点。代码中的 `name=` 决定节点名，`PushRosNamespace` 决定命名空间。

## 七、启动顺序

Launch 先启动 A 和 B。`OnProcessStart(target_action=node_b)` 监听 B 的
`ProcessStarted` 事件，随后 `TimerAction(period=1.0)` 等待一秒，再启动 C。

事件触发后的 C 单独放入一个：

```python
GroupAction(
    actions=[
        PushRosNamespace(namespace),
        node_c,
    ]
)
```

这样 C 不会丢失外层命名空间。

实际启动日志：

```text
[INFO] [node_a_sensor-1]: process started
[INFO] [node_b_filter-2]: process started
[robot1.node_b_filter]: 节点 B 已启动，等待传感器数据
...约一秒后...
[INFO] [node_c_alarm-3]: process started
[robot1.node_c_alarm]: 节点 C 已启动，等待滤波距离
```

最终 C 仍然出现在：

```text
/robot1/node_c_alarm
```

没有跑到根命名空间 `/node_c_alarm`。

## 八、参数文件错误处理

在创建任何节点之前，Launch 检查：

```python
if params_file and not os.path.isfile(params_file):
    error_message = f"[ERROR] 参数文件不存在: {params_file}"
    return [
        LogInfo(msg=error_message),
        Shutdown(reason=error_message),
    ]
```

测试：

```bash
ros2 launch m1_ultrasonic bringup.launch.py \
  namespace:=robot1 \
  params_file:=/nope.yaml
```

实际输出：

```text
[INFO] [launch.user]: [ERROR] 参数文件不存在: /nope.yaml
```

Launch 随即退出：

- 不启动 A/B/C；
- 不使用代码默认参数偷偷运行；
- 不输出 Python Traceback。

## 九、use_sim_time 验证

启动时传入：

```bash
ros2 launch m1_ultrasonic bringup.launch.py \
  namespace:=simtest \
  params_file:=/home/tranc/codex/codex_chat/m0-m6-practice/M1/M1-2/params_robot1.yaml \
  use_sim_time:=true
```

检查：

```bash
ros2 param get /simtest/node_a_sensor use_sim_time
ros2 param get /simtest/node_b_filter use_sim_time
ros2 param get /simtest/node_c_alarm use_sim_time
```

实测三个节点均返回：

```text
Boolean value is: True
```

## 十、其他验证命令

查看节点：

```bash
ros2 node list
```

查看话题：

```bash
ros2 topic list
```

查看一条原始数据：

```bash
ros2 topic echo /robot1/sensor_data --once
```

查看一条滤波结果：

```bash
ros2 topic echo /robot1/processed_distance --once
```

查看话题频率：

```bash
ros2 topic hz /robot1/processed_distance
```

原始 `/sensor_data` 约为 `10 Hz`；滤波结果约为 `9.2～9.4 Hz`，因为节点 B
会丢弃 `status != 0` 的数据。

## 十一、报警服务说明

M1-2 的 Launch 主体只启动 A/B/C 三个业务节点。若需要验证正常报警，需要额外
启动与命名空间匹配的报警服务端：

```bash
ros2 run m1_ultrasonic alarm_server \
  --ros-args -r __ns:=/robot1
```

robot2 同理：

```bash
ros2 run m1_ultrasonic alarm_server \
  --ros-args -r __ns:=/robot2
```

只启动根命名空间的 `/trigger_alarm` 不会响应
`/robot1/trigger_alarm` 或 `/robot2/trigger_alarm`。

未启动服务端时，节点 C 输出：

```text
[WARN] 报警服务超时
```

这是 M1-1 已实现的正确超时行为，不是 M1-2 Launch 错误。

## 十二、实际踩坑记录

### 1. 新终端找不到 `m1_ultrasonic`

现象：

```text
Package 'm1_ultrasonic' not found
```

原因：当前终端只加载了 `/opt/ros/humble`，没有加载当前工作区的 `install/`。

解决：

```bash
source /opt/ros/humble/setup.bash
source install/setup.bash
```

### 2. Launch 返回错误类型

最初把 `generate_launch_description()` 的返回值写成了 `LaunchConfiguration`，
导致 Launch 无法规范化动作并报 `InvalidFrontendLaunchFileError`。

修复为：

```python
return LaunchDescription([...])
```

### 3. 参数文件被错误地插入自身

错误写法：

```python
parameters.insert(0, parameters)
```

这会把列表自身插入列表。正确写法：

```python
parameters.insert(0, params_file)
```

### 4. 节点 C 原来与 A/B 同时启动

初始 Launch 把 C 放入普通 `actions` 列表，三个节点几乎同时启动。

修复为：

- 使用 `RegisterEventHandler` 注册启动事件；
- 使用 `OnProcessStart` 监听 B；
- 使用 `TimerAction` 延迟一秒；
- 事件触发后给 C 重新设置命名空间。

### 5. 参数文件不存在时仍使用默认值运行

`launch_ros` 对不存在的文件只输出 Warning，随后节点仍用
`declare_parameter()` 的默认值启动。这样用户可能误以为 YAML 已加载。

修复为在创建节点前使用 `os.path.isfile()` 检查，并通过
`LogInfo + Shutdown` 提前终止。

## 十三、AI 使用声明

- Launch 文件结构、事件处理思路、参数文件校验方案和有关概念解释使用了 AI 辅助。
- 以上代码由本人手动输入、构建并运行；节点命名空间、参数差异、启动顺序、
  文件不存在和 `use_sim_time` 均通过实际命令验证。
- 本 README 的整理使用了 AI 辅助，命令和结果已按本机实际输出核对。
