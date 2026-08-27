"""CLI to create a new Spotify playlist or edit an existing playlist's metadata."""
import argparse
import sys
from collections.abc import Sequence

import spotipy

from spotify_tools.auth import get_client
from spotify_tools.groups import (
    PlaylistRule,
    load_rules,
    require_modifiable,
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


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a new Spotify playlist or edit an existing one's metadata."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    create_parser = subparsers.add_parser("create", help="Create a new playlist")
    create_parser.add_argument("name", help="Playlist name")
    create_parser.add_argument(
        "--description", default=None, help="Playlist description"
    )
    create_parser.add_argument(
        "--public",
        action="store_true",
        help="Make the playlist public (default: private)",
    )
    create_parser.add_argument(
        "--collaborative", action="store_true", help="Make the playlist collaborative"
    )
    create_parser.add_argument(
        "--yes", action="store_true", help="Skip the confirmation prompt"
    )

    update_parser = subparsers.add_parser(
        "update", help="Update an existing playlist's name/description/visibility"
    )
    update_parser.add_argument("playlist_id", help="Playlist ID to update")
    update_parser.add_argument("--name", default=None, help="New name")
    update_parser.add_argument("--description", default=None, help="New description")
    visibility = update_parser.add_mutually_exclusive_group()
    visibility.add_argument(
        "--public", dest="public", action="store_true", default=None
    )
    visibility.add_argument(
        "--private", dest="public", action="store_false", default=None
    )
    collaborative = update_parser.add_mutually_exclusive_group()
    collaborative.add_argument(
        "--collaborative", dest="collaborative", action="store_true", default=None
    )
    collaborative.add_argument(
        "--no-collaborative", dest="collaborative", action="store_false", default=None
    )
    update_parser.add_argument(
        "--yes", action="store_true", help="Skip the confirmation prompt"
    )

    return parser.parse_args(argv)


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
    args: argparse.Namespace, sp: spotipy.Spotify, rules: list[PlaylistRule]
) -> None:
    print("Create playlist:")
    print(f"  Name: {args.name}")
    print(f"  Description: {args.description or '(none)'}")
    print(f"  Public: {args.public}")
    print(f"  Collaborative: {args.collaborative}")

    require_safe_new_target(_NEW_PLAYLIST_ID_PLACEHOLDER, args.name, rules)

    if not _confirm("\nProceed?", args.yes):
        print("Cancelled.")
        sys.exit(0)

    playlist = create_playlist(
        sp,
        args.name,
        description=args.description,
        public=args.public,
        collaborative=args.collaborative,
    )

    expected: dict[str, str | bool] = {
        "name": args.name,
        "description": args.description or "",
        "public": args.public,
        "collaborative": args.collaborative,
    }
    after = _verify_write(sp, playlist.id, expected)
    print(f"\nCreated '{after.name}' ({after.id}).")
    print(f"  Description: {after.description or '(none)'}")
    print(f"  Public: {after.public}")
    print(f"  Collaborative: {after.collaborative}")


def _requested_changes(args: argparse.Namespace) -> dict[str, str | bool]:
    changes: dict[str, str | bool] = {}
    if args.name is not None:
        changes["name"] = args.name
    if args.description is not None:
        changes["description"] = args.description
    if args.public is not None:
        changes["public"] = args.public
    if args.collaborative is not None:
        changes["collaborative"] = args.collaborative
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
    args: argparse.Namespace, sp: spotipy.Spotify, rules: list[PlaylistRule]
) -> None:
    changes = _requested_changes(args)
    if not changes:
        print(
            "No fields to update; specify at least one of --name/--description/"
            "--public/--private/--collaborative/--no-collaborative."
        )
        sys.exit(1)

    before = get_playlist_details(sp, args.playlist_id)
    current_user_id: str = sp.current_user()["id"]
    require_owned_by_current_user(before, current_user_id)
    require_modifiable(before.id, before.name, rules)

    _show_update_diff(before, changes)
    if not _confirm("\nProceed?", args.yes):
        print("Cancelled.")
        sys.exit(0)

    update_playlist_details(
        sp,
        args.playlist_id,
        name=args.name,
        description=args.description,
        public=args.public,
        collaborative=args.collaborative,
    )

    expected = _expected_after_update(before, changes)
    after = _verify_write(sp, args.playlist_id, expected)
    print(f"\nDone. '{after.name}' ({after.id}) updated.")
    print(f"  Description: {after.description or '(none)'}")
    print(f"  Public: {after.public}")
    print(f"  Collaborative: {after.collaborative}")


def main(argv: Sequence[str] | None = None) -> None:
    args = _parse_args(argv)
    sp = get_client()
    rules = load_rules()
    if args.command == "create":
        _run_create(args, sp, rules)
    else:
        _run_update(args, sp, rules)


if __name__ == "__main__":
    main()
