"""Tests for source dispatch between playlists and Liked Songs, and the
playlist-group protection guard applied to move operations."""

from typing import Any

import pytest

from spotify_tools.groups import PlaylistRule, ProtectedPlaylistError
from spotify_tools.playlist import LIKED_SONGS_ID, Playlist, Track
from spotify_tools.split_playlist import (
    _confirm_and_move,
    _fetch_source_tracks,
    _filter_modifiable,
    _remove_from_source,
)


class FakeSpotify:
    """Minimal fake of the spotipy client for playlist and saved-tracks endpoints."""

    def __init__(self) -> None:
        self.playlist_tracks_calls: list[str] = []
        self.saved_tracks_called = False
        self.removed_playlist: list[tuple[str, list[str]]] = []
        self.removed_saved: list[str] = []
        self.added_playlist: list[tuple[str, list[str]]] = []

    def playlist_tracks(self, playlist_id: str) -> dict[str, Any]:
        self.playlist_tracks_calls.append(playlist_id)
        return {"items": [], "next": None}

    def current_user_saved_tracks(self, limit: int = 50) -> dict[str, Any]:
        self.saved_tracks_called = True
        return {"items": [], "next": None}

    def next(self, response: dict[str, Any]) -> None:
        return None

    def playlist_add_items(self, playlist_id: str, uris: list[str]) -> None:
        self.added_playlist.append((playlist_id, uris))

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


def test_filter_modifiable_returns_all_when_no_rules_configured() -> None:
    playlists = [Playlist(id="a", name="A", track_count=0)]

    assert _filter_modifiable(playlists, []) == playlists


def test_filter_modifiable_excludes_protected_and_unclassified() -> None:
    playlists = [
        Playlist(id="active", name="Active", track_count=0),
        Playlist(id="blocked", name="Protected", track_count=0),
        Playlist(id="unknown", name="Unclassified", track_count=0),
    ]
    rules = [
        PlaylistRule(group="active", id="active"),
        PlaylistRule(group="protected", id="blocked"),
    ]

    result = _filter_modifiable(playlists, rules)

    assert [p.id for p in result] == ["active"]


def test_confirm_and_move_blocks_protected_target(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("builtins.input", lambda _: "y")
    sp = FakeSpotify()
    source = Playlist(id="src", name="Source", track_count=0)
    target = Playlist(id="blocked", name="Protected", track_count=0)
    rules = [
        PlaylistRule(group="active", id="src"),
        PlaylistRule(group="protected", id="blocked"),
    ]

    with pytest.raises(ProtectedPlaylistError):
        _confirm_and_move(sp, source, target, [], rules, {"blocked"})  # type: ignore[arg-type]

    assert sp.added_playlist == []


def test_confirm_and_move_blocks_unclassified_source(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("builtins.input", lambda _: "y")
    sp = FakeSpotify()
    source = Playlist(id="unknown", name="Unclassified", track_count=0)
    target = Playlist(id="dest", name="Dest", track_count=0)
    rules = [PlaylistRule(group="active", id="dest")]

    with pytest.raises(ProtectedPlaylistError):
        _confirm_and_move(sp, source, target, [], rules, {"dest"})  # type: ignore[arg-type]

    assert sp.added_playlist == []


def test_confirm_and_move_allows_newly_created_target(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A freshly created target playlist isn't in existing_target_ids, so the
    unclassified guard shouldn't block it."""
    monkeypatch.setattr("builtins.input", lambda _: "y")
    sp = FakeSpotify()
    source = Playlist(id="src", name="Source", track_count=0)
    new_target = Playlist(id="new-id", name="New Playlist", track_count=0)
    selected = [Track(uri="spotify:track:1", name="Song", artists="Artist")]
    rules = [PlaylistRule(group="active", id="src")]

    _confirm_and_move(sp, source, new_target, selected, rules, set())  # type: ignore[arg-type]

    assert sp.added_playlist == [("new-id", ["spotify:track:1"])]


def test_confirm_and_move_blocks_new_target_colliding_with_protected_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A newly created playlist isn't exempt from the guard if its name
    collides with a protected rule (e.g. the user named it after an
    existing protected playlist)."""
    monkeypatch.setattr("builtins.input", lambda _: "y")
    sp = FakeSpotify()
    source = Playlist(id="src", name="Source", track_count=0)
    new_target = Playlist(id="new-id", name="Family Shared", track_count=0)
    rules = [
        PlaylistRule(group="active", id="src"),
        PlaylistRule(group="protected", name="Family Shared"),
    ]

    with pytest.raises(ProtectedPlaylistError):
        _confirm_and_move(sp, source, new_target, [], rules, set())  # type: ignore[arg-type]

    assert sp.added_playlist == []
