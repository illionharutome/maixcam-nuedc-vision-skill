# 导出 ONNX

- 固定输入分辨率、batch=1、类别顺序和预处理。
- 用 ONNX Runtime 对同一测试图与训练框架结果做数值/框位置对比。
- 记录模型家族（YOLOv8/YOLO11/YOLO26）和输出节点名；不要把 `.onnx` 提交 Git。

