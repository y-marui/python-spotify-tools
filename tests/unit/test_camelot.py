"""Tests for Camelot key parsing and harmonic-mixing sort order."""
import pytest

from spotify_tools.camelot import (
    CamelotKey,
    choose_direction,
    parse_camelot,
    sort_order,
)


def test_parse_camelot_accepts_lowercase_and_whitespace() -> None:
    assert parse_camelot(" 5a ") == CamelotKey(5, "A")
    assert parse_camelot("10B") == CamelotKey(10, "B")


@pytest.mark.parametrize("text", ["", "B10", "10C", "13A", "0A"])
def test_parse_camelot_rejects_invalid_input(text: str) -> None:
    with pytest.raises(ValueError):
        parse_camelot(text)


def test_choose_direction_prefers_clockwise_when_keys_cluster_that_way() -> None:
    start = CamelotKey(1, "A")
    keys = [start, CamelotKey(2, "A"), CamelotKey(3, "A")]
    assert choose_direction(start, keys) == "cw"


def test_choose_direction_prefers_counterclockwise_when_keys_cluster_that_way() -> None:
    start = CamelotKey(1, "A")
    keys = [start, CamelotKey(11, "A"), CamelotKey(10, "A")]
    assert choose_direction(start, keys) == "ccw"


def test_choose_direction_defaults_to_clockwise_on_a_tie() -> None:
    start = CamelotKey(1, "A")
    keys = [start, CamelotKey(7, "A")]  # directly opposite: both spreads are 6
    assert choose_direction(start, keys) == "cw"


def test_choose_direction_matches_manually_verified_real_playlist() -> None:
    """Regression check against the actual 'Ins' playlist key distribution
    (see the reordering session that motivated this module)."""
    keys = [
        parse_camelot(k)
        for k in [
            "10B", "10A", "9B", "5A", "8B", "4A", "4B", "8B", "7A", "6A",
            "8A", "1A", "6B", "7A", "7A", "5A", "8B", "9B", "1B", "7B",
        ]
    ]
    assert choose_direction(keys[0], keys) == "ccw"


def test_sort_order_groups_same_number_with_matching_mode_first() -> None:
    start = CamelotKey(5, "A")
    keys = [CamelotKey(4, "A"), CamelotKey(6, "A"), CamelotKey(5, "B"), start]

    order = sort_order(start, keys, direction="cw")

    assert order == [3, 2, 1, 0]


def test_sort_order_matches_manually_verified_real_playlist_clockwise() -> None:
    """Regression check against the order actually applied to the 'Ins'
    playlist (computed and verified by hand before this module existed)."""
    keys = [
        parse_camelot(k)
        for k in [
            "10B", "10A", "9B", "5A", "8B", "4A", "4B", "8B", "7A", "6A",
            "8A", "1A", "6B", "7A", "7A", "5A", "8B", "9B", "1B", "7B",
        ]
    ]

    order = sort_order(keys[0], keys, direction="cw")

    assert order == [
        0, 1, 18, 11, 6, 5, 3, 15, 12, 9, 19, 8, 13, 14, 4, 7, 16, 10, 2, 17,
    ]
