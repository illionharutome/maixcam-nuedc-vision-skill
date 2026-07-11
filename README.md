# MaixCAM-Pro 电赛视觉 Skill

## 新项目结构说明

新增题目统一放在 `problems/<题号_用途>/`，每题隔离 MaixVision 工程、MCU、脚本、配置、日志与文档。`problems/2023E_single_gimbal/` 是当前单云台 subset 主线；其 `maixvision_project/` 可独立打开，不依赖仓库根目录或 `shared/`。

现有根目录 `apps_replay/`、`apps_atomic/`、`mcu_stm32zet6_debug/`、`scripts/`、`vision/`、`comm/` 和 `core/` 暂作为 legacy / verified baseline 保留，以避免破坏已通过的 2025E、analyze-raw 和 STM32 bridge 验证链路。`problems/2025E_target_aiming/` 当前只提供索引，后续再分阶段复制迁移。`shared/` 只记录真正通用的协议和工具思路，MaixVision 运行时不得依赖它。

本仓库重建安全、克制的 2025E 视觉最小闭环：MaixCAM-Pro 识别靶心与红点替代物，计算图像空间误差并输出 `$MV,AIM`；PC 记录分析；STM32ZET6 仅作调试桥；天猛星 MSPM0G3507 是最终主控模板。

## 硬件分工

- MaixCAM-Pro / MaixPy：采集、检测、图像空间误差、画面显示、UART 或 `print` 输出。不得控制电机、云台、机械臂、PWM、舵机角度或 PID。
- MSPM0G3507：后续负责底盘、云台、舵机、机械臂、PID、限幅、死区、搜索、回中和安全状态机。
- STM32ZET6：只接收并检查 `$MV` 数据，不是最终主控，不控制执行机构。
- PC：只运行 `scripts/tune.py log/analyze`，不自动改配置。

## 在 MaixVision 中运行

用 MaixVision 打开整个 `maixcam-nuedc-vision-skill_rebuild` 文件夹，而不是单独打开 `main.py`。完整文件夹能保留 `apps_atomic`、`vision`、`core`、`comm` 和 `config` 的相对导入与配置路径。

默认 [`main.py`](main.py) 运行普通红点/替代光点检测：

```python
from apps_atomic.app_laser_spot_detect import main
main()
```

依次切换为靶心测试和完整 AIM 测试：

```python
from apps_atomic.app_target_board_detect import main
main()
```

```python
from apps_atomic.app_aim_error_demo import main
main()
```

`2025E_target_aiming.py` 以数字开头，不能写 `from apps_replay.2025E_target_aiming ...`。使用安全入口：

```python
from apps_replay import run_2025e_target_aiming
run_2025e_target_aiming()
```

无真实激光测试顺序：靶心 → 普通红点 → AIM error demo → 2025E replay。

## 协议与 PC 日志

UART 主协议见 [`comm/protocol.md`](comm/protocol.md)。`config/uart.yaml` 默认关闭真实 UART，此时在 MaixVision 控制台 `print` 协议帧。MaixVision 无线连接可以运行程序和查看画面，但不是 PC COM 串口。

使用 USB-TTL 或可用串口记录：

```powershell
python scripts\tune.py log --port COM7 --baud 115200 --seconds 30
python scripts\tune.py analyze --file logs\serial\xxx.jsonl
python scripts\tune.py analyze
python scripts\tune.py analyze-raw --file logs\serial\manual_maixvision_raw.txt
```

`log` 需要 `pyserial`：`python -m pip install pyserial`。`analyze` 和 `analyze-raw` 不依赖串口，也不会修改配置。

没有 USB-TTL 时，在 MaixVision 无线运行 AIM demo 或 2025E replay，将控制台文本完整复制到 `logs/serial/manual_maixvision_raw.txt`，再运行 `analyze-raw`。文件可以包含普通日志、空行和报错；工具只统计能够被现有 `$MV` 解析器验证的完整 `$MV,AIM,...#` 行。

## 当前安全边界

只使用红色 LED、屏幕红点、红点图片、红色纸点或红笔点等低风险替代物。405nm profile 存在但默认禁用，真实激光、云台、舵机、小车和机械臂执行机构均不得接入。开始测试前阅读 [`docs/laser_safety.md`](docs/laser_safety.md) 和 [`docs/testing_checklist.md`](docs/testing_checklist.md)。

YOLO、小车和机械臂部分当前只是目录、数据接口和文档占位，不属于 2025E 最小闭环。
