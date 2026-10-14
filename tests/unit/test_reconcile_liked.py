"""Tests for Liked Songs reconciliation: matching rules and the pre-removal
re-verification of the retained target track."""

from typing import Any

import pytest

from spotify_tools.playlist import Track
from spotify_tools.reconcile_liked import Match, find_matches, verify_retained


def _track(uri: str, isrc: str | None = None, ms: int = 200000) -> Track:
    return Track(uri=uri, name=f"n{uri}", artists="a", isrc=isrc, duration_ms=ms)


class FakeSpotify:
    def __init__(self, uris: list[str]) -> None:
        self.uris = uris

    def playlist_tracks(self, playlist_id: str) -> dict[str, Any]:
        items = [
            {"track": {"uri": u, "name": "x", "artists": [{"name": "a"}]}}
            for u in self.uris
        ]
        return {"items": items, "next": None}

    def next(self, response: dict[str, Any]) -> None:
        return None


def test_exact_uri_match_is_exact() -> None:
    matches = find_matches([_track("u1")], [_track("u1")])
    assert len(matches) == 1 and matches[0].is_exact


def test_same_isrc_different_uri_is_alternate() -> None:
    matches = find_matches([_track("u1", "ISRC1")], [_track("u2", "ISRC1")])
    assert len(matches) == 1
    assert not matches[0].is_exact
    assert matches[0].retained.uri == "u2"


def test_same_title_without_isrc_is_not_matched() -> None:
    liked = Track(uri="u1", name="Song", artists="a")
    target = Track(uri="u2", name="Song", artists="a")
    assert find_matches([liked], [target]) == []


def test_exact_match_preferred_over_isrc() -> None:
    target = [_track("u2", "I"), _track("u1", "I")]
    (match,) = find_matches([_track("u1", "I")], target)
    assert match.is_exact


def test_duration_gap() -> None:
    m = Match(_track("u1", ms=200000), _track("u2", ms=203500))
    assert m.duration_gap_ms == 3500
    assert Match(Track("a", "n", "x"), _track("b")).duration_gap_ms is None


def test_verify_retained_drops_vanished_tracks() -> None:
    kept = Match(_track("u1"), _track("t1"))
    gone = Match(_track("u2"), _track("t2"))
    sp = FakeSpotify(["t1"])
    ok, missing = verify_retained(sp, "pl", [kept, gone])  # type: ignore[arg-type]
    assert ok == [kept]
    assert missing == [gone]


@pytest.mark.parametrize("isrc", [None, ""])
def test_missing_isrc_never_alternate(isrc: str | None) -> None:
    assert find_matches([_track("u1", isrc)], [_track("u2", isrc)]) == []
