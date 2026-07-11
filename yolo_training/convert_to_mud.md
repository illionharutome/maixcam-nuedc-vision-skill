# ONNX 转 MUD

使用 Sipeed 官方 MaixCAM 模型转换流程，目标类型选择 `detector`，填写 labels、mean/scale、输入尺寸和正确输出节点。转换后先用官方最小检测脚本验证，再接入本工程。

官方流程：<https://wiki.sipeed.com/maixpy/doc/en/vision/customize_model_yolo.html>

