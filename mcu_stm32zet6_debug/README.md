# STM32ZET6 debug bridge

This directory is an early visual-tuning and UART-validation bridge only. Feed received MaixCAM bytes into the shared parser and inspect the latest `Aim_Result` in a debugger.

Do not add PID, motor, servo, laser, arm, or final-controller behavior here. MSPM0G3507 remains the final controller platform.
