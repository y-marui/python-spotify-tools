"""CLI to reorder a playlist in-place into Camelot Wheel (harmonic mixing) order.

Spotify's Web API no longer exposes track key/tempo data to new
applications (the Audio Features endpoint has been restricted since
2024-11-27), so this command takes Camelot keys as an external input file
rather than fetching them itself.
"""

import sys
from pathlib import Path
from typing import Annotated

import typer

from spotify_tools import __version__
from spotify_tools.auth import get_client
from spotify_tools.camelot import (
    CamelotKey,
    choose_direction,
    parse_camelot,
    sort_order,
)
from spotify_tools.groups import require_modifiable, require_rules
from spotify_tools.playlist import Track, get_playlist_name, list_tracks
from spotify_tools.reorder import apply_moves, compute_moves

app = typer.Typer(
    help=(
        "Reorder a playlist in-place into Camelot Wheel (harmonic mixing) "
        "order, starting from its first track's key."
    ),
    context_settings={"help_option_names": ["-h", "--help"]},
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"reorder-by-key {__version__}")
        raise typer.Exit()


def _read_keys(path: Path, track_count: int) -> list[CamelotKey]:
    lines = [line.strip() for line in path.read_text().splitlines() if line.strip()]
    if len(lines) != track_count:
        raise ValueError(
            f"{path} has {len(lines)} key(s) but the playlist has "
            f"{track_count} track(s); they must match 1:1 in order."
        )
    return [parse_camelot(line) for line in lines]


def _show_plan(tracks: list[Track], keys: list[CamelotKey], order: list[int]) -> None:
    print("New order:")
    for pos, i in enumerate(order, 1):
        print(f"  {pos:3}. [{keys[i]}] {tracks[i].name} — {tracks[i].artists}")


@app.callback(invoke_without_command=True)
def _reorder(
    playlist_id: Annotated[str, typer.Argument(help="Playlist ID to reorder")],
    keys_file: Annotated[
        Path,
        typer.Argument(
            help=(
                "Text file with one Camelot key per line (e.g. '10B'), in the "
                "same order as the playlist's current tracks"
            )
        ),
    ],
    yes: Annotated[
        bool, typer.Option("--yes", help="Skip the confirmation prompt")
    ] = False,
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
    sp = get_client()

    tracks = list_tracks(sp, playlist_id)
    if not tracks:
        print("No tracks found.")
        sys.exit(0)

    keys = _read_keys(keys_file, len(tracks))
    direction = choose_direction(keys[0], keys)
    order = sort_order(keys[0], keys, direction)

    print(f"Direction: {direction} (auto-selected from key distribution)")
    _show_plan(tracks, keys, order)

    if not yes:
        confirm = input("\nApply this order to the playlist? [y/N] ").strip().lower()
        if confirm != "y":
            print("Cancelled.")
            sys.exit(0)

    rules = require_rules()
    playlist_name = get_playlist_name(sp, playlist_id)
    require_modifiable(playlist_id, playlist_name, rules)

    current_uris = [t.uri for t in tracks]
    target_uris = [tracks[i].uri for i in order]
    moves = compute_moves(current_uris, target_uris)
    apply_moves(sp, playlist_id, moves)

    final = list_tracks(sp, playlist_id)
    if [t.uri for t in final] == target_uris:
        print(f"\nDone. {len(moves)} move(s) applied.")
    else:
        print("\nWARNING: final order doesn't match the plan. Please verify manually.")
        sys.exit(1)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
