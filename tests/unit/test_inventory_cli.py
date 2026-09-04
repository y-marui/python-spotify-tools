"""Tests for inventory CLI filtering, formatting, and argument parsing."""

import json
from dataclasses import replace
from typing import Any

import pytest
from typer.testing import CliRunner

from spotify_tools.inventory import PlaylistInfo, TrackInfo
from spotify_tools.inventory_cli import (
    _filter_playlists,
    _format_playlists_markdown,
    _format_tracks_markdown,
    _to_json,
    app,
)

runner = CliRunner()

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


# --- CLI wiring (typer option/argument parsing end-to-end) ---


class FakeSpotify:
    """Minimal fake of the spotipy client for the read-only inventory endpoints."""

    def __init__(self, playlists: list[dict[str, Any]]) -> None:
        self._playlists = playlists

    def current_user_playlists(self) -> dict[str, Any]:
        return {"items": self._playlists, "next": None}

    def current_user_saved_tracks(self, limit: int = 50) -> dict[str, Any]:
        return {"items": [], "next": None, "total": 0}

    def next(self, response: dict[str, Any]) -> None:
        return None


def _playlist_response(playlist_id: str, name: str, owner: str) -> dict[str, Any]:
    return {
        "id": playlist_id,
        "name": name,
        "owner": {"id": owner},
        "public": True,
        "description": "",
        "tracks": {"total": 0},
        "external_urls": {
            "spotify": f"https://open.spotify.com/playlist/{playlist_id}"
        },
        "snapshot_id": "snap",
    }


def test_playlists_command_applies_prefix_filter_and_json_format(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sp = FakeSpotify(
        [
            _playlist_response("1", "Work Mix", "alice"),
            _playlist_response("2", "Other", "bob"),
        ]
    )
    monkeypatch.setattr("spotify_tools.inventory_cli.get_readonly_client", lambda: sp)
    monkeypatch.setattr("spotify_tools.inventory_cli.load_rules", lambda: [])

    result = runner.invoke(app, ["playlists", "--prefix", "Work", "--format", "json"])

    assert result.exit_code == 0, result.output
    parsed = json.loads(result.output)
    assert [p["name"] for p in parsed] == ["Work Mix"]


def test_tracks_command_defaults_to_markdown(monkeypatch: pytest.MonkeyPatch) -> None:
    sp = FakeSpotify([])
    monkeypatch.setattr("spotify_tools.inventory_cli.get_readonly_client", lambda: sp)

    result = runner.invoke(app, ["tracks", "liked"])

    assert result.exit_code == 0, result.output
    assert "| Name | Artists |" in result.output
