"""In-place playlist reordering via the Spotify Web API."""

import spotipy


def compute_moves(current: list[str], target: list[str]) -> list[tuple[int, int]]:
    """Compute a sequence of single-item (from_index, to_index) moves that
    transforms `current` into `target`.

    Both lists must contain the same items (order may differ). Positions
    are 0-based and refer to the array state *as of that step* (each move
    is applied to `current` before computing the next one).
    """
    current = list(current)
    moves: list[tuple[int, int]] = []
    for i, item in enumerate(target):
        j = current.index(item, i)
        if j != i:
            moves.append((j, i))
            current.insert(i, current.pop(j))
    return moves


def apply_moves(
    sp: spotipy.Spotify, playlist_id: str, moves: list[tuple[int, int]]
) -> None:
    """Execute precomputed (from_index, to_index) moves against a live playlist."""
    snapshot_id = None
    for from_idx, to_idx in moves:
        insert_before = to_idx if to_idx <= from_idx else to_idx + 1
        result = sp.playlist_reorder_items(
            playlist_id,
            range_start=from_idx,
            insert_before=insert_before,
            range_length=1,
            snapshot_id=snapshot_id,
        )
        snapshot_id = result["snapshot_id"]
