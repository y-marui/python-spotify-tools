"""Interactive CLI to split a Spotify playlist into smaller ones."""
import sys

import spotipy

from spotify_tools.auth import get_client
from spotify_tools.playlist import (
    Playlist,
    Track,
    add_tracks,
    create_playlist,
    list_playlists,
    list_tracks,
    remove_tracks,
)


def _pick_playlist(playlists: list[Playlist], prompt: str) -> Playlist:
    for i, p in enumerate(playlists, 1):
        print(f"  {i:3}. {p.name} ({p.track_count} tracks)")
    while True:
        raw = input(f"{prompt} (number): ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(playlists):
            return playlists[int(raw) - 1]
        print("  Invalid input. Try again.")


def _parse_selection(raw: str, max_index: int) -> list[int]:
    """Parse '1,3,5-8' style input into a list of 0-based indices."""
    indices: list[int] = []
    for part in raw.split(","):
        part = part.strip()
        if "-" in part:
            start, _, end = part.partition("-")
            if start.isdigit() and end.isdigit():
                indices.extend(range(int(start) - 1, int(end)))
        elif part.isdigit():
            indices.append(int(part) - 1)
    return [i for i in indices if 0 <= i < max_index]


def _show_tracks(tracks: list[Track]) -> None:
    for i, t in enumerate(tracks, 1):
        print(f"  {i:4}. {t.name} — {t.artists}")


def _select_target(sp: spotipy.Spotify, playlists: list[Playlist]) -> Playlist:
    print("\nTarget playlist:")
    print("   0. [Create new playlist]")
    for i, p in enumerate(playlists, 1):
        print(f"  {i:3}. {p.name}")
    while True:
        raw = input("Select (number): ").strip()
        if raw == "0":
            name = input("New playlist name: ").strip()
            if name:
                return create_playlist(sp, name)
        elif raw.isdigit() and 1 <= int(raw) <= len(playlists):
            return playlists[int(raw) - 1]
        print("  Invalid input. Try again.")


def main() -> None:
    sp = get_client()

    print("Fetching playlists…")
    playlists = list_playlists(sp)
    if not playlists:
        print("No playlists found.")
        sys.exit(0)

    print("\n=== Source playlist ===")
    source = _pick_playlist(playlists, "Select source playlist")

    print(f"\nFetching tracks from '{source.name}'…")
    tracks = list_tracks(sp, source.id)
    if not tracks:
        print("No tracks found.")
        sys.exit(0)

    print(f"\n{len(tracks)} tracks in '{source.name}':")
    _show_tracks(tracks)

    print("\nEnter track numbers to move (e.g. 1,3,5-8):")
    raw = input("> ").strip()
    indices = _parse_selection(raw, len(tracks))
    if not indices:
        print("No valid tracks selected. Exiting.")
        sys.exit(0)

    selected = [tracks[i] for i in indices]
    print(f"\n{len(selected)} track(s) selected:")
    for t in selected:
        print(f"  - {t.name} — {t.artists}")

    print("\n=== Target playlist ===")
    target = _select_target(sp, playlists)

    print(f"\nMove {len(selected)} track(s): '{source.name}' → '{target.name}'")
    confirm = input("Proceed? [y/N] ").strip().lower()
    if confirm != "y":
        print("Cancelled.")
        sys.exit(0)

    uris = [t.uri for t in selected]
    print("Adding tracks to target…")
    add_tracks(sp, target.id, uris)
    print("Removing tracks from source…")
    remove_tracks(sp, source.id, uris)
    print(f"Done. {len(selected)} track(s) moved to '{target.name}'.")


if __name__ == "__main__":
    main()
