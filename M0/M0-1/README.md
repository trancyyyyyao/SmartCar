# M0-1 ｜ 从零搭建开发环境

本文记录本机的开发环境搭建过程、遇到的问题与解决办法，以及最终的环境版本。

## 一、环境清单

| 组件 | 版本 / 方式 | 备注 |
| :-- | :-- | :-- |
| 操作系统 | Ubuntu 22.04.5 LTS | 双系统安装 |
| 内核 | 6.8.0-138-generic | |
| 桌面环境 | GNOME | |
| ROS2 | Humble | `/opt/ros/humble` |
| Python | 3.10.12 | 系统自带 |
| GCC | 11.4.0 | 随系统 / ROS2 依赖安装 |
| Git | 2.34.1 | |
| uv | 0.12.19 | Python 虚拟环境管理 |
| VS Code | 1.138.0 | |
| GitHub | 已有账号 | 新建仓库用于存放考核代码 |

## 二、安装过程

### 1. Ubuntu 双系统

参考 B 站 UP 主 **机器人工匠阿杰** 的视频系列完成双系统安装。

安装过程中遇到的问题基本都能在这套视频里找到对应的处理方式，包括：
分区规划、启动盘制作、BIOS 设置、GRUB 引导等。

### 2. ROS2 Humble

参考 **鱼香 ROS 机器人** 的教程与视频完成安装。

安装过程中遇到的问题（环境源配置、依赖缺失、密钥导入等）在视频里都能找到
对应的解决步骤。

验证方式：

```bash
ls /opt/ros
# humble
```

### 3. uv（Python 虚拟环境）

在 **uv 官网** 找到安装教程，按官网步骤安装。

过程中遇到不懂的地方借助豆包（AI 助手）确认，最终安装成功：

```bash
uv --version
# uv 0.12.19 (x86_64-unknown-linux-gnu)
```

后续所有 Python 项目的虚拟环境都用 uv 管理：

```bash
cd <项目目录>
uv venv                     # 创建 .venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

### 4. C/C++ 与 VS Code

- GCC 随系统与 ROS2 的依赖一起装好，`gcc --version` 为 11.4.0
- VS Code 由 Codex 协助自动安装完成，版本 1.138.0

### 5. Git 与 GitHub

本机已装好 Git（2.34.1）。GitHub 账号是之前就有的，本次新建了一个仓库
`m0-m6-practice` 用于存放考核代码，并按「模块 / 题目」两级组织目录：

```
m0-m6-practice/
├── README.md
├── .gitignore
├── M0/
│   ├── M0-1/
│   ├── M0-2/
│   ├── M0-3/
│   └── M0-4/
└── ...
```

为后续 `git push` 生成了 Personal Access Token（GitHub 已不支持账号密码推送）。

## 三、本机踩坑实录

以下都是本机实际遇到并解决的问题，按"现象 → 原因 → 解决"整理。

### 坑 1：`apt-get update` 报权限不足

**现象：**

```
E: 无法打开锁文件 /var/lib/apt/lists/lock - open (13: 权限不够)
```

**原因：** `apt` 需要写系统目录，必须以管理员身份运行。

**解决：** 加 `sudo`。

```bash
sudo apt-get update
```

### 坑 2：apt 软件源解析不了域名

**现象：**

```
错误: http://ftp.sjtu.edu.cn/ubuntu ... 暂时不能解析域名"ftp.sjtu.edu.cn"
E: 有几个软件包无法下载
```

**原因：** 配置的镜像站（上海交大源）临时不可用，网络不稳定。`apt-get update`
看起来成功，其实大部分用的是本地缓存的索引（显示"命中"），真正下载 deb 包时才暴露问题。

**尝试：** 按提示加 `--fix-missing`，但它只能"跳过下载失败的包"，当所有包都下载
失败时等于什么都没装上，治标不治本。

**解决：**

- 换用可用的镜像源后重试
- 或者绕开 apt，见坑 3

### 坑 3：`python3 -m venv` 创建的环境里没有 pip

**现象：**

```bash
python3 -m venv .venv
ls .venv/bin/
# activate  python  python3  python3.10     ← 没有 pip

.venv/bin/python3 -m pip --version
# No module named pip
```

**原因：** Ubuntu 上 `python3 -m venv` 依赖 `python3-venv` 包提供的 `ensurepip`
模块，才能往新环境里装 pip。本机没有装这个包，所以 venv 创建到"装 pip"这一步
就中断了，留下一个只有解释器、没有 pip 的"空壳"环境。

**解决：** 改用 uv 创建虚拟环境——uv 自带安装包的能力，不依赖 `ensurepip`。

```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

### 坑 4：`pip install` 把包装到了用户目录，venv 里看不到

**现象：**

```
Defaulting to user installation because normal site-packages is not writeable
...
Successfully installed PyYAML-6.0.3
```

看似装成功了，但：

```bash
.venv/bin/python3 -c "import yaml"
# ModuleNotFoundError: No module named 'yaml'
```

**原因：** 当时 shell 里激活的是一个已经被删除的旧虚拟环境，PATH 指向了不存在的
目录，`pip` 于是退回到系统 / 用户级安装，包装进了 `~/.local/lib/python3.10/site-packages`。
而 venv 默认不会搜索用户目录，所以看不到它。

**解决：** 用 uv 明确指定目标解释器：

```bash
uv pip install -r requirements.txt --python .venv/bin/python3
```

验证：

```bash
.venv/bin/python3 -c "import yaml; print(yaml.__version__, yaml.__file__)"
# 6.0.3  .../M0-4/.venv/lib/python3.10/site-packages/yaml/__init__.py
```

### 坑 5：如何确认装进的是虚拟环境而不是系统

**方法：** 看包的实际路径。

```bash
.venv/bin/python3 -c "import sys, yaml; print(sys.executable); print(yaml.__file__)"
```

- 路径里包含 `.venv/` → 装在虚拟环境里 ✓
- 路径是 `/usr/lib/python3/dist-packages/...` → 装到系统了 ✗

## 四、与题目要求的对应关系

| 题目要求 | 状态 |
| :-- | :-- |
| Ubuntu 22.04 | ✅ 22.04.5 LTS 双系统 |
| ROS2 Humble | ✅ `/opt/ros/humble` |
| Python 虚拟环境（uv 或 conda） | ✅ uv 0.12.19 |
| C / C++ | ✅ GCC 11.4.0 |
| VS Code | ✅ 1.138.0 |
| Git | ✅ 2.34.1 |
| 写 README（含踩坑实录） | ✅ 本文 |
| 创建 Git 仓库（本地 + 云端），按模块与题目划分 | ✅ `m0-m6-practice` |
| 远程登录（开发板 / 远程电脑） | ⏸ 暂缓，需要时再补 |

## 五、未完成项

**远程登录**暂时没有做。计划等后续模块真的需要连开发板或远程机器时，再补这一部分，
届时会把操作步骤和遇到的问题补充到本文档。

## 六、AI 使用声明

- 使用了 AI 的部分：VS Code 的安装过程由 Codex 协助完成；
  uv 安装过程中不清楚的地方借助豆包确认；本文档的整理借助 AI。
- 是否逐行研究并验证：Ubuntu、ROS2、uv 的安装过程均按教程自行操作并验证；
  文中所有版本号与路径均由本机命令实际查询得到。
