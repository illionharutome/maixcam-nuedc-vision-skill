"""Print simulated AIM packets and their expected dry-run interpretation."""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from comm.uart_packet import parse_mv_packet


CASES = (
    ("sample", "$MV,AIM,1,160,120,148,132,-12,12,0.91,25.6,AIMING#",
     "pan should respond negative; tilt should respond positive"),
    ("spot_left", "$MV,AIM,1,160,120,120,120,-40,0,0.91,25.6,AIMING#",
     "pan should respond to negative x error"),
    ("spot_right", "$MV,AIM,1,160,120,190,120,30,0,0.91,25.6,AIMING#",
     "pan should respond to positive x error"),
    ("no_spot", "$MV,AIM,0,160,120,0,0,0,0,0.00,25.6,NO_SPOT#",
     "tracking must be invalid and both commands must be zero"),
    ("aimed", "$MV,AIM,1,160,120,162,119,2,-1,0.95,25.6,AIMED#",
     "state should be locked/stable and both commands should be near zero"),
    ("lost", "$MV,AIM,1,160,120,0,0,0,0,0.00,25.6,LOST#",
     "tracking must be invalid and both commands must be zero"),
    ("error", "$MV,AIM,1,160,120,0,0,0,0,0.00,25.6,ERROR#",
     "tracking must be invalid and both commands must be zero"),
)


def main():
    print("PC-only explanation; this script does not replace the C tests.")
    for name, packet, expected in CASES:
        result = parse_mv_packet(packet)
        print("\ncase: %s" % name)
        print("packet: %s" % packet)
        print("parsed: ok=%d ex=%d ey=%d status=%s" % (
            1 if result.ok else 0,
            result.aim_error_x,
            result.aim_error_y,
            result.status,
        ))
        print("expected: %s" % expected)


if __name__ == "__main__":
    main()
