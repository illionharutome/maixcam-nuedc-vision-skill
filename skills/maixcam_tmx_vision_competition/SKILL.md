---
name: maixcam-tmx-vision-competition
description: Build, migrate, tune, test, or troubleshoot electronic-design-competition vision systems that use MaixCAM Pro for vision, TianMengXing MSPM0G3507 for control, and DCC-100 dual stepper hardware. Use for MaixPy classical vision or YOLO modules, UART VisionResult integration, MSPM0 DriverLib adapters, MaixVision field debugging, structured replay logs, DeepSeek-assisted threshold tuning, MaixHub training, and competition-day recovery workflows.
---

# MaixCAM TMX Vision Competition

## Enforce the architecture

- Assign vision to MaixCAM Pro, control to TianMengXing MSPM0G3507, and actuation to DCC-100.
- Treat MSPM0G3507 as the only production controller. Do not introduce STM32 HAL, CubeMX, `HAL_UART`, or an `stm32_bridge` production path.
- Keep the chain `VisionModule -> VisionResult -> uart_protocol.py -> vision_parser.c -> VisionCommand_t -> gimbal_control.c -> motor_adapter.c -> step_motor.c`.
- Keep GPIO and Timer operations inside the migrated `step_motor.c`. Keep parsing free of motor control and UART ISRs free of control policy.

## Develop vision modules

1. Reuse an existing module before adding one.
2. Make the simplest stable method run before optimizing accuracy.
3. Prefer traditional vision for laser spots, color blobs, lines, rectangles, and circles. Use YOLO for complex classes, digits, or symbols.
4. Put every tunable parameter in a YAML file. Emit only the shared `VisionResult` mapping from every module.
5. Generate every outbound string through `maixcam_app/comm/uart_protocol.py`.
6. Use YOLO for coarse localization and traditional vision inside its ROI when precise center coordinates matter.

## Migrate and control DCC-100

- Read `controller_tmx_mspm0/dcc_reference_notes.md` before changing motor code.
- Prefer the supplied 08 dual-axis MSPM0 project, then project 15 for speed/angle semantics, then project 14 for pulse basics. Use `tripod__head-master` only for high-level ideas.
- Preserve `step_motor_init`, `step_motor_dir_set`, `step_motor_start`, `step_motor_stop`, `step_set_speed`, and `step_motor_set_angle`.
- Confirm axis mapping, direction, 1/32 microstep mode, soft limits, and zero position without load before closed-loop operation.
- Stop both axes on low confidence, sustained loss, invalid frames, or receive timeout.

## Tune safely

- Follow `docs/vision_optimization.md` for capture, point annotation, dataset validation, scene-stratified replay, and bounded parameter sweeps.
- Use MaixVision only for human observation and overlays. Do not treat its GUI as API input.
- Collect explicit sampling sessions under `logs/tuning/`; never write every frame during competition mode.
- Refuse formal scoring when any sample is unlabeled or when the set lacks positive or negative cases. Treat host replay FPS as diagnostic; use only an explicit MaixCAM-measured FPS in the score.
- Let DeepSeek read only `frames.jsonl`, `metrics.json`, `current_config.yaml`, and `failure_cases.json`.
- Read `DEEPSEEK_API_KEY` and `DEEPSEEK_MODEL` only from environment variables. Require strict JSON candidate output.
- Save candidates under `configs/candidates/`, replay them, compute the repository score, and promote only a strictly higher score to `configs/best/current_best.yaml`.

## Operate at the field

1. Photograph wiring and tag the last known-good commit.
2. Verify camera focus/exposure and MaixVision overlay without motors.
3. Verify the exact `$MV,...#` frame, 115200 8N1, crossed TX/RX, 3.3V logic, and common ground.
4. Point-test each DCC axis at low speed without load; confirm inversion and limits.
5. Run open-loop vision, then closed-loop at conservative speed.
6. Change one YAML variable group at a time, replay, commit, and keep a rollback point.
7. Prefer a stable reduced feature set over an unverified architectural rewrite.

## Diagnose common failures

- No target: inspect exposure, ROI, threshold mask, minimum area, lens focus, and target pixel size.
- Jitter: narrow ROI, raise area/circularity filters, lower gain, increase deadband, or extend tracker constraints.
- Wrong direction: change `invert_pan`/`invert_tilt`; do not swap parser signs opportunistically.
- Motor stalls/noise: stop immediately; verify 11–26V DCC power, common ground, current setting, microstep mode, speed ramp, and mechanical load.
- UART garbage: verify 115200 8N1 and ground; avoid UART0 boot logs or rely on `$MV` resynchronization.
- YOLO mismatch: verify MUD family, labels, output nodes, preprocessing, and MaixPy minimum version.

## Preserve the repository

- Commit every coherent change. Push every commit when a remote is configured; otherwise record the reason in `docs/git_remote_todo.md`.
- Never commit `.env`, API keys, logs, raw datasets, videos, archives, ONNX/MUD/PT weights, or personal data.
- Run `python scripts/repo_health_check.py` and relevant replay/C tests before handoff.
