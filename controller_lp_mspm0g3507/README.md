# LP-MSPM0G3507 first-stage tracking firmware

This target is the safe development step before the final TianMengXing port. It keeps the parser, gimbal controller,
motor adapter, and DCC-100 driver board-neutral while replacing only the board SysConfig and entry point.

## Verified board mapping

The local TI `SLAU873` user guide and `MCU098A` schematic show:

- BoosterPack J1 pin 3 can route to PA9 / UART1 RX through J14.
- BoosterPack J1 pin 4 is PA8 / UART1 TX.
- UART0 PA10/PA11 remains connected to the XDS110 Application/User UART when J21/J22 select XDS.
- All logic is 3.3 V.

For the first one-way test:

```text
MaixCAM Pro A19 / UART1_TX  -> LP-MSPM0G3507 J1 pin 3 / PA9 / UART1_RX
MaixCAM Pro GND             -> LP-MSPM0G3507 GND
```

Move J14 to the position that selects PA9, not PB23. Do not connect 5 V between boards; power both boards normally
and share only ground. Optional return data uses LP J1 pin 4 / PA8 to MaixCAM A18 / UART1_RX.

## CCS project assembly

1. Create or copy an MSPM0G3507 empty DriverLib project using MSPM0 SDK 2.10 or later.
2. Replace its SysConfig file with `empty.syscfg` from this directory.
3. Use `main.c` from this directory.
4. Add these existing repository sources to the project:
   `vision_parser.c`, `gimbal_control.c`, `motor_adapter.c`, and `step_motor.c`, plus their headers, from
   `controller_tmx_mspm0/`.
5. Add this directory and `controller_tmx_mspm0/` to the compiler include paths.
6. Build once and confirm SysConfig generates `VISION_UART_*`, `DEBUG_UART_*`, and `DCC_100_PWM*` macros.

## Safe bring-up order

`lp_tracking_config.h` intentionally sets `LP_TRACKING_ENABLE_MOTORS` to `0`.

1. Keep DCC motor power off. Flash the project and open `XDS110 Class Application/User UART` at 115200 8N1.
2. Run the MaixCAM application with `/dev/ttyS1`. Moving the laser should produce lines such as
   `MV state=1 dx=-42 dy=18 conf=67` on the PC terminal.
3. Only after UART parsing is stable, set motor enable to `1`. Leave tilt disabled and test pan at 5-20 deg/s.
4. If pan moves away from the target, toggle `LP_TRACKING_INVERT_PAN` and rebuild.
5. Enable tilt only after pan direction and emergency power removal are proven. Then calibrate `INVERT_TILT`.

The initial deadband is 8 pixels, the maximum speed is 20 deg/s, and a receive timeout stops the active controller.
These conservative values are for bench integration, not final competition tuning.
