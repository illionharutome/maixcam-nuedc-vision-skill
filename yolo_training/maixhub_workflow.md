# 路线 A：MaixHub

1. 上传去隐私、去重复并完成标注的数据集。
2. 选择与任务匹配的检测模型和 MaixCAM Pro 平台，先用小模型验证闭环。
3. 检查验证集漏检、误检和混淆类别，不只看总 mAP。
4. 导出 MaixCAM 可用模型，放到设备 `/root/models/`，不要提交仓库。
5. 更新 `yolo_target.yaml` 的模型路径、阈值和标签，用回放集和实机分别验证。

参考：<https://maixhub.com/> 与 Sipeed MaixPy 官方视觉文档。

