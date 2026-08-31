"""Tests for OAuth credential and cache locations."""

from pathlib import Path

import pytest

from spotify_tools.auth import _cache_path, _credential_paths, _load_credentials


def test_cache_path_uses_xdg_cache_home(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XDG_CACHE_HOME", "/tmp/spotify-cache")

    assert _cache_path("oauth") == Path("/tmp/spotify-cache/spotify-tools/oauth")


def test_cache_path_defaults_to_home_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("XDG_CACHE_HOME", raising=False)
    monkeypatch.setattr(Path, "home", lambda: Path("/tmp/test-home"))

    assert _cache_path("oauth-readonly") == Path(
        "/tmp/test-home/.cache/spotify-tools/oauth-readonly"
    )


def test_credentials_accept_checkout_local_env(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    for name in ("SPOTIFY_CLIENT_ID", "SPOTIFY_CLIENT_SECRET", "SPOTIFY_REDIRECT_URI"):
        monkeypatch.delenv(name, raising=False)
    (tmp_path / ".env").write_text(
        "SPOTIFY_CLIENT_ID=test-id\n"
        "SPOTIFY_CLIENT_SECRET=test-secret\n"
        "SPOTIFY_REDIRECT_URI=http://127.0.0.1:8888/callback\n"
    )

    _load_credentials()

    assert _credential_paths()[0] == tmp_path / ".env"


def test_credentials_explain_how_to_configure_missing_values(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    for name in ("SPOTIFY_CLIENT_ID", "SPOTIFY_CLIENT_SECRET", "SPOTIFY_REDIRECT_URI"):
        monkeypatch.delenv(name, raising=False)

    with pytest.raises(SystemExit, match="Spotify credentials are missing"):
        _load_credentials()
