"""Spotify OAuth authentication and credential discovery."""
import os
from pathlib import Path

import spotipy
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth

_SCOPES = " ".join([
    "playlist-read-private",
    "playlist-read-collaborative",
    "playlist-modify-public",
    "playlist-modify-private",
    "user-library-read",
    "user-library-modify",
])

_READ_ONLY_SCOPES = " ".join([
    "playlist-read-private",
    "playlist-read-collaborative",
    "user-library-read",
])


def _credential_paths() -> tuple[Path, Path]:
    """Return the local and XDG credential files, in precedence order."""
    local = Path.cwd() / ".env"
    config_home = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return local, config_home / "spotify-tools"


def _load_credentials() -> None:
    """Load credentials and give an actionable error when they are absent."""
    local, config = _credential_paths()
    load_dotenv(local)
    load_dotenv(config)

    required = ("SPOTIFY_CLIENT_ID", "SPOTIFY_CLIENT_SECRET", "SPOTIFY_REDIRECT_URI")
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        raise SystemExit(
            "error: Spotify credentials are missing "
            f"({', '.join(missing)}). Create {config} from .env.example, "
            f"or create {local} for this checkout."
        )


def _cache_path(name: str) -> Path:
    cache_home = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    return cache_home / "spotify-tools" / name


def _build_client(scope: str, cache_name: str) -> spotipy.Spotify:
    _load_credentials()
    cache_path = _cache_path(cache_name)
    cache_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    return spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            client_id=os.environ["SPOTIFY_CLIENT_ID"],
            client_secret=os.environ["SPOTIFY_CLIENT_SECRET"],
            redirect_uri=os.environ["SPOTIFY_REDIRECT_URI"],
            scope=scope,
            cache_path=str(cache_path),
            open_browser=True,
        )
    )


def get_client() -> spotipy.Spotify:
    """Return an authenticated Spotify client via OAuth (read/write scope)."""
    return _build_client(_SCOPES, "oauth")


def get_readonly_client() -> spotipy.Spotify:
    """Return an authenticated Spotify client via OAuth (read-only scope)."""
    return _build_client(_READ_ONLY_SCOPES, "oauth-readonly")
