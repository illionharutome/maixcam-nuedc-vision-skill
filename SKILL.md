---
name: maixcam-nuedc-vision-skill-rebuild
description: Build, review, and safely extend MaixCAM-Pro/MaixPy v4 vision projects for Chinese electronic design contests, especially the 2025E target-center and red-dot image-error loop using the $MV ASCII protocol, PC serial analysis, STM32ZET6 debug bridging, and MSPM0G3507 controller templates. Use when working on this repository, MaixVision bring-up, visual detection, protocol parsing, or later vehicle, arm, and YOLO interface planning.
---

# MaixCAM NUEDC Vision

Keep the verified 2025E vision path working before adding future capabilities. Treat MaixCAM as a perception device: acquire images, detect targets, calculate image-space errors, draw overlays, and emit results. Never add actuator control, PWM, servo angles, chassis PID, or arm motion planning to MaixCAM code.

## Work safely

1. Read `docs/laser_safety.md` before hardware testing.
2. Use red LEDs, screen dots, printed dots, or other low-risk substitutes. Keep the 405 nm profile disabled.
3. Validate atomic apps in this order: target center, red spot, AIM error, then the 2025E replay.
4. Preserve the `$MV,AIM` field order in `comm/protocol.md`.
5. Keep STM32ZET6 as a debug bridge. Keep MSPM0G3507 as the final controller template.

## Follow the capability priorities

- Priority 1, implemented: 2025E target center, red-dot detection, image-space error, `$MV,AIM`, and PC log analysis.
- Priority 2, placeholders only: vehicle perception data, tracking, line error, distance estimates, and protocol extensions.
- Priority 3, placeholders only: YOLO datasets/training/deployment and arm object/grasp-point perception.

Do not implement Priority 2 or 3 control behavior unless the user explicitly starts a later phase. Never let placeholders alter the Priority 1 loop.

## Route work to references

- Read `comm/protocol.md` before changing serialization or C parsing.
- Read `docs/testing_checklist.md` before MaixVision or UART validation.
- Read `docs/2025E_vision_notes.md` before changing the current detector.
- Read `docs/source_review.md` and `references/k230_reference_only.md` before consulting K230/CanMV material.
- Read `docs/yolo_training_plan.md` only for later model-planning work.
- Read `docs/vision_to_vehicle_control.md` or `docs/vision_to_arm_control.md` only for those later interfaces.

## Preserve hardware ownership

- MaixCAM-Pro: vision and result output only.
- MSPM0G3507: final safety state machines, PID, limits, dead zones, search, return-to-center, and actuator execution.
- STM32ZET6: receive and inspect `$MV` data only; never become the final controller.
- PC: run `scripts/tune.py log` and `analyze`; never auto-apply configuration.

## Validate changes

Run Python tests, exercise `scripts/tune.py analyze`, compile the shared C parser tests when a host compiler is available, run the Skill validator, and verify that no K230/CanMV APIs or actuator calls entered the MaixCAM path.
