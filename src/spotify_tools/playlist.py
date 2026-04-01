"""Playlist read/write operations."""
from dataclasses import dataclass

import spotipy


@dataclass
class Playlist:
    id: str
    name: str
    track_count: int


@dataclass
class Track:
    uri: str
    name: str
    artists: str


def list_playlists(sp: spotipy.Spotify) -> list[Playlist]:
    """Return all playlists owned or followed by the current user, sorted by name."""
    items: list[Playlist] = []
    response = sp.current_user_playlists()
    while response:
        for p in response["items"]:
            items.append(Playlist(
                id=p["id"],
                name=p["name"],
                track_count=p["tracks"]["total"],
            ))
        response = sp.next(response) if response["next"] else None
    return sorted(items, key=lambda p: p.name.lower())


def list_tracks(sp: spotipy.Spotify, playlist_id: str) -> list[Track]:
    """Return all tracks in a playlist."""
    items: list[Track] = []
    response = sp.playlist_tracks(playlist_id)
    while response:
        for item in response["items"]:
            t = item.get("track")
            if not t or t.get("is_local"):
                continue
            items.append(Track(
                uri=t["uri"],
                name=t["name"],
                artists=", ".join(a["name"] for a in t["artists"]),
            ))
        response = sp.next(response) if response["next"] else None
    return items


def create_playlist(sp: spotipy.Spotify, name: str, public: bool = False) -> Playlist:
    """Create a new private playlist and return it."""
    user_id: str = sp.current_user()["id"]
    p = sp.user_playlist_create(user_id, name, public=public)
    return Playlist(id=p["id"], name=p["name"], track_count=0)


def add_tracks(sp: spotipy.Spotify, playlist_id: str, uris: list[str]) -> None:
    """Add tracks to a playlist (max 100 per request)."""
    for i in range(0, len(uris), 100):
        sp.playlist_add_items(playlist_id, uris[i : i + 100])


def remove_tracks(sp: spotipy.Spotify, playlist_id: str, uris: list[str]) -> None:
    """Remove all occurrences of tracks from a playlist (max 100 per request)."""
    for i in range(0, len(uris), 100):
        sp.playlist_remove_all_occurrences_of_items(playlist_id, uris[i : i + 100])
