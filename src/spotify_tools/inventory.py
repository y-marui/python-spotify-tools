"""Read-only export of playlist and track details."""
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

import spotipy

from spotify_tools.playlist import LIKED_SONGS_ID


@dataclass
class PlaylistInfo:
    id: str
    name: str
    owner: str
    public: bool | None
    description: str
    track_count: int
    url: str
    snapshot_id: str | None
    is_liked_songs: bool = False


@dataclass
class TrackInfo:
    name: str
    artists: str
    album: str
    uri: str
    url: str
    added_at: str | None
    is_local: bool


def _paginate(
    sp: spotipy.Spotify, response: dict[str, Any]
) -> Iterator[dict[str, Any]]:
    """Yield items across all pages of a Spotify paging response."""
    page: dict[str, Any] | None = response
    while page:
        yield from page["items"]
        page = sp.next(page) if page["next"] else None


def _to_playlist_info(p: dict[str, Any]) -> PlaylistInfo:
    owner = p["owner"]
    return PlaylistInfo(
        id=p["id"],
        name=p["name"],
        owner=owner.get("display_name") or owner["id"],
        public=p.get("public"),
        description=p.get("description") or "",
        track_count=p["tracks"]["total"],
        url=p.get("external_urls", {}).get("spotify", ""),
        snapshot_id=p.get("snapshot_id"),
    )


def list_playlist_infos(sp: spotipy.Spotify) -> list[PlaylistInfo]:
    """Return details for all playlists owned or followed by the current user."""
    items = [_to_playlist_info(p) for p in _paginate(sp, sp.current_user_playlists())]
    return sorted(items, key=lambda p: p.name.lower())


def get_liked_songs_info(sp: spotipy.Spotify) -> PlaylistInfo:
    """Return a pseudo-playlist entry representing the user's Liked Songs."""
    response = sp.current_user_saved_tracks(limit=1)
    return PlaylistInfo(
        id=LIKED_SONGS_ID,
        name="Liked Songs",
        owner="",
        public=None,
        description="",
        track_count=response["total"],
        url="",
        snapshot_id=None,
        is_liked_songs=True,
    )


def _to_track_info(entry: dict[str, Any]) -> TrackInfo | None:
    t = entry.get("track")
    if not t:
        return None
    return TrackInfo(
        name=t["name"],
        artists=", ".join(a["name"] for a in t["artists"]),
        album=t.get("album", {}).get("name", ""),
        uri=t["uri"],
        url=t.get("external_urls", {}).get("spotify", ""),
        added_at=entry.get("added_at"),
        is_local=bool(t.get("is_local")),
    )


def list_playlist_track_infos(sp: spotipy.Spotify, playlist_id: str) -> list[TrackInfo]:
    """Return details for all tracks in a playlist."""
    entries = _paginate(sp, sp.playlist_tracks(playlist_id))
    return [info for info in (_to_track_info(e) for e in entries) if info]


def list_liked_song_infos(sp: spotipy.Spotify) -> list[TrackInfo]:
    """Return details for all tracks in the user's Liked Songs."""
    entries = _paginate(sp, sp.current_user_saved_tracks(limit=50))
    return [info for info in (_to_track_info(e) for e in entries) if info]
