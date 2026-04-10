"""Spotify OAuth authentication."""
import os
from pathlib import Path

import spotipy
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth

load_dotenv()

_config_env = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "spotify-tools"
load_dotenv(_config_env)

_SCOPES = " ".join([
    "playlist-read-private",
    "playlist-read-collaborative",
    "playlist-modify-public",
    "playlist-modify-private",
])


def get_client() -> spotipy.Spotify:
    """Return an authenticated Spotify client via OAuth."""
    return spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            client_id=os.environ["SPOTIFY_CLIENT_ID"],
            client_secret=os.environ["SPOTIFY_CLIENT_SECRET"],
            redirect_uri=os.environ["SPOTIFY_REDIRECT_URI"],
            scope=_SCOPES,
            cache_path=".spotify_cache",
            open_browser=True,
        )
    )
