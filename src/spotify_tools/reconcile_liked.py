"""Remove Liked Songs already represented in a playlist, with verification.

Exact URI matches are removed automatically. Same-recording matches under a
different URI (same ISRC, e.g. a single vs. album release) are shown with
duration for review and removed only after explicit per-track confirmation.
The target playlist is never written to; the retained track is re-read from
the target immediately before any Liked Songs removal.
"""

import sys
from dataclasses import dataclass
from typing import Annotated

import spotipy
import typer

from spotify_tools import __version__
from spotify_tools.auth import get_client, get_readonly_client
from spotify_tools.groups import PlaylistRule, require_modifiable, require_rules
from spotify_tools.playlist import (
    Track,
    get_playlist_details,
    list_saved_tracks,
    list_tracks,
    remove_saved_tracks,
    require_owned_by_current_user,
)

# Alternate releases of one recording differ by a little; a larger gap hints
# at a different edit (radio edit, live version) that deserves a closer look.
_DURATION_WARN_MS = 3000
_REMOVE_BATCH = 50

app = typer.Typer(
    help=(
        "Preview (default) or apply removal of Liked Songs already present in "
        "a playlist."
    ),
    context_settings={"help_option_names": ["-h", "--help"]},
)


@dataclass
class Match:
    liked: Track
    retained: Track

    @property
    def is_exact(self) -> bool:
        return self.liked.uri == self.retained.uri

    @property
    def duration_gap_ms(self) -> int | None:
        if self.liked.duration_ms is None or self.retained.duration_ms is None:
            return None
        return abs(self.liked.duration_ms - self.retained.duration_ms)


def find_matches(liked: list[Track], target: list[Track]) -> list[Match]:
    """Match Liked tracks against target by URI, then by ISRC.

    Title/artist similarity is deliberately not used: remasters, live
    versions and other same-title performances are different recordings.
    """
    by_uri = {t.uri: t for t in target}
    by_isrc: dict[str, Track] = {}
    for t in target:
        if t.isrc:
            by_isrc.setdefault(t.isrc, t)

    matches: list[Match] = []
    for track in liked:
        if track.uri in by_uri:
            matches.append(Match(track, by_uri[track.uri]))
        elif track.isrc and track.isrc in by_isrc:
            matches.append(Match(track, by_isrc[track.isrc]))
    return matches


def verify_retained(
    sp: spotipy.Spotify, target_id: str, matches: list[Match]
) -> tuple[list[Match], list[Match]]:
    """Re-read the target and split matches into (still retained, missing)."""
    current = {t.uri for t in list_tracks(sp, target_id)}
    kept = [m for m in matches if m.retained.uri in current]
    missing = [m for m in matches if m.retained.uri not in current]
    return kept, missing


def _fmt_duration(ms: int | None) -> str:
    if ms is None:
        return "?:??"
    return f"{ms // 60000}:{ms // 1000 % 60:02}"


def _describe(m: Match) -> str:
    line = f"{m.liked.name} — {m.liked.artists} [{_fmt_duration(m.liked.duration_ms)}]"
    if m.is_exact:
        return line
    gap = m.duration_gap_ms
    warn = " DURATION DIFFERS" if gap is not None and gap > _DURATION_WARN_MS else ""
    return (
        f"{line}\n         ≈ retained: {m.retained.name} — {m.retained.artists} "
        f"[{_fmt_duration(m.retained.duration_ms)}] "
        f"(ISRC {m.liked.isrc}){warn}"
    )


def _print_preview(
    exact: list[Match], alternates: list[Match], liked_count: int
) -> None:
    print(f"\nLiked Songs scanned: {liked_count}")
    print(f"Exact URI matches (auto-removable): {len(exact)}")
    for i, m in enumerate(exact, 1):
        print(f"  {i:4}. {_describe(m)}")
    print(f"Same recording, different URI (needs confirmation): {len(alternates)}")
    for i, m in enumerate(alternates, 1):
        print(f"  {i:4}. {_describe(m)}")


def _confirm_alternates(alternates: list[Match]) -> list[Match]:
    accepted: list[Match] = []
    for m in alternates:
        print(f"\n{_describe(m)}")
        if (
            input("Treat as the same song and remove from Liked Songs? [y/N] ")
            .strip()
            .lower()
            == "y"
        ):
            accepted.append(m)
    return accepted


def _remove_in_batches(sp: spotipy.Spotify, matches: list[Match]) -> list[Match]:
    """Remove from Liked Songs; return the matches whose batch failed."""
    failed: list[Match] = []
    for i in range(0, len(matches), _REMOVE_BATCH):
        batch = matches[i : i + _REMOVE_BATCH]
        try:
            remove_saved_tracks(sp, [m.liked.uri for m in batch])
        except spotipy.SpotifyException as error:
            print(f"  ERROR removing a batch of {len(batch)}: {error}")
            failed.extend(batch)
    return failed


def _run_apply(
    sp: spotipy.Spotify,
    rules: list[PlaylistRule],
    target_id: str,
    exact: list[Match],
    alternates: list[Match],
    yes: bool,
) -> None:
    details = get_playlist_details(sp, target_id)
    require_owned_by_current_user(details, sp.current_user()["id"])
    require_modifiable(details.id, details.name, rules)

    chosen = list(exact)
    if exact and not yes:
        if (
            input(f"\nRemove {len(exact)} exact match(es)? [y/N] ").strip().lower()
            != "y"
        ):
            chosen = []
    chosen += _confirm_alternates(alternates)
    if not chosen:
        print("Nothing to remove.")
        return

    verified, missing = verify_retained(sp, target_id, chosen)
    for m in missing:
        print(f"  SKIPPED (retained track vanished from target): {_describe(m)}")
    if not verified:
        print("No removals are safe; aborting.")
        sys.exit(1)

    print(f"\nRemoving {len(verified)} track(s) from Liked Songs…")
    failed = _remove_in_batches(sp, verified)

    removed_uris = {m.liked.uri for m in verified}
    still_liked = {t.uri for t in list_saved_tracks(sp)} & removed_uris
    print(f"Done. Removed {len(removed_uris) - len(still_liked)} track(s).")
    if still_liked or failed or missing:
        print(
            f"Remaining in Liked Songs (requested but not removed): {len(still_liked)}"
        )
        print(f"Skipped due to missing retained track: {len(missing)}")
        sys.exit(1)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"reconcile-liked {__version__}")
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def _reconcile(
    target_id: Annotated[
        str,
        typer.Argument(help="ID of the playlist that should already hold the songs"),
    ],
    apply: Annotated[
        bool,
        typer.Option(
            "--apply", help="Remove matches from Liked Songs (default: preview only)"
        ),
    ] = False,
    yes: Annotated[
        bool,
        typer.Option(
            "--yes", help="Skip the prompt for exact matches (never for alternates)"
        ),
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
    sp = get_client() if apply else get_readonly_client()
    rules = require_rules() if apply else []

    print("Fetching Liked Songs and target playlist…")
    liked = list_saved_tracks(sp)
    target = list_tracks(sp, target_id)
    matches = find_matches(liked, target)
    exact = [m for m in matches if m.is_exact]
    alternates = [m for m in matches if not m.is_exact]

    _print_preview(exact, alternates, len(liked))
    if not apply:
        print("\nPreview only. Re-run with --apply to remove.")
        return
    _run_apply(sp, rules, target_id, exact, alternates, yes)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
