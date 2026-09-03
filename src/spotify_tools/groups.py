"""Local playlist group/protection config.

Spotify's Web API returns playlists as a flat list with no folder
information, so client-side folder boundaries cannot be read from the API.
This module lets a user mirror those boundaries locally instead: a TOML
config maps playlist IDs/names to logical groups, and the `protected`
group is treated as off-limits for any move operation.

Write commands require a config file. Once it exists, any playlist that isn't
classified into exactly one non-protected group is treated as not modifiable,
since the mapping cannot be verified against Spotify's real folder structure.
"""

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

PROTECTED_GROUP = "protected"

GROUPS_FILENAME = "spotify-tools-groups.toml"


@dataclass
class PlaylistRule:
    group: str
    id: str | None = None
    name: str | None = None
    note: str | None = None


class GroupConfigError(Exception):
    """Raised when the group config file is malformed."""


class ProtectedPlaylistError(Exception):
    """Raised when an operation targets a protected or unclassified playlist."""


def default_groups_path() -> Path:
    """Return the XDG groups configuration path."""
    config_home = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return config_home / GROUPS_FILENAME


def resolve_groups_path() -> Path:
    """Prefer a checkout-local groups file over the XDG configuration file."""
    local = Path.cwd() / GROUPS_FILENAME
    return local if local.is_file() else default_groups_path()


def load_rules(path: Path | None = None) -> list[PlaylistRule]:
    """Load playlist group rules from a local TOML config.

    Returns an empty list if the selected file doesn't exist. Read-only
    commands use this to mark every playlist as unclassified.
    """
    path = path or resolve_groups_path()
    if not path.exists():
        return []
    with path.open("rb") as f:
        data = tomllib.load(f)
    return [_parse_rule(entry) for entry in data.get("playlists", [])]


def require_rules() -> list[PlaylistRule]:
    """Load non-empty rules required before a playlist write operation."""
    path = resolve_groups_path()
    if not path.is_file():
        raise SystemExit(
            "error: Playlist protection rules are missing. Create "
            f"{default_groups_path()} or {Path.cwd() / GROUPS_FILENAME} "
            "from spotify-tools-groups.toml.example before writing."
        )
    try:
        rules = load_rules(path)
    except (GroupConfigError, tomllib.TOMLDecodeError) as error:
        raise SystemExit(
            f"error: Invalid playlist protection rules: {error}"
        ) from error
    if not rules:
        raise SystemExit(
            f"error: {path} has no [[playlists]] rules; refusing to write."
        )
    return rules


def _parse_rule(entry: dict[str, object]) -> PlaylistRule:
    group = entry.get("group")
    playlist_id = entry.get("id")
    name = entry.get("name")
    if not group:
        raise GroupConfigError("Each [[playlists]] entry needs a 'group'.")
    if not playlist_id and not name:
        raise GroupConfigError("Each [[playlists]] entry needs 'id' or 'name'.")
    return PlaylistRule(
        group=str(group),
        id=str(playlist_id) if playlist_id else None,
        name=str(name) if name else None,
        note=str(entry["note"]) if entry.get("note") else None,
    )


def _matching_groups(
    playlist_id: str, playlist_name: str, rules: list[PlaylistRule]
) -> set[str]:
    return {
        r.group
        for r in rules
        if (r.id is not None and r.id == playlist_id)
        or (r.name is not None and r.name == playlist_name)
    }


def classify(
    playlist_id: str, playlist_name: str, rules: list[PlaylistRule]
) -> str | None:
    """Return the playlist's group name, or None if unclassified/ambiguous."""
    groups = _matching_groups(playlist_id, playlist_name, rules)
    return next(iter(groups)) if len(groups) == 1 else None


def is_modifiable(
    playlist_id: str, playlist_name: str, rules: list[PlaylistRule]
) -> bool:
    """Return whether a playlist may be used as a move source/target.

    Write commands call ``require_rules`` before this function. Once rules
    exist, only playlists classified into exactly one non-protected group
    qualify. The empty-list behavior remains for read-only callers.
    """
    if not rules:
        return True
    group = classify(playlist_id, playlist_name, rules)
    return group is not None and group != PROTECTED_GROUP


def require_modifiable(
    playlist_id: str, playlist_name: str, rules: list[PlaylistRule]
) -> None:
    """Raise ProtectedPlaylistError if the playlist must not be modified."""
    if not is_modifiable(playlist_id, playlist_name, rules):
        raise ProtectedPlaylistError(
            f"'{playlist_name}' is protected or unclassified; refusing to modify."
        )


def is_safe_new_target(
    playlist_id: str, playlist_name: str, rules: list[PlaylistRule]
) -> bool:
    """Return whether a playlist just created in this session may be used
    as a move target.

    Unlike is_modifiable, an unmatched id/name is allowed here — a
    brand-new playlist's id can't already be in the rules file, and it's
    fine if its name isn't there either. It's still rejected if its name
    happens to collide with a protected or ambiguous rule (e.g. the user
    named it after an existing protected playlist).
    """
    if not rules:
        return True
    groups = _matching_groups(playlist_id, playlist_name, rules)
    if PROTECTED_GROUP in groups:
        return False
    return len(groups) <= 1


def require_safe_new_target(
    playlist_id: str, playlist_name: str, rules: list[PlaylistRule]
) -> None:
    """Raise ProtectedPlaylistError if a newly created playlist collides
    with a protected or ambiguous group rule."""
    if not is_safe_new_target(playlist_id, playlist_name, rules):
        raise ProtectedPlaylistError(
            f"'{playlist_name}' collides with a protected/ambiguous group "
            "rule; refusing to use as a new target."
        )
