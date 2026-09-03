"""Tests for the reorder-by-key CLI's key-file parsing."""

from pathlib import Path

import pytest

from spotify_tools.reorder_by_key_cli import _read_keys


def test_read_keys_parses_lines_matching_track_count(tmp_path: Path) -> None:
    path = tmp_path / "keys.txt"
    path.write_text("10B\n10A\n9B\n")

    keys = _read_keys(path, track_count=3)

    assert [str(k) for k in keys] == ["10B", "10A", "9B"]


def test_read_keys_skips_blank_lines(tmp_path: Path) -> None:
    path = tmp_path / "keys.txt"
    path.write_text("10B\n\n10A\n")

    keys = _read_keys(path, track_count=2)

    assert [str(k) for k in keys] == ["10B", "10A"]


def test_read_keys_rejects_count_mismatch(tmp_path: Path) -> None:
    path = tmp_path / "keys.txt"
    path.write_text("10B\n10A\n")

    with pytest.raises(ValueError, match="2 key"):
        _read_keys(path, track_count=3)
