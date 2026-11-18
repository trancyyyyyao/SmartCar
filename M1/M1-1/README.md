# M1-1 ROS 2 工作区

当前只完成了工作区、包结构和接口定义，尚未实现 A/B/C 三个业务的节点逻辑。

## 目录

```text
M1-1/
└── src/
    ├── sensor_interfaces/   # 自定义消息与服务
    └── m1_ultrasonic/       # 后续实现三个业务节点
```

## 构建

```bash
cd /home/tranc/codex/codex_chat/m0-m6-practice/M1/M1-1
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
```

## 第一步检查

```bash
ros2 interface show sensor_interfaces/msg/SensorData
ros2 interface show sensor_interfaces/srv/TriggerAlarm
```

接口字段和顺序必须与官方 M1-1 题面完全一致。
