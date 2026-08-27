"""Tests for playlist reorder move computation and execution."""
from typing import Any

from spotify_tools.reorder import apply_moves, compute_moves


def _simulate(current: list[str], moves: list[tuple[int, int]]) -> list[str]:
    current = list(current)
    for from_idx, to_idx in moves:
        current.insert(to_idx, current.pop(from_idx))
    return current


def test_compute_moves_returns_nothing_when_already_sorted() -> None:
    items = ["a", "b", "c"]
    assert compute_moves(items, items) == []


def test_compute_moves_reproduces_an_arbitrary_target_order() -> None:
    current = ["a", "b", "c", "d", "e"]
    target = ["c", "a", "e", "b", "d"]

    moves = compute_moves(current, target)

    assert _simulate(current, moves) == target


def test_compute_moves_handles_full_reversal() -> None:
    current = ["a", "b", "c", "d"]
    target = list(reversed(current))

    moves = compute_moves(current, target)

    assert _simulate(current, moves) == target


class FakeSpotify:
    """Minimal fake of the spotipy client for playlist_reorder_items."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []
        self._snapshot = 0

    def playlist_reorder_items(
        self,
        playlist_id: str,
        range_start: int,
        insert_before: int,
        range_length: int = 1,
        snapshot_id: str | None = None,
    ) -> dict[str, Any]:
        self.calls.append(
            {
                "playlist_id": playlist_id,
                "range_start": range_start,
                "insert_before": insert_before,
                "range_length": range_length,
                "snapshot_id": snapshot_id,
            }
        )
        self._snapshot += 1
        return {"snapshot_id": str(self._snapshot)}


def test_apply_moves_computes_insert_before_for_forward_and_backward_moves() -> None:
    sp = FakeSpotify()

    apply_moves(sp, "pl1", [(1, 3), (5, 2)])  # type: ignore[arg-type]

    assert sp.calls[0]["insert_before"] == 4  # forward move: to_idx + 1
    assert sp.calls[1]["insert_before"] == 2  # backward move: to_idx
    assert sp.calls[1]["snapshot_id"] == "1"  # chained from the previous call's result
