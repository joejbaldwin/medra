"""Bubble radius and edge width."""

from __future__ import annotations

import math

R_MIN, R_MAX = 20.0, 64.0
W_MIN, W_MAX = 1.5, 7.0


def radius(count: int, max_count: int) -> float:
    """Area proportional to count (radius to its square root), rescaled so the
    most mentioned bubble on screen is always R_MAX."""
    return round(R_MIN + (R_MAX - R_MIN) * math.sqrt(count / max_count), 1)


def edge_width(count: int) -> float:
    """Width grows with the number of sentences the pair shares."""
    return round(min(W_MAX, W_MIN + 1.1 * (count - 1)), 2)
