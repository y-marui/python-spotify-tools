"""Camelot Wheel key parsing and harmonic-mixing sort order.

The Camelot Wheel maps every musical key to a number (1-12) and a mode
letter (A = minor, B = major) arranged so that harmonically compatible
keys sit next to each other. Sorting a playlist by Camelot position from
a chosen starting track keeps adjacent tracks in compatible keys.
"""

from dataclasses import dataclass
from typing import Literal

Direction = Literal["cw", "ccw"]


@dataclass(frozen=True)
class CamelotKey:
    number: int
    mode: str

    def __post_init__(self) -> None:
        if not 1 <= self.number <= 12:
            raise ValueError(f"Camelot number must be 1-12, got {self.number}")
        if self.mode not in ("A", "B"):
            raise ValueError(f"Camelot mode must be 'A' or 'B', got {self.mode!r}")

    def __str__(self) -> str:
        return f"{self.number}{self.mode}"


def parse_camelot(text: str) -> CamelotKey:
    """Parse a Camelot code like '10B' or '5a' into a CamelotKey."""
    text = text.strip().upper()
    if len(text) < 2 or text[-1] not in ("A", "B") or not text[:-1].isdigit():
        raise ValueError(f"Invalid Camelot key: {text!r}")
    return CamelotKey(number=int(text[:-1]), mode=text[-1])


def _relative(start: CamelotKey, key: CamelotKey, direction: Direction) -> int:
    if direction == "cw":
        return (key.number - start.number) % 12
    return (start.number - key.number) % 12


def choose_direction(start: CamelotKey, keys: list[CamelotKey]) -> Direction:
    """Pick whichever direction packs the playlist's keys into a tighter arc.

    For each direction, the "spread" is how far around the wheel you'd have
    to travel from `start` to reach the farthest distinct key actually used.
    The direction with the smaller spread keeps the walk tighter. Ties keep
    "cw" as an arbitrary but consistent default.
    """
    numbers = {k.number for k in keys}
    cw_spread = max((n - start.number) % 12 for n in numbers)
    ccw_spread = max((start.number - n) % 12 for n in numbers)
    return "ccw" if ccw_spread < cw_spread else "cw"


def sort_order(
    start: CamelotKey, keys: list[CamelotKey], direction: Direction | None = None
) -> list[int]:
    """Return indices into `keys`, ordered by harmonic distance from `start`.

    Ties (identical Camelot number and mode) keep their original relative
    order. Within the same number, the mode matching `start` sorts first
    (relative major/minor is the closest harmonic neighbor).
    """
    if direction is None:
        direction = choose_direction(start, keys)

    def sort_key(key: CamelotKey) -> tuple[int, int]:
        mode_diff = 0 if key.mode == start.mode else 1
        return (_relative(start, key, direction), mode_diff)

    return sorted(range(len(keys)), key=lambda i: sort_key(keys[i]))
