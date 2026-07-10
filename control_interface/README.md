# Future control-data interfaces

These types reserve perception results for later vehicle and arm tasks. They contain observations, errors, confidence, and status only.

MaixCAM must not output motor PWM, chassis speed, servo angle sequences, or arm actions. MSPM0G3507 must apply timeouts, manual stop, execution enable, limits, return-to-center, and task-specific safety before any future actuator use.

The current `$MV,AIM` frame remains unchanged. `TASK` and `ARM` frames are documentation-only until separate parsers and tests are added.
