# $GM,CMD protocol

## Command (ZET6 -> C8T6)

```
$GM,CMD,PAN=-300,TILT=220,MODE=TRACK#
```

| Field | Type | Range |
|---|---|---|
| PAN | int | -1000..1000 (milli-unit) |
| TILT | int | -1000..1000 (milli-unit) |
| MODE | enum | TRACK, AIMED, HOLD, STOP |

## Response (C8T6 -> ZET6)

### ACK
```
$GM,ACK,MODE=TRACK,PAN=-300,TILT=220,STATE=TRACK#
```

### Error
```
$GM,ERR,CODE=PAN_RANGE,STATE=ERROR#
```

Error codes: OK, SHORT, FIELD_COUNT, PAN_RANGE, TILT_RANGE, MODE_INVALID, NO_TERMINATOR, PREFIX

## Safety

STOP always resets pan/tilt to zero regardless of previous state.
CAD timeout (default 2s) auto-enters STOP.
