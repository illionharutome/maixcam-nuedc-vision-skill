# API 调参计划

第一阶段只运行 `scripts/tune_2023e_single.py` 本地分析 JSONL，计算 lock time、平均/最大/标准差误差、overshoot、jitter、saturation rate、lost count 和 FPS，并打印 `kp_x/kp_y`、`kd_x/kd_y`、deadband、command limit、smoothing alpha、path speed 的人工建议。

可选 `--deepseek` 仅在环境变量 `DEEPSEEK_API_KEY` 存在时上传聚合摘要；代码不写死或打印 key。API 不接收实时图像、不控制硬件、不自动写配置、不启用 PWM/光源/云台。任何参数应用都需要人工确认和新的安全审查。
