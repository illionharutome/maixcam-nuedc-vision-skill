"""Small geometry helpers shared by target solvers."""
import math


def pixel_angle(offset_px: float, focal_length_px: float) -> float:
    return math.degrees(math.atan2(offset_px, focal_length_px))


def pinhole_distance(real_size_mm: float, focal_length_px: float, observed_size_px: float) -> float:
    if observed_size_px <= 0:
        return 0.0
    return real_size_mm * focal_length_px / observed_size_px

