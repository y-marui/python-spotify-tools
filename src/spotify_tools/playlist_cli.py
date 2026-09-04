"""CLI to create a new Spotify playlist or edit an existing playlist's metadata."""

import sys
from typing import Annotated

import spotipy
import typer

from spotify_tools import __version__
from spotify_tools.auth import get_client
from spotify_tools.groups import (
    PlaylistRule,
    require_modifiable,
    require_rules,
    require_safe_new_target,
)
from spotify_tools.playlist import (
    PlaylistDetails,
    create_playlist,
    get_playlist_details,
    require_owned_by_current_user,
    update_playlist_details,
)

# A not-yet-created playlist has no real ID, so pre-creation safety checks
# can only match group rules by name (no ID collides with this).
_NEW_PLAYLIST_ID_PLACEHOLDER = ""

app = typer.Typer(
    help="Create a new Spotify playlist or edit an existing one's metadata.",
    context_settings={"help_option_names": ["-h", "--help"]},
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"spotify-playlist {__version__}")
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


def _confirm(prompt: str, skip: bool) -> bool:
    if skip:
        return True
    return input(f"{prompt} [y/N] ").strip().lower() == "y"


def _verify_write(
    sp: spotipy.Spotify, playlist_id: str, expected: dict[str, str | bool]
) -> PlaylistDetails:
    """Re-fetch the playlist and abort with a warning if it drifted from what
    was requested — including fields nobody asked to change (e.g. Spotify
    forcing public=False as a side effect of turning on collaborative)."""
    after = get_playlist_details(sp, playlist_id)
    actual: dict[str, str | bool | None] = {
        "name": after.name,
        "description": after.description,
        "public": after.public,
        "collaborative": after.collaborative,
    }
    mismatches = {
        field: (expected_value, actual[field])
        for field, expected_value in expected.items()
        if actual[field] != expected_value
    }
    if mismatches:
        print("\nWARNING: final state doesn't match the requested change(s):")
        for field, (expected_value, actual_value) in mismatches.items():
            print(f"  {field}: expected {expected_value!r}, got {actual_value!r}")
        sys.exit(1)
    return after


def _run_create(
    sp: spotipy.Spotify,
    rules: list[PlaylistRule],
    *,
    name: str,
    description: str | None,
    public: bool,
    collaborative: bool,
    yes: bool,
) -> None:
    print("Create playlist:")
    print(f"  Name: {name}")
    print(f"  Description: {description or '(none)'}")
    print(f"  Public: {public}")
    print(f"  Collaborative: {collaborative}")

    require_safe_new_target(_NEW_PLAYLIST_ID_PLACEHOLDER, name, rules)

    if not _confirm("\nProceed?", yes):
        print("Cancelled.")
        sys.exit(0)

    playlist = create_playlist(
        sp,
        name,
        description=description,
        public=public,
        collaborative=collaborative,
    )

    expected: dict[str, str | bool] = {
        "name": name,
        "description": description or "",
        "public": public,
        "collaborative": collaborative,
    }
    after = _verify_write(sp, playlist.id, expected)
    print(f"\nCreated '{after.name}' ({after.id}).")
    print(f"  Description: {after.description or '(none)'}")
    print(f"  Public: {after.public}")
    print(f"  Collaborative: {after.collaborative}")


def _requested_changes(
    *,
    name: str | None,
    description: str | None,
    public: bool | None,
    collaborative: bool | None,
) -> dict[str, str | bool]:
    changes: dict[str, str | bool] = {}
    if name is not None:
        changes["name"] = name
    if description is not None:
        changes["description"] = description
    if public is not None:
        changes["public"] = public
    if collaborative is not None:
        changes["collaborative"] = collaborative
    return changes


def _show_update_diff(before: PlaylistDetails, changes: dict[str, str | bool]) -> None:
    print(f"Update playlist '{before.name}' ({before.id}):")
    current: dict[str, str | bool | None] = {
        "name": before.name,
        "description": before.description,
        "public": before.public,
        "collaborative": before.collaborative,
    }
    for field, new_value in changes.items():
        print(f"  {field}: {current[field]!r} -> {new_value!r}")


def _expected_after_update(
    before: PlaylistDetails, changes: dict[str, str | bool]
) -> dict[str, str | bool]:
    """Merge requested changes over the current state to get the full
    expected result, so _verify_write also catches drift in fields nobody
    asked to change."""
    return {
        "name": changes.get("name", before.name),
        "description": changes.get("description", before.description),
        "public": changes.get("public", bool(before.public)),
        "collaborative": changes.get("collaborative", before.collaborative),
    }


def _run_update(
    sp: spotipy.Spotify,
    rules: list[PlaylistRule],
    *,
    playlist_id: str,
    name: str | None,
    description: str | None,
    public: bool | None,
    collaborative: bool | None,
    yes: bool,
) -> None:
    changes = _requested_changes(
        name=name, description=description, public=public, collaborative=collaborative
    )
    if not changes:
        print(
            "No fields to update; specify at least one of --name/--description/"
            "--public/--private/--collaborative/--no-collaborative."
        )
        sys.exit(1)

    before = get_playlist_details(sp, playlist_id)
    current_user_id: str = sp.current_user()["id"]
    require_owned_by_current_user(before, current_user_id)
    require_modifiable(before.id, before.name, rules)

    _show_update_diff(before, changes)
    if not _confirm("\nProceed?", yes):
        print("Cancelled.")
        sys.exit(0)

    update_playlist_details(
        sp,
        playlist_id,
        name=name,
        description=description,
        public=public,
        collaborative=collaborative,
    )

    expected = _expected_after_update(before, changes)
    after = _verify_write(sp, playlist_id, expected)
    print(f"\nDone. '{after.name}' ({after.id}) updated.")
    print(f"  Description: {after.description or '(none)'}")
    print(f"  Public: {after.public}")
    print(f"  Collaborative: {after.collaborative}")


@app.command("create", help="Create a new playlist")
def create_command(
    name: Annotated[str, typer.Argument(help="Playlist name")],
    description: Annotated[
        str | None, typer.Option(help="Playlist description")
    ] = None,
    public: Annotated[
        bool,
        typer.Option(help="Make the playlist public (default: private)"),
    ] = False,
    collaborative: Annotated[
        bool, typer.Option(help="Make the playlist collaborative")
    ] = False,
    yes: Annotated[
        bool, typer.Option("--yes", help="Skip the confirmation prompt")
    ] = False,
) -> None:
    sp = get_client()
    rules = require_rules()
    _run_create(
        sp,
        rules,
        name=name,
        description=description,
        public=public,
        collaborative=collaborative,
        yes=yes,
    )


@app.command("update", help="Update an existing playlist's name/description/visibility")
def update_command(
    playlist_id: Annotated[str, typer.Argument(help="Playlist ID to update")],
    name: Annotated[str | None, typer.Option(help="New name")] = None,
    description: Annotated[str | None, typer.Option(help="New description")] = None,
    public: Annotated[
        bool | None,
        typer.Option(
            "--public/--private", help="Change visibility", show_default=False
        ),
    ] = None,
    collaborative: Annotated[
        bool | None,
        typer.Option(
            "--collaborative/--no-collaborative",
            help="Change the collaborative flag",
            show_default=False,
        ),
    ] = None,
    yes: Annotated[
        bool, typer.Option("--yes", help="Skip the confirmation prompt")
    ] = False,
) -> None:
    sp = get_client()
    rules = require_rules()
    _run_update(
        sp,
        rules,
        playlist_id=playlist_id,
        name=name,
        description=description,
        public=public,
        collaborative=collaborative,
        yes=yes,
    )


def main() -> None:
    app()


if __name__ == "__main__":
    main()
