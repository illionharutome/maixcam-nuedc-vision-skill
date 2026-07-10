# `$MV` ASCII protocol

The current mainline protocol is the `$MV` comma-separated ASCII protocol. MaixCAM-Pro, the STM32ZET6 debug bridge, the PC logger, and the MSPM0G3507 template must use the same field order.

The old `tripod__head` `0x13 0x78` binary protocol is deprecated. The K230/car-kit `0xA5 0x5A` and `FF FE` binary formats are historical references only. Do not emit or migrate them into this mainline.

## General frame

```text
$MV,MODE,OK,CLS,CX,CY,W,H,AREA,SCORE,EX,EY,FPS,STATUS#
```

Use general frames for atomic tests such as `SPOT` or `BOARD`. A `SPOT` frame is not an AIM frame.

## AIM frame

```text
$MV,AIM,OK,TARGET_CX,TARGET_CY,SPOT_CX,SPOT_CY,AIM_EX,AIM_EY,SCORE,FPS,STATUS#
```

Example:

```text
$MV,AIM,1,160,120,148,132,-12,12,0.91,25.6,AIMING#
```

Rules:

- Encode `OK` as exactly `0` or `1`.
- Encode coordinates and errors as decimal integers.
- Encode `SCORE` and `FPS` as decimal floating-point values.
- Put `STATUS` immediately before `#`.
- Do not use JSON on the serial wire.
- Do not reorder AIM fields.
- Add future `TASK` or `ARM` modes as new frames; never break AIM.

Reserved documentation-only shapes, not implemented by the current parser:

```text
$MV,TASK,OK,TASK_MODE,CLS,CX,CY,EX,EY,ANGLE,DIST,SCORE,FPS,STATUS#
$MV,ARM,OK,CLS,CX,CY,W,H,ANGLE,GRASP_X,GRASP_Y,GRASP_ANGLE,SCORE,FPS,STATUS#
```
