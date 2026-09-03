"""Tests for inventory CLI filtering, formatting, and argument parsing."""

import json
from dataclasses import replace

from spotify_tools.inventory import PlaylistInfo, TrackInfo
from spotify_tools.inventory_cli import (
    _filter_playlists,
    _format_playlists_markdown,
    _format_tracks_markdown,
    _parse_args,
    _to_json,
)

_ALPHA = PlaylistInfo(
    id="1",
    name="Alpha",
    owner="alice",
    public=True,
    description="a|b",
    track_count=10,
    url="https://open.spotify.com/playlist/1",
    snapshot_id="snap-1",
)
_BETA = PlaylistInfo(
    id="2",
    name="Beta List",
    owner="bob",
    public=False,
    description="",
    track_count=2,
    url="https://open.spotify.com/playlist/2",
    snapshot_id=None,
)
_LIKED = PlaylistInfo(
    id="liked",
    name="Liked Songs",
    owner="",
    public=None,
    description="",
    track_count=5,
    url="",
    snapshot_id=None,
    is_liked_songs=True,
)


def test_filter_playlists_by_name_prefix_and_owner() -> None:
    playlists = [_ALPHA, _BETA, _LIKED]

    assert _filter_playlists(playlists, "Alpha", None, None) == [_ALPHA]
    assert _filter_playlists(playlists, None, "Beta", None) == [_BETA]
    assert _filter_playlists(playlists, None, None, "bob") == [_BETA]
    assert _filter_playlists(playlists, None, None, None) == playlists


def test_format_playlists_markdown_escapes_pipe_and_flags_liked_songs() -> None:
    output = _format_playlists_markdown([_ALPHA, _LIKED])

    lines = output.splitlines()
    assert "a\\|b" in lines[2]
    assert "Liked Songs (Liked Songs)" in lines[3]


def test_format_playlists_markdown_escapes_pipe_in_group_column() -> None:
    playlist = replace(_BETA, group="team|shared")

    output = _format_playlists_markdown([playlist])

    assert "team\\|shared" in output.splitlines()[2]
    assert "team|shared" not in output.splitlines()[2]


def test_format_playlists_markdown_shows_unclassified_when_no_group() -> None:
    output = _format_playlists_markdown([_BETA])

    assert "(unclassified)" in output.splitlines()[2]


def test_format_tracks_markdown_includes_local_flag() -> None:
    track = TrackInfo(
        name="Song",
        artists="Artist",
        album="Album",
        uri="spotify:track:1",
        url="https://open.spotify.com/track/1",
        added_at="2026-01-01T00:00:00Z",
        is_local=True,
    )

    output = _format_tracks_markdown([track])

    assert "True" in output.splitlines()[2]


def test_to_json_round_trips_dataclass_fields() -> None:
    output = _to_json([_ALPHA])
    parsed = json.loads(output)

    assert parsed == [
        {
            "id": "1",
            "name": "Alpha",
            "owner": "alice",
            "public": True,
            "description": "a|b",
            "track_count": 10,
            "url": "https://open.spotify.com/playlist/1",
            "snapshot_id": "snap-1",
            "is_liked_songs": False,
            "group": None,
        }
    ]


def test_parse_args_playlists_defaults_to_markdown() -> None:
    args = _parse_args(["playlists"])

    assert args.command == "playlists"
    assert args.format == "md"
    assert args.name is None


def test_parse_args_tracks_requires_playlist_id() -> None:
    args = _parse_args(["tracks", "liked", "--format", "json"])

    assert args.command == "tracks"
    assert args.playlist_id == "liked"
    assert args.format == "json"
