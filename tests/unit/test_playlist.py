"""Tests for Liked Songs read/remove operations, and playlist metadata
create/update/ownership helpers."""
from typing import Any

import pytest

from spotify_tools.playlist import (
    LIKED_SONGS_ID,
    NotPlaylistOwnerError,
    PlaylistDetails,
    create_playlist,
    get_liked_songs_playlist,
    get_playlist_details,
    get_playlist_name,
    list_saved_tracks,
    remove_saved_tracks,
    require_owned_by_current_user,
    update_playlist_details,
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


class _FakeSpotifyForPlaylistOps:
    """Minimal fake of the spotipy client for create/update/details endpoints."""

    def __init__(self, playlist_response: dict[str, Any] | None = None) -> None:
        self.created: dict[str, Any] | None = None
        self.changed: dict[str, Any] | None = None
        self._playlist_response = playlist_response

    def current_user_playlist_create(
        self,
        name: str,
        public: bool = True,
        collaborative: bool = False,
        description: str = "",
    ) -> dict[str, Any]:
        self.created = {
            "name": name,
            "public": public,
            "collaborative": collaborative,
            "description": description,
        }
        return {"id": "new-id", "name": name}

    def playlist(self, playlist_id: str, fields: str | None = None) -> dict[str, Any]:
        assert self._playlist_response is not None
        return self._playlist_response

    def playlist_change_details(self, playlist_id: str, **kwargs: Any) -> None:
        self.changed = {"playlist_id": playlist_id, **kwargs}


def test_create_playlist_uses_current_user_playlist_create() -> None:
    sp = _FakeSpotifyForPlaylistOps()

    playlist = create_playlist(
        sp, "New Playlist", description="desc", public=True  # type: ignore[arg-type]
    )

    assert playlist.id == "new-id"
    assert sp.created == {
        "name": "New Playlist",
        "public": True,
        "collaborative": False,
        "description": "desc",
    }


def test_create_playlist_rejects_collaborative_and_public() -> None:
    sp = _FakeSpotifyForPlaylistOps()

    with pytest.raises(ValueError):
        create_playlist(  # type: ignore[arg-type]
            sp, "New Playlist", public=True, collaborative=True
        )


def test_get_playlist_details_returns_owner_and_metadata() -> None:
    sp = _FakeSpotifyForPlaylistOps(
        playlist_response={
            "id": "abc",
            "name": "My Playlist",
            "description": "desc",
            "public": True,
            "collaborative": False,
            "owner": {"id": "owner-1"},
        }
    )

    details = get_playlist_details(sp, "abc")  # type: ignore[arg-type]

    assert details == PlaylistDetails(
        id="abc",
        name="My Playlist",
        owner_id="owner-1",
        description="desc",
        public=True,
        collaborative=False,
    )


def test_update_playlist_details_requires_at_least_one_field() -> None:
    sp = _FakeSpotifyForPlaylistOps()

    with pytest.raises(ValueError):
        update_playlist_details(sp, "abc")  # type: ignore[arg-type]


def test_update_playlist_details_forwards_changed_fields() -> None:
    sp = _FakeSpotifyForPlaylistOps()

    update_playlist_details(sp, "abc", name="New Name")  # type: ignore[arg-type]

    assert sp.changed == {
        "playlist_id": "abc",
        "name": "New Name",
        "description": None,
        "public": None,
        "collaborative": None,
    }


def test_require_owned_by_current_user_allows_owner() -> None:
    details = PlaylistDetails(
        id="abc",
        name="Mine",
        owner_id="me",
        description="",
        public=False,
        collaborative=False,
    )

    require_owned_by_current_user(details, "me")


def test_require_owned_by_current_user_rejects_non_owner() -> None:
    details = PlaylistDetails(
        id="abc",
        name="Theirs",
        owner_id="someone-else",
        description="",
        public=False,
        collaborative=False,
    )

    with pytest.raises(NotPlaylistOwnerError):
        require_owned_by_current_user(details, "me")
