"""CLI to export playlist/track inventory as Markdown or JSON (read-only)."""
import argparse
import json
from collections.abc import Sequence
from dataclasses import asdict, replace

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


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export Spotify playlist/track inventory (read-only)."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    playlists_parser = subparsers.add_parser("playlists", help="List playlists")
    playlists_parser.add_argument("--name", help="Exact name filter")
    playlists_parser.add_argument("--prefix", help="Name prefix filter")
    playlists_parser.add_argument("--owner", help="Owner display name filter")
    playlists_parser.add_argument("--format", choices=["md", "json"], default="md")

    tracks_parser = subparsers.add_parser("tracks", help="List tracks in a playlist")
    tracks_parser.add_argument(
        "playlist_id", help="Playlist ID, or 'liked' for Liked Songs"
    )
    tracks_parser.add_argument("--format", choices=["md", "json"], default="md")

    return parser.parse_args(argv)


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
        group = p.group or "(unclassified)"
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


def _run_playlists(args: argparse.Namespace) -> str:
    sp = get_readonly_client()
    playlists = [get_liked_songs_info(sp), *list_playlist_infos(sp)]
    playlists = _filter_playlists(playlists, args.name, args.prefix, args.owner)
    playlists = _annotate_groups(playlists)
    if args.format == "json":
        return _to_json(playlists)
    return _format_playlists_markdown(playlists)


def _run_tracks(args: argparse.Namespace) -> str:
    sp = get_readonly_client()
    if args.playlist_id in ("liked", LIKED_SONGS_ID):
        tracks = list_liked_song_infos(sp)
    else:
        tracks = list_playlist_track_infos(sp, args.playlist_id)
    if args.format == "json":
        return _to_json(tracks)
    return _format_tracks_markdown(tracks)


def main() -> None:
    args = _parse_args()
    if args.command == "playlists":
        output = _run_playlists(args)
    else:
        output = _run_tracks(args)
    print(output)


if __name__ == "__main__":
    main()
