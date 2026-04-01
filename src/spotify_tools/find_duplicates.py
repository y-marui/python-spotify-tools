"""Detect duplicate tracks across playlists matching a given prefix."""
import sys
from collections import defaultdict
from dataclasses import dataclass

from spotify_tools.auth import get_client
from spotify_tools.playlist import Playlist, Track, list_playlists, list_tracks


@dataclass
class Occurrence:
    playlist: Playlist
    track: Track


def _find_duplicates(
    occurrences: list[Occurrence],
) -> tuple[dict[str, list[Occurrence]], dict[str, list[Occurrence]]]:
    """Return (exact_dupes, fuzzy_dupes) where values have 2+ occurrences."""
    by_uri: dict[str, list[Occurrence]] = defaultdict(list)
    by_key: dict[str, list[Occurrence]] = defaultdict(list)

    for occ in occurrences:
        by_uri[occ.track.uri].append(occ)
        key = f"{occ.track.name.lower()}|||{occ.track.artists.lower()}"
        by_key[key].append(occ)

    exact = {uri: occs for uri, occs in by_uri.items() if len(occs) >= 2}

    fuzzy: dict[str, list[Occurrence]] = {}
    for key, occs in by_key.items():
        uris = {o.track.uri for o in occs}
        if len(uris) >= 2:
            fuzzy[key] = occs

    return exact, fuzzy


def _print_group(label: str, groups: dict[str, list[Occurrence]]) -> None:
    if not groups:
        print(f"  {label}: none")
        return
    print(f"  {label}:")
    for occs in groups.values():
        t = occs[0].track
        print(f"    [{t.name} — {t.artists}]")
        for occ in occs:
            print(f"      {occ.playlist.name}  ({occ.track.uri})")


def main() -> None:
    if len(sys.argv) >= 2:
        prefix = sys.argv[1]
    else:
        prefix = input("Playlist prefix to search (Enter to search all): ").strip()

    sp = get_client()
    all_playlists = list_playlists(sp)

    if prefix:
        print(f"Fetching playlists starting with '{prefix}'…")
        targets = [p for p in all_playlists if p.name.startswith(prefix)]
        if not targets:
            print(f"No playlists found with prefix '{prefix}'.")
            sys.exit(0)
    else:
        confirm = input(
            f"Search all {len(all_playlists)} playlists? [y/N] "
        ).strip().lower()
        if confirm != "y":
            print("Cancelled.")
            sys.exit(0)
        targets = all_playlists
        print("Fetching all playlists…")

    print(f"Found {len(targets)} playlist(s): {', '.join(p.name for p in targets)}\n")

    occurrences: list[Occurrence] = []
    for playlist in targets:
        tracks = list_tracks(sp, playlist.id)
        for track in tracks:
            occurrences.append(Occurrence(playlist=playlist, track=track))

    exact, fuzzy = _find_duplicates(occurrences)

    print("=== Results ===")
    _print_group("Exact duplicates (same URI)", exact)
    print()
    _print_group("Fuzzy duplicates (same title+artist, different URI)", fuzzy)


if __name__ == "__main__":
    main()
