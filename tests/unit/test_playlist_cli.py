"""Tests for the create/update playlist CLI: confirmation flow, and the
ownership and playlist-group protection guards applied to updates."""

from typing import Any

import pytest
from typer.testing import CliRunner

from spotify_tools.groups import PlaylistRule, ProtectedPlaylistError
from spotify_tools.playlist import NotPlaylistOwnerError
from spotify_tools.playlist_cli import _run_create, _run_update, app

runner = CliRunner()


class FakeSpotify:
    """Minimal fake of the spotipy client for playlist create/update endpoints."""

    def __init__(self, playlist: dict[str, Any], user_id: str = "me") -> None:
        self._playlist = dict(playlist)
        self._user_id = user_id
        self.created: dict[str, Any] | None = None
        self.changed: dict[str, Any] | None = None

    def current_user(self) -> dict[str, Any]:
        return {"id": self._user_id}

    def current_user_playlist_create(
        self,
        name: str,
        public: bool = True,
        collaborative: bool = False,
        description: str = "",
    ) -> dict[str, Any]:
        self.created = {
            "name": name,
            "public": public,
            "collaborative": collaborative,
            "description": description,
        }
        self._playlist = {
            "id": "new-id",
            "name": name,
            "description": description,
            "public": public,
            "collaborative": collaborative,
            "owner": {"id": self._user_id},
        }
        return {"id": "new-id", "name": name}

    def playlist(self, playlist_id: str, fields: str | None = None) -> dict[str, Any]:
        return self._playlist

    def playlist_change_details(self, playlist_id: str, **kwargs: Any) -> None:
        self.changed = kwargs
        for key, value in kwargs.items():
            if value is not None:
                self._playlist[key] = value


def _playlist(
    playlist_id: str = "abc",
    name: str = "My Playlist",
    owner_id: str = "me",
    description: str = "old desc",
    public: bool = False,
    collaborative: bool = False,
) -> dict[str, Any]:
    return {
        "id": playlist_id,
        "name": name,
        "description": description,
        "public": public,
        "collaborative": collaborative,
        "owner": {"id": owner_id},
    }


def _create(
    sp: Any,
    rules: list[PlaylistRule],
    *,
    name: str = "New Playlist",
    description: str | None = None,
    public: bool = False,
    collaborative: bool = False,
    yes: bool = False,
) -> None:
    _run_create(
        sp,
        rules,
        name=name,
        description=description,
        public=public,
        collaborative=collaborative,
        yes=yes,
    )


def _update(
    sp: Any,
    rules: list[PlaylistRule],
    *,
    playlist_id: str = "abc",
    name: str | None = None,
    description: str | None = None,
    public: bool | None = None,
    collaborative: bool | None = None,
    yes: bool = False,
) -> None:
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


# --- create ---


def test_run_create_creates_playlist_after_confirmation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("builtins.input", lambda _: "y")
    sp = FakeSpotify(_playlist())

    _create(sp, [], description="desc")  # type: ignore[arg-type]

    assert sp.created == {
        "name": "New Playlist",
        "public": False,
        "collaborative": False,
        "description": "desc",
    }


def test_run_create_cancelled_when_not_confirmed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("builtins.input", lambda _: "n")
    sp = FakeSpotify(_playlist())

    with pytest.raises(SystemExit) as exc_info:
        _create(sp, [])  # type: ignore[arg-type]

    assert exc_info.value.code == 0
    assert sp.created is None


def test_run_create_rejects_name_colliding_with_protected_rule(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("builtins.input", lambda _: "y")
    sp = FakeSpotify(_playlist())
    rules = [PlaylistRule(group="protected", name="New Playlist")]

    with pytest.raises(ProtectedPlaylistError):
        _create(sp, rules)  # type: ignore[arg-type]

    assert sp.created is None


def test_run_create_rejects_protected_name_before_prompting(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The Playlist Groups guard must run before the confirmation prompt,
    not after — otherwise a rejected name still shows the user a "Proceed?"
    prompt they can say yes to before hitting the (uncaught) error."""

    def _fail_if_called(_: str) -> str:
        raise AssertionError("must not prompt when the safety guard rejects")

    monkeypatch.setattr("builtins.input", _fail_if_called)
    sp = FakeSpotify(_playlist())
    rules = [PlaylistRule(group="protected", name="New Playlist")]

    with pytest.raises(ProtectedPlaylistError):
        _create(sp, rules)  # type: ignore[arg-type]

    assert sp.created is None


def test_run_create_warns_when_final_state_does_not_match(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("builtins.input", lambda _: "y")

    class StaleCreateSpotify(FakeSpotify):
        def current_user_playlist_create(
            self,
            name: str,
            public: bool = True,
            collaborative: bool = False,
            description: str = "",
        ) -> dict[str, Any]:
            self.created = {
                "name": name,
                "public": public,
                "collaborative": collaborative,
                "description": description,
            }
            # Simulate the API not honoring the requested public flag.
            self._playlist = {
                "id": "new-id",
                "name": name,
                "description": description,
                "public": False,
                "collaborative": collaborative,
                "owner": {"id": self._user_id},
            }
            return {"id": "new-id", "name": name}

    sp = StaleCreateSpotify(_playlist())

    with pytest.raises(SystemExit) as exc_info:
        _create(sp, [], public=True)  # type: ignore[arg-type]

    assert exc_info.value.code == 1


# --- update ---


def test_run_update_updates_after_confirmation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("builtins.input", lambda _: "y")
    sp = FakeSpotify(_playlist())

    _update(sp, [], name="New Name")  # type: ignore[arg-type]

    assert sp.changed is not None
    assert sp.changed["name"] == "New Name"


def test_run_update_cancelled_when_not_confirmed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("builtins.input", lambda _: "n")
    sp = FakeSpotify(_playlist())

    with pytest.raises(SystemExit) as exc_info:
        _update(sp, [], name="New Name")  # type: ignore[arg-type]

    assert exc_info.value.code == 0
    assert sp.changed is None


def test_run_update_requires_at_least_one_field() -> None:
    sp = FakeSpotify(_playlist())

    with pytest.raises(SystemExit) as exc_info:
        _update(sp, [])  # type: ignore[arg-type]

    assert exc_info.value.code == 1
    assert sp.changed is None


def test_run_update_rejects_non_owner(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("builtins.input", lambda _: "y")
    sp = FakeSpotify(_playlist(owner_id="someone-else"))

    with pytest.raises(NotPlaylistOwnerError):
        _update(sp, [], name="New Name")  # type: ignore[arg-type]

    assert sp.changed is None


def test_run_update_rejects_protected_playlist(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("builtins.input", lambda _: "y")
    sp = FakeSpotify(_playlist(playlist_id="abc", name="My Playlist"))
    rules = [PlaylistRule(group="protected", id="abc")]

    with pytest.raises(ProtectedPlaylistError):
        _update(sp, rules, name="New Name")  # type: ignore[arg-type]

    assert sp.changed is None


def test_run_update_rejects_unclassified_playlist(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("builtins.input", lambda _: "y")
    sp = FakeSpotify(_playlist(playlist_id="abc", name="My Playlist"))
    rules = [PlaylistRule(group="active", id="other-id")]

    with pytest.raises(ProtectedPlaylistError):
        _update(sp, rules, name="New Name")  # type: ignore[arg-type]

    assert sp.changed is None


def test_run_update_rejects_ambiguous_playlist(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Two rules match the same playlist via id and name into different
    groups, so classification is ambiguous and must be refused just like
    protected/unclassified."""
    monkeypatch.setattr("builtins.input", lambda _: "y")
    sp = FakeSpotify(_playlist(playlist_id="abc", name="My Playlist"))
    rules = [
        PlaylistRule(group="active", id="abc"),
        PlaylistRule(group="future_target", name="My Playlist"),
    ]

    with pytest.raises(ProtectedPlaylistError):
        _update(sp, rules, name="New Name")  # type: ignore[arg-type]

    assert sp.changed is None


def test_run_update_warns_when_final_state_does_not_match(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("builtins.input", lambda _: "y")

    class StaleSpotify(FakeSpotify):
        def playlist_change_details(self, playlist_id: str, **kwargs: Any) -> None:
            self.changed = kwargs
            # Simulate the API silently not applying the change.

    sp = StaleSpotify(_playlist())

    with pytest.raises(SystemExit) as exc_info:
        _update(sp, [], name="New Name")  # type: ignore[arg-type]

    assert exc_info.value.code == 1


def test_run_update_warns_on_unrequested_field_side_effect(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Spotify can change a field nobody asked to touch as a side effect of
    another field (e.g. forcing public=False when collaborative is turned
    on). The verification step must catch this even though only
    "collaborative" was in the requested changes."""
    monkeypatch.setattr("builtins.input", lambda _: "y")

    class SideEffectSpotify(FakeSpotify):
        def playlist_change_details(self, playlist_id: str, **kwargs: Any) -> None:
            self.changed = kwargs
            self._playlist["collaborative"] = True
            self._playlist["public"] = False  # unrequested side effect

    sp = SideEffectSpotify(_playlist(public=True))

    with pytest.raises(SystemExit) as exc_info:
        _update(sp, [], collaborative=True)  # type: ignore[arg-type]

    assert exc_info.value.code == 1


# --- CLI wiring (typer option/argument parsing end-to-end) ---


def test_create_command_wires_options_through_to_run_create(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("builtins.input", lambda _: "y")
    sp = FakeSpotify(_playlist())
    monkeypatch.setattr("spotify_tools.playlist_cli.get_client", lambda: sp)
    monkeypatch.setattr("spotify_tools.playlist_cli.require_rules", lambda: [])

    result = runner.invoke(
        app,
        ["create", "New Playlist", "--description", "desc", "--public", "--yes"],
    )

    assert result.exit_code == 0, result.output
    assert sp.created == {
        "name": "New Playlist",
        "public": True,
        "collaborative": False,
        "description": "desc",
    }


def test_update_command_wires_tri_state_flags_through_to_run_update(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sp = FakeSpotify(_playlist())
    monkeypatch.setattr("spotify_tools.playlist_cli.get_client", lambda: sp)
    monkeypatch.setattr("spotify_tools.playlist_cli.require_rules", lambda: [])

    result = runner.invoke(
        app, ["update", "abc", "--private", "--no-collaborative", "--yes"]
    )

    assert result.exit_code == 0, result.output
    assert sp.changed == {
        "name": None,
        "description": None,
        "public": False,
        "collaborative": False,
    }


def test_update_command_leaves_untouched_flags_as_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Neither --public/--private nor --collaborative/--no-collaborative is
    passed, so both must reach _run_update as None (no change requested),
    not default to False."""
    sp = FakeSpotify(_playlist())
    monkeypatch.setattr("spotify_tools.playlist_cli.get_client", lambda: sp)
    monkeypatch.setattr("spotify_tools.playlist_cli.require_rules", lambda: [])

    result = runner.invoke(app, ["update", "abc", "--name", "New Name", "--yes"])

    assert result.exit_code == 0, result.output
    assert sp.changed == {
        "name": "New Name",
        "description": None,
        "public": None,
        "collaborative": None,
    }
