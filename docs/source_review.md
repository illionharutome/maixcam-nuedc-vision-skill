# 来源与兼容性审查

用户已说明其提供的代码拥有学习和复用授权。本仓库仍按平台边界选择性参考：

- `https://github.com/2262727886-stack/mspm0g3507-car-kit.git`：只参考 MSPM0G3507 工程分层、状态机和主控职责；其 K230/CanMV 视觉代码、旧二进制协议和 `pixel_to_servo` 不迁入主线。
- `https://gitee.com/allphata/tripod__head/tree/master`：用户自有并授权使用的云台仓库；当前阶段只记录为后续 MSPM0 执行层参考，不接入云台，不迁入 `0x13 0x78` 旧协议。

- K230/CanMV 的 `media.sensor`、`FPIOA`、`Sensor`、`MediaManager` API 与 MaixCAM-Pro/MaixPy v4 不兼容，不迁入主代码。
- K230 方案中的 `pixel_to_servo` 把视觉与执行映射耦合，属于旧方案，不迁入主线。
- `tripod__head` 的 `0x13 0x78` 以及 car-kit 的 `0xA5 0x5A`、`FF FE` 二进制帧不作为当前协议。
- 参考 `mspm0g3507-car-kit` 时只吸收模块分层、状态机和主控职责等结构思想，不直接复制 K230 API、二进制协议或引脚配置。

当前主线只使用 MaixCAM-Pro/MaixPy v4、`$MV` ASCII 协议和图像空间误差。
