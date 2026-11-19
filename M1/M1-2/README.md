# M1-2 ROS 2 工作区

当前已完成工作区、M1-1 节点复用、官方提供的两份参数文件和 Launch 安装结构。
`bringup.launch.py` 尚未实现。

## 目录

```text
M1-2/
├── params_robot1.yaml
├── params_robot2.yaml
└── src/
    ├── sensor_interfaces/
    └── m1_ultrasonic/
        ├── launch/
        └── m1_ultrasonic/
```

## 构建

```bash
cd /home/tranc/codex/codex_chat/m0-m6-practice/M1/M1-2
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
```

后续将先实现支持单个命名空间的 `bringup.launch.py`，再用同一 Launch 文件
分别启动 `robot1` 和 `robot2` 两组实例。
