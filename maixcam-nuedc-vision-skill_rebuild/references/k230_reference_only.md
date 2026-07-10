# K230 / CanMV historical reference only

K230/CanMV code is historical reference and must not be directly generated, copied, or migrated as MaixCAM-Pro code.

It is incompatible with MaixCAM-Pro/MaixPy v4. Do not introduce `media.sensor`, `FPIOA`, `Sensor`, `MediaManager`, K230 `pixel_to_servo`, or its binary protocols into the mainline.

The current mainline is MaixCAM-Pro + `$MV` ASCII text protocol + image-space error output. Actuator mapping belongs to the MSPM0G3507 controller layer.
