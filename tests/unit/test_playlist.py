"""Tests for Liked Songs read/remove operations."""
from typing import Any

from spotify_tools.playlist import (
    LIKED_SONGS_ID,
    get_liked_songs_playlist,
    get_playlist_name,
    list_saved_tracks,
    remove_saved_tracks,
)


def _saved_track(track_id: str, name: str, is_local: bool = False) -> dict[str, Any]:
    return {
        "track": {
            "uri": f"spotify:track:{track_id}",
            "name": name,
            "artists": [{"name": "Artist"}],
            "is_local": is_local,
        }
    }


class FakeSpotify:
    """Minimal fake of the spotipy client for saved-tracks endpoints."""

    def __init__(self, pages: list[dict[str, Any]]) -> None:
        self._pages = pages
        self.deleted: list[list[str]] = []

    def current_user_saved_tracks(self, limit: int = 50) -> dict[str, Any]:
        return self._pages[0]

    def next(self, response: dict[str, Any]) -> dict[str, Any] | None:
        index = self._pages.index(response)
        if index + 1 < len(self._pages):
            return self._pages[index + 1]
        return None

    def current_user_saved_tracks_delete(self, tracks: list[str]) -> None:
        self.deleted.append(tracks)

    def playlist(self, playlist_id: str, fields: str | None = None) -> dict[str, Any]:
        return {"name": f"Playlist {playlist_id}"}


def test_get_liked_songs_playlist_returns_total_count() -> None:
    sp = FakeSpotify([{"total": 3, "items": [], "next": None}])

    playlist = get_liked_songs_playlist(sp)  # type: ignore[arg-type]

    assert playlist.id == LIKED_SONGS_ID
    assert playlist.track_count == 3


def test_list_saved_tracks_paginates_and_skips_local() -> None:
    page1 = {
        "items": [
            _saved_track("1", "Song A"),
            _saved_track("2", "Local", is_local=True),
        ],
        "next": "page2",
    }
    page2 = {"items": [_saved_track("3", "Song B")], "next": None}
    sp = FakeSpotify([page1, page2])

    tracks = list_saved_tracks(sp)  # type: ignore[arg-type]

    assert [t.name for t in tracks] == ["Song A", "Song B"]


def test_get_playlist_name_returns_name() -> None:
    sp = FakeSpotify([{"total": 0, "items": [], "next": None}])

    name = get_playlist_name(sp, "abc123")  # type: ignore[arg-type]

    assert name == "Playlist abc123"


def test_remove_saved_tracks_chunks_by_fifty() -> None:
    sp = FakeSpotify([{"total": 0, "items": [], "next": None}])
    uris = [f"spotify:track:{i}" for i in range(120)]

    remove_saved_tracks(sp, uris)  # type: ignore[arg-type]

    assert [len(chunk) for chunk in sp.deleted] == [50, 50, 20]
    assert sp.deleted[0][0] == "0"
