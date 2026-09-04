"""CLI to export playlist/track inventory as Markdown or JSON (read-only)."""

import json
from collections.abc import Sequence
from dataclasses import asdict, replace
from enum import StrEnum
from typing import Annotated

import typer

from spotify_tools import __version__
from spotify_tools.auth import get_readonly_client
from spotify_tools.groups import classify, load_rules
from spotify_tools.inventory import (
    PlaylistInfo,
    TrackInfo,
    get_liked_songs_info,
    list_liked_song_infos,
    list_playlist_infos,
    list_playlist_track_infos,
)
from spotify_tools.playlist import LIKED_SONGS_ID

app = typer.Typer(
    help="Export Spotify playlist/track inventory (read-only).",
    context_settings={"help_option_names": ["-h", "--help"]},
)


class OutputFormat(StrEnum):
    md = "md"
    json = "json"


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"spotify-inventory {__version__}")
        raise typer.Exit()


@app.callback()
def _cli(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-V",
            callback=_version_callback,
            is_eager=True,
            help="Show the version and exit.",
        ),
    ] = False,
) -> None:
    pass


def _filter_playlists(
    playlists: list[PlaylistInfo],
    name: str | None,
    prefix: str | None,
    owner: str | None,
) -> list[PlaylistInfo]:
    result = playlists
    if name:
        result = [p for p in result if p.name == name]
    if prefix:
        result = [p for p in result if p.name.startswith(prefix)]
    if owner:
        result = [p for p in result if p.owner == owner]
    return result


def _escape_md(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def _annotate_groups(playlists: list[PlaylistInfo]) -> list[PlaylistInfo]:
    rules = load_rules()
    return [replace(p, group=classify(p.id, p.name, rules)) for p in playlists]


def _format_playlists_markdown(playlists: list[PlaylistInfo]) -> str:
    lines = [
        "| ID | Name | Owner | Public | Tracks | Group | Description | URL |"
        " Snapshot |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for p in playlists:
        name = _escape_md(p.name) + (" (Liked Songs)" if p.is_liked_songs else "")
        group = _escape_md(p.group) if p.group else "(unclassified)"
        lines.append(
            f"| {p.id} | {name} | {_escape_md(p.owner)} | {p.public} | "
            f"{p.track_count} | {group} | {_escape_md(p.description)} | {p.url} | "
            f"{p.snapshot_id or ''} |"
        )
    return "\n".join(lines)


def _format_tracks_markdown(tracks: list[TrackInfo]) -> str:
    lines = [
        "| Name | Artists | Album | URI | URL | Added At | Local |",
        "|---|---|---|---|---|---|---|",
    ]
    for t in tracks:
        lines.append(
            f"| {_escape_md(t.name)} | {_escape_md(t.artists)} | "
            f"{_escape_md(t.album)} | {t.uri} | {t.url} | "
            f"{t.added_at or ''} | {t.is_local} |"
        )
    return "\n".join(lines)


def _to_json(items: Sequence[PlaylistInfo | TrackInfo]) -> str:
    return json.dumps([asdict(i) for i in items], ensure_ascii=False, indent=2)


@app.command("playlists", help="List playlists")
def playlists_command(
    name: Annotated[str | None, typer.Option(help="Exact name filter")] = None,
    prefix: Annotated[str | None, typer.Option(help="Name prefix filter")] = None,
    owner: Annotated[str | None, typer.Option(help="Owner display name filter")] = None,
    format: Annotated[
        OutputFormat, typer.Option(help="Output format")
    ] = OutputFormat.md,
) -> None:
    sp = get_readonly_client()
    playlists = [get_liked_songs_info(sp), *list_playlist_infos(sp)]
    playlists = _filter_playlists(playlists, name, prefix, owner)
    playlists = _annotate_groups(playlists)
    if format == OutputFormat.json:
        print(_to_json(playlists))
    else:
        print(_format_playlists_markdown(playlists))


@app.command("tracks", help="List tracks in a playlist")
def tracks_command(
    playlist_id: Annotated[
        str, typer.Argument(help="Playlist ID, or 'liked' for Liked Songs")
    ],
    format: Annotated[
        OutputFormat, typer.Option(help="Output format")
    ] = OutputFormat.md,
) -> None:
    sp = get_readonly_client()
    if playlist_id in ("liked", LIKED_SONGS_ID):
        tracks = list_liked_song_infos(sp)
    else:
        tracks = list_playlist_track_infos(sp, playlist_id)
    if format == OutputFormat.json:
        print(_to_json(tracks))
    else:
        print(_format_tracks_markdown(tracks))


def main() -> None:
    app()


if __name__ == "__main__":
    main()
