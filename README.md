# MaixCAM Pro + 天猛星 MSPM0G3507 电赛视觉工程

本仓库提供可复用的视觉模块、UART 协议、MSPM0G3507 主控适配、DCC-100 双路云台驱动迁移、结构化回放调参、DeepSeek 候选参数和 YOLO/MaixHub 训练部署流程。目标是比赛现场稳定、可回滚、能快速换题，而不是单个 Demo。

## 硬件分工

| 设备 | 责任 |
|---|---|
| MaixCAM Pro | 摄像、传统视觉/YOLO、统一结果、UART 发送、MaixVision 画面 |
| 立创·天猛星 MSPM0G3507 | 串口解析、死区/方向/速度、丢帧保护、主状态机 |
| DCC-100 | 两路步进电机功率驱动和云台执行 |
| DeepSeek API | 离线读取结构化日志，建议候选 YAML 参数 |
| GitHub | 每阶段备份、比较和回滚 |

主控不是 STM32。生产代码禁止使用 STM32 HAL/CubeMX；`tripod__head-master` 只提供控制思路。

## MaixCAM Pro 视觉模块

所有模块继承 `VisionModule`，输出同一个 `VisionResult`：`ok/mode/target/center/dx/dy/confidence/distance/status/extra`。激光、色块、线、圆和边框优先传统视觉；复杂类别、数字或符号才用 YOLO。参数全部放 `maixcam_app/configs/*.yaml`（仓库默认文件采用无依赖的 JSON 语法，仍是合法 YAML 1.2）。

`laser_spot` 支持 LAB、HSV、亮度、ROI、面积、圆度、上一帧距离约束、丢帧保持和 debug overlay。紫光打墙偏蓝/偏白/过曝时先调整 `purple_to_blue_wall.yaml`，不要硬改代码。

## 天猛星与 DCC-100

链路严格保持：

```text
MaixCAM -> uart_protocol.py -> vision_parser.c -> VisionCommand_t
        -> gimbal_control.c -> motor_adapter.c -> step_motor.c -> DCC-100
```

`step_motor.c/.h` 从提供的 08 双路 MSPM0 工程迁移，补上源文件已有但头文件漏掉的 `step_motor_stop()` 声明。两路引脚、定时器、0.05625°/脉冲和风险见 `controller_tmx_mspm0/dcc_reference_notes.md`。

DCC-100 v3 动力供电 11–26V，逻辑为 3.3V/0V；必须共地。未确认电机轴、方向、微步、限流、零位和软限位前，不得带负载闭环高速运行。

## UART 协议

115200 8N1、3.3V TTL、TX/RX 交叉、共地：

```text
$MV,AIM,1,160,120,148,132,-12,12,91,256,AIMING#
```

格式与范围见 `controller_tmx_mspm0/protocol.md`。MaixCAM UART0 会输出启动日志且 TX 参与启动检测，优先评估 UART1；解析器会用 `$MV`/`#` 自动重同步。

## 现场命令

```bash
python maixcam_app/main.py --module laser_spot --config maixcam_app/configs/purple_to_blue_wall.yaml --uart /dev/ttyS0 --debug
python maixcam_app/tools/collect_dataset.py --module laser_spot --session purple_wall_001
python maixcam_app/tools/replay_test.py --config maixcam_app/configs/purple_to_blue_wall.yaml --samples logs/tuning/session_xxx/samples
python maixcam_app/tools/tune_with_deepseek.py --session logs/tuning/session_xxx
```

MaixVision 只用于人眼看画面和 overlay。正式比赛模式不逐帧写盘；只有显式采样模式才生成 `logs/tuning/session_xxx`。

## DeepSeek 调参闭环

1. 采样得到 `frames.jsonl`、`metrics.json`、`current_config.yaml`、`failure_cases.json` 和代表图。
2. 从环境变量读取 `DEEPSEEK_API_KEY`、`DEEPSEEK_MODEL`；API 强制返回 JSON。
3. 候选写到 `configs/candidates/`，必须由 `replay_test.py` 评分。
4. 只有严格高于当前分数且样本非空的候选才复制到 `configs/best/current_best.yaml`。

评分：`3*detect_rate - 2*false_positive_rate - .02*center_error - .02*jitter + .03*fps - .1*lost_frames`。

## YOLO / MaixHub

- 路线 A：MaixHub 快速训练并导出设备模型。
- 路线 B：离线训练 YOLO，验证 ONNX，按 Sipeed 官方流程转换 MUD。

设备适配器支持 MaixPy `YOLOv8/YOLO11/YOLO26`，默认 YOLO11。模型和原始数据不提交 Git。详见 `yolo_training/`。

## Git 备份规则

每个相干阶段都 commit；配置远程后每次 commit 都 push。禁止提交 `.env`、API key、日志、原始数据集、视频、压缩包和模型权重。使用 `scripts/git_checkpoint.ps1` 或 `.sh` 创建检查点，最后运行健康检查。

## 常见故障

- 看不到目标：检查镜头盖/焦距、曝光、ROI、阈值 mask、目标像素面积。
- 目标抖动：收紧 ROI/上一帧约束，调面积圆度，增大死区，降低曝光增益。
- 云台反向：只改 `invert_pan/invert_tilt`，不要在解析器临时改符号。
- 电机鸣叫/堵转：立即停止，检查电源、共地、限流、细分、速度与机械负载。
- 串口乱码：检查 115200 8N1、共地和 TX/RX；排除 UART0 启动日志。
- YOLO 无框：检查 MUD 家族、标签、输出节点、MaixPy 版本和阈值。

完整上场顺序见 `docs/field_workflow.md`，主控接入见 `controller_tmx_mspm0/integration_notes.md`。

