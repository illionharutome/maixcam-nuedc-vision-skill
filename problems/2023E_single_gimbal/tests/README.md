# Tests

当前先运行 PC 仿真、Python 语法检查和 ZET6 纯 C 主机测试。连接实板时也只验证文本解析与建议命令，不接任何执行机构。

GCC 示例：

```powershell
gcc tests/test_single_mcu.c mcu_stm32zet6/protocol_2023e_single.c mcu_stm32zet6/gimbal_command.c mcu_stm32zet6/single_gimbal_tracker.c -o tests/test_single_mcu.exe
tests/test_single_mcu.exe
```
