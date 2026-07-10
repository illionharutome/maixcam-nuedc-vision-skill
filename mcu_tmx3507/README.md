# MSPM0G3507 final-controller template

MSPM0G3507 owns later execution safety, PID, limits, dead zones, search, return-to-center, chassis, gimbal, servo, and arm decisions. The current template only converts validated image-space AIM errors into bounded abstract suggestion values.

No UART/PWM/GPIO pins are fixed here and no actuator is connected. Integrate board drivers only after visual and serial validation and a separate safety review.
