"""Tests for source dispatch between playlists and Liked Songs."""
from typing import Any

from spotify_tools.playlist import LIKED_SONGS_ID, Playlist
from spotify_tools.split_playlist import _fetch_source_tracks, _remove_from_source


class FakeSpotify:
    """Minimal fake of the spotipy client for playlist and saved-tracks endpoints."""

    def __init__(self) -> None:
        self.playlist_tracks_calls: list[str] = []
        self.saved_tracks_called = False
        self.removed_playlist: list[tuple[str, list[str]]] = []
        self.removed_saved: list[str] = []

    def playlist_tracks(self, playlist_id: str) -> dict[str, Any]:
        self.playlist_tracks_calls.append(playlist_id)
        return {"items": [], "next": None}

    def current_user_saved_tracks(self, limit: int = 50) -> dict[str, Any]:
        self.saved_tracks_called = True
        return {"items": [], "next": None}

    def next(self, response: dict[str, Any]) -> None:
        return None

    def playlist_remove_all_occurrences_of_items(
        self, playlist_id: str, uris: list[str]
    ) -> None:
        self.removed_playlist.append((playlist_id, uris))

    def current_user_saved_tracks_delete(self, tracks: list[str]) -> None:
        self.removed_saved.extend(tracks)


def test_fetch_source_tracks_uses_saved_tracks_for_liked_songs() -> None:
    sp = FakeSpotify()
    liked_songs = Playlist(id=LIKED_SONGS_ID, name="Liked Songs", track_count=0)

    _fetch_source_tracks(sp, liked_songs)  # type: ignore[arg-type]

    assert sp.saved_tracks_called
    assert sp.playlist_tracks_calls == []


def test_fetch_source_tracks_uses_playlist_tracks_for_normal_playlist() -> None:
    sp = FakeSpotify()
    playlist = Playlist(id="abc", name="My Playlist", track_count=0)

    _fetch_source_tracks(sp, playlist)  # type: ignore[arg-type]

    assert sp.playlist_tracks_calls == ["abc"]
    assert not sp.saved_tracks_called


def test_remove_from_source_deletes_saved_tracks_for_liked_songs() -> None:
    sp = FakeSpotify()
    liked_songs = Playlist(id=LIKED_SONGS_ID, name="Liked Songs", track_count=0)

    _remove_from_source(sp, liked_songs, ["spotify:track:1", "spotify:track:2"])  # type: ignore[arg-type]

    assert sp.removed_saved == ["1", "2"]
    assert sp.removed_playlist == []


def test_remove_from_source_removes_playlist_items_for_normal_playlist() -> None:
    sp = FakeSpotify()
    playlist = Playlist(id="abc", name="My Playlist", track_count=0)

    _remove_from_source(sp, playlist, ["spotify:track:1"])  # type: ignore[arg-type]

    assert sp.removed_playlist == [("abc", ["spotify:track:1"])]
    assert sp.removed_saved == []
