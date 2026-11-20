# M1-3 ROS 2 工作区

当前已完成投影节点包、Launch 安装结构和官方 rosbag 生成工具，尚未实现 TF、
时间同步或点云投影。

## 目录

```text
M1-3/
├── README.md
├── tools/
│   └── make_bag.py
└── src/
    └── m1_projection/
        ├── launch/
        ├── m1_projection/
        ├── resource/
        ├── package.xml
        └── setup.py
```

## 构建

```bash
cd /home/tranc/codex/codex_chat/m0-m6-practice/M1/M1-3
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
```

## 生成小规模测试数据

首次调试使用 40 帧激光数据，避免直接生成几百 MB 的 bag：

```bash
cd /home/tranc/codex/codex_chat/m0-m6-practice/M1/M1-3
source /opt/ros/humble/setup.bash

python3 tools/make_bag.py \
  --frames 40 \
  --out sample_bag \
  --extrinsics extrinsics.yaml
```

生成结果：

```text
sample_bag/
extrinsics.yaml
```

回放：

```bash
ros2 bag play sample_bag --clock
```

回放时节点必须设置：

```text
use_sim_time = true
```

## 后续实现顺序

1. 解析 `extrinsics.yaml`；
2. 发布完整静态 TF 树；
3. 使用 `ApproximateTimeSynchronizer` 同步激光和图像；
4. 完成激光点坐标转换和相机投影；
5. 按距离着色并保存至少三张投影图；
6. 扫描不同 `slop` 并记录同步效果；
7. 对比 `use_sim_time=true/false`；
8. 使用非默认外参重新生成 bag 进行最终验证。
