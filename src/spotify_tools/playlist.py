"""Playlist read/write operations."""

from dataclasses import dataclass

import spotipy

LIKED_SONGS_ID = "__liked_songs__"


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


@dataclass
class PlaylistDetails:
    id: str
    name: str
    owner_id: str
    description: str
    public: bool | None
    collaborative: bool


class NotPlaylistOwnerError(Exception):
    """Raised when an operation targets a playlist not owned by the current user."""


def list_playlists(sp: spotipy.Spotify) -> list[Playlist]:
    """Return all playlists owned or followed by the current user, sorted by name."""
    items: list[Playlist] = []
    response = sp.current_user_playlists()
    while response:
        for p in response["items"]:
            items.append(
                Playlist(
                    id=p["id"],
                    name=p["name"],
                    track_count=p["tracks"]["total"],
                )
            )
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
            items.append(
                Track(
                    uri=t["uri"],
                    name=t["name"],
                    artists=", ".join(a["name"] for a in t["artists"]),
                )
            )
        response = sp.next(response) if response["next"] else None
    return items


def get_playlist_name(sp: spotipy.Spotify, playlist_id: str) -> str:
    """Return a playlist's name."""
    name: str = sp.playlist(playlist_id, fields="name")["name"]
    return name


def get_liked_songs_playlist(sp: spotipy.Spotify) -> Playlist:
    """Return a pseudo-playlist representing the user's Liked Songs."""
    response = sp.current_user_saved_tracks(limit=1)
    return Playlist(
        id=LIKED_SONGS_ID, name="Liked Songs", track_count=response["total"]
    )


def list_saved_tracks(sp: spotipy.Spotify) -> list[Track]:
    """Return all tracks in the user's Liked Songs."""
    items: list[Track] = []
    response = sp.current_user_saved_tracks(limit=50)
    while response:
        for item in response["items"]:
            t = item.get("track")
            if not t or t.get("is_local"):
                continue
            items.append(
                Track(
                    uri=t["uri"],
                    name=t["name"],
                    artists=", ".join(a["name"] for a in t["artists"]),
                )
            )
        response = sp.next(response) if response["next"] else None
    return items


def create_playlist(
    sp: spotipy.Spotify,
    name: str,
    public: bool = False,
    collaborative: bool = False,
    description: str | None = None,
) -> Playlist:
    """Create a new playlist and return it (private by default)."""
    if collaborative and public:
        raise ValueError("A collaborative playlist cannot be public.")
    p = sp.current_user_playlist_create(
        name,
        public=public,
        collaborative=collaborative,
        description=description or "",
    )
    return Playlist(id=p["id"], name=p["name"], track_count=0)


def get_playlist_details(sp: spotipy.Spotify, playlist_id: str) -> PlaylistDetails:
    """Return a playlist's editable metadata and owner."""
    p = sp.playlist(
        playlist_id, fields="id,name,description,public,collaborative,owner.id"
    )
    return PlaylistDetails(
        id=p["id"],
        name=p["name"],
        owner_id=p["owner"]["id"],
        description=p.get("description") or "",
        public=p.get("public"),
        collaborative=bool(p.get("collaborative")),
    )


def update_playlist_details(
    sp: spotipy.Spotify,
    playlist_id: str,
    name: str | None = None,
    description: str | None = None,
    public: bool | None = None,
    collaborative: bool | None = None,
) -> None:
    """Update a playlist's name/description/public/collaborative state.

    Raises ValueError if no field is given, since Spotify's API silently
    no-ops on an empty payload.
    """
    if all(v is None for v in (name, description, public, collaborative)):
        raise ValueError("At least one field must be provided to update.")
    if collaborative and public:
        raise ValueError("A collaborative playlist cannot be public.")
    sp.playlist_change_details(
        playlist_id,
        name=name,
        description=description,
        public=public,
        collaborative=collaborative,
    )


def require_owned_by_current_user(
    details: PlaylistDetails, current_user_id: str
) -> None:
    """Raise NotPlaylistOwnerError if the playlist isn't owned by the current user."""
    if details.owner_id != current_user_id:
        raise NotPlaylistOwnerError(
            f"'{details.name}' is owned by '{details.owner_id}', not the "
            "current user; refusing to modify."
        )


def add_tracks(sp: spotipy.Spotify, playlist_id: str, uris: list[str]) -> None:
    """Add tracks to a playlist (max 100 per request)."""
    for i in range(0, len(uris), 100):
        sp.playlist_add_items(playlist_id, uris[i : i + 100])


def remove_tracks(sp: spotipy.Spotify, playlist_id: str, uris: list[str]) -> None:
    """Remove all occurrences of tracks from a playlist (max 100 per request)."""
    for i in range(0, len(uris), 100):
        sp.playlist_remove_all_occurrences_of_items(playlist_id, uris[i : i + 100])


def remove_saved_tracks(sp: spotipy.Spotify, uris: list[str]) -> None:
    """Remove tracks from Liked Songs (max 50 per request)."""
    track_ids = [uri.rsplit(":", 1)[-1] for uri in uris]
    for i in range(0, len(track_ids), 50):
        sp.current_user_saved_tracks_delete(track_ids[i : i + 50])
