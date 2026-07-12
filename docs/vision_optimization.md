# MaixCAM 视觉模块优化作业单

本阶段冻结 UART、MSPM0G3507、DCC-100 和云台控制，只比较视觉结果。每个模块使用独立数据集和独立基线，禁止用同一批图片既调参又做最终验收。

## 1. 固定相机条件

记录分辨率、镜头焦距、曝光、增益、白平衡、安装高度和俯角。同一轮参数对比期间不得改变这些条件。颜色任务优先手动曝光和白平衡；如果必须自动曝光，要把不同稳定状态作为不同场景采集。

## 2. 在 MaixCAM 采集

每个命令创建一个新 session，已有目录不会被覆盖：

```bash
python maixcam_app/tools/collect_dataset.py \
  --module laser_spot \
  --config maixcam_app/configs/purple_to_blue_wall.yaml \
  --session laser_indoor_1000mm_present_01 \
  --scene indoor_white_wall \
  --lighting bright \
  --distance-mm 1000 \
  --expected present \
  --exposure-us 1000 \
  --sample-every 15 \
  --max-frames 1500
```

为同一场景单独采集无目标和干扰光负样本。建议激光模块首轮至少包括：

| 场景 | 正样本 | 负样本 |
|---|---:|---:|
| 室内白墙正常光 | 80 | 40 |
| 室内暗光 | 50 | 30 |
| 强光/侧光 | 50 | 40 |
| 近、中、远距离 | 每档 40 | 每档 20 |
| 反光、白点、蓝色干扰 | 30 | 80 |

采集阶段的 `detect_rate_unlabeled` 只是旧参数的观察值，不能作为准确率。

## 3. 在电脑标注真值

将整个 session 复制到电脑，运行：

```bash
python maixcam_app/tools/annotate_samples.py --session logs/tuning/laser_indoor_1000mm_present_01
```

- 鼠标点击目标中心，再按 Enter/空格标记有目标。
- 按 `N` 标记无目标，`B` 返回，`S` 跳过，`Q` 保存退出。
- 工具每标一张都原子写入 `samples/ground_truth.json`，中断后可继续。

不要根据当前算法的框来标中心；只根据原图人工判断。

## 4. 检查数据集

```bash
python maixcam_app/tools/dataset_report.py --samples logs/tuning/session_xxx/samples
```

只有全部图片已标注、坐标合法、同时包含正负样本时，`ready_for_scoring` 才为 `true`。回放工具默认拒绝不完整数据集。

## 5. 建立基线

```bash
python maixcam_app/tools/replay_test.py \
  --module laser_spot \
  --config maixcam_app/configs/purple_to_blue_wall.yaml \
  --samples logs/tuning/session_xxx/samples \
  --output logs/tuning/session_xxx/baseline_metrics.json
```

重点查看总指标和 `by_scene`：检出率、误报率、平均/P95 中心误差、残差抖动、丢帧、处理耗时。`host_processing_fps` 只用于诊断，默认不进入评分；只有取得同一配置的 MaixCAM 实测值后，才用 `--scoring-fps 45` 一类参数把它计入公式。不要用电脑瞬时 FPS 选择阈值。

## 6. 小范围网格搜索

先只搜索面积、圆度和跟踪约束，再搜索颜色阈值，避免组合爆炸：

```bash
python maixcam_app/tools/parameter_sweep.py \
  --base maixcam_app/configs/purple_to_blue_wall.yaml \
  --grid maixcam_app/configs/laser_spot_sweep.example.json \
  --samples logs/tuning/session_xxx/samples \
  --module laser_spot \
  --repeat 3 \
  --output logs/tuning/session_xxx/sweep_results.json \
  --save-best
```

候选只写入 `configs/candidates/`，不得直接覆盖当前最佳配置。先检查最差场景和失败文件，再决定是否提升。

## 7. 独立验收与实机复测

用没有参与调参的 session 对候选回放。通过后在 MaixCAM 上连续运行至少 10 分钟，记录处理耗时 P95、温度、内存、画面延迟和失败案例。只有独立验收和实机稳定性都更好时，才更新 `configs/best/current_best.yaml`。

## 模块顺序

1. `laser_spot`
2. `color_blob`
3. `line_track`
4. `rectangle_detect` / `circle_detect`
5. `qr_apriltag`
6. `yolo_detect`（仅复杂类别、数字或符号；届时再启动模型训练）
