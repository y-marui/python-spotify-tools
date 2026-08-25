"""Tests for local playlist group/protection config."""
from pathlib import Path

import pytest

from spotify_tools.groups import (
    GroupConfigError,
    PlaylistRule,
    ProtectedPlaylistError,
    classify,
    is_modifiable,
    load_rules,
    require_modifiable,
)


def test_load_rules_returns_empty_list_when_file_missing(tmp_path: Path) -> None:
    assert load_rules(tmp_path / "missing.toml") == []


def test_load_rules_parses_entries(tmp_path: Path) -> None:
    config = tmp_path / "groups.toml"
    config.write_text(
        """
        [[playlists]]
        id = "abc123"
        group = "protected"

        [[playlists]]
        name = "Winter Cleanup"
        group = "future_target"
        note = "split after New Year"
        """
    )

    rules = load_rules(config)

    assert rules == [
        PlaylistRule(group="protected", id="abc123", name=None, note=None),
        PlaylistRule(
            group="future_target",
            id=None,
            name="Winter Cleanup",
            note="split after New Year",
        ),
    ]


def test_load_rules_rejects_entry_without_group(tmp_path: Path) -> None:
    config = tmp_path / "groups.toml"
    config.write_text('[[playlists]]\nid = "abc123"\n')

    with pytest.raises(GroupConfigError):
        load_rules(config)


def test_load_rules_rejects_entry_without_id_or_name(tmp_path: Path) -> None:
    config = tmp_path / "groups.toml"
    config.write_text('[[playlists]]\ngroup = "protected"\n')

    with pytest.raises(GroupConfigError):
        load_rules(config)


def test_classify_returns_none_when_unclassified() -> None:
    assert classify("id-1", "Name", []) is None


def test_classify_returns_group_for_single_match() -> None:
    rules = [PlaylistRule(group="active", id="id-1")]
    assert classify("id-1", "Name", rules) == "active"


def test_classify_returns_none_when_ambiguous() -> None:
    rules = [
        PlaylistRule(group="protected", id="id-1"),
        PlaylistRule(group="active", name="Name"),
    ]
    assert classify("id-1", "Name", rules) is None


def test_is_modifiable_ignores_guard_when_no_rules_configured() -> None:
    assert is_modifiable("id-1", "Anything", []) is True


def test_is_modifiable_rejects_protected_playlist() -> None:
    rules = [PlaylistRule(group="protected", id="id-1")]
    assert is_modifiable("id-1", "Family Shared", rules) is False


def test_is_modifiable_rejects_unclassified_playlist_when_rules_active() -> None:
    rules = [PlaylistRule(group="protected", id="other-id")]
    assert is_modifiable("id-1", "Unknown Playlist", rules) is False


def test_is_modifiable_allows_non_protected_classified_playlist() -> None:
    rules = [PlaylistRule(group="future_target", id="id-1")]
    assert is_modifiable("id-1", "Winter Cleanup", rules) is True


def test_require_modifiable_raises_for_protected_playlist() -> None:
    rules = [PlaylistRule(group="protected", id="id-1")]
    with pytest.raises(ProtectedPlaylistError):
        require_modifiable("id-1", "Family Shared", rules)


def test_require_modifiable_passes_silently_when_allowed() -> None:
    rules = [PlaylistRule(group="active", id="id-1")]
    require_modifiable("id-1", "Anything", rules)
