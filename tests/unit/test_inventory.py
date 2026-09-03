"""Tests for read-only playlist/track inventory export."""

from typing import Any

from spotify_tools.inventory import (
    get_liked_songs_info,
    list_liked_song_infos,
    list_playlist_infos,
    list_playlist_track_infos,
)
from spotify_tools.playlist import LIKED_SONGS_ID


def _playlist(playlist_id: str, name: str, total: int) -> dict[str, Any]:
    return {
        "id": playlist_id,
        "name": name,
        "owner": {"id": "owner-id", "display_name": "Owner Name"},
        "public": False,
        "description": "desc",
        "tracks": {"total": total},
        "external_urls": {
            "spotify": f"https://open.spotify.com/playlist/{playlist_id}"
        },
        "snapshot_id": "snap-1",
    }


def _track_item(
    track_id: str,
    name: str,
    added_at: str = "2026-01-01T00:00:00Z",
    is_local: bool = False,
) -> dict[str, Any]:
    return {
        "added_at": added_at,
        "track": {
            "uri": f"spotify:track:{track_id}",
            "name": name,
            "artists": [{"name": "Artist"}],
            "album": {"name": "Album"},
            "external_urls": {"spotify": f"https://open.spotify.com/track/{track_id}"},
            "is_local": is_local,
        },
    }


class FakeSpotify:
    """Minimal fake of the spotipy client with pageable responses per endpoint."""

    def __init__(self, pages_by_endpoint: dict[str, list[dict[str, Any]]]) -> None:
        self._pages_by_endpoint = pages_by_endpoint
        self._endpoint_by_id: dict[int, str] = {}

    def _first_page(self, endpoint: str) -> dict[str, Any]:
        page = self._pages_by_endpoint[endpoint][0]
        self._endpoint_by_id[id(page)] = endpoint
        return page

    def current_user_playlists(self) -> dict[str, Any]:
        return self._first_page("playlists")

    def playlist_tracks(self, playlist_id: str) -> dict[str, Any]:
        return self._first_page("tracks")

    def current_user_saved_tracks(self, limit: int = 50) -> dict[str, Any]:
        return self._first_page("tracks")

    def next(self, response: dict[str, Any]) -> dict[str, Any] | None:
        endpoint = self._endpoint_by_id[id(response)]
        pages = self._pages_by_endpoint[endpoint]
        index = pages.index(response)
        if index + 1 < len(pages):
            next_page = pages[index + 1]
            self._endpoint_by_id[id(next_page)] = endpoint
            return next_page
        return None


def test_list_playlist_infos_paginates_and_sorts_by_name() -> None:
    page1 = {"items": [_playlist("2", "Zeta", 5)], "next": "page2"}
    page2 = {"items": [_playlist("1", "Alpha", 3)], "next": None}
    sp = FakeSpotify({"playlists": [page1, page2]})

    infos = list_playlist_infos(sp)  # type: ignore[arg-type]

    assert [p.name for p in infos] == ["Alpha", "Zeta"]
    assert infos[0].owner == "Owner Name"
    assert infos[0].track_count == 3
    assert infos[0].is_liked_songs is False


def test_get_liked_songs_info_is_flagged_and_uses_total() -> None:
    sp = FakeSpotify({"tracks": [{"total": 42, "items": [], "next": None}]})

    info = get_liked_songs_info(sp)  # type: ignore[arg-type]

    assert info.id == LIKED_SONGS_ID
    assert info.is_liked_songs is True
    assert info.track_count == 42


def test_list_playlist_track_infos_includes_local_flag() -> None:
    page = {
        "items": [_track_item("1", "Song A"), _track_item("2", "Local", is_local=True)],
        "next": None,
    }
    sp = FakeSpotify({"tracks": [page]})

    tracks = list_playlist_track_infos(sp, "playlist-id")  # type: ignore[arg-type]

    assert [t.is_local for t in tracks] == [False, True]
    assert tracks[0].added_at == "2026-01-01T00:00:00Z"
    assert tracks[0].album == "Album"


def test_list_liked_song_infos_paginates() -> None:
    page1 = {"items": [_track_item("1", "Song A")], "next": "page2"}
    page2 = {"items": [_track_item("2", "Song B")], "next": None}
    sp = FakeSpotify({"tracks": [page1, page2]})

    tracks = list_liked_song_infos(sp)  # type: ignore[arg-type]

    assert [t.name for t in tracks] == ["Song A", "Song B"]
