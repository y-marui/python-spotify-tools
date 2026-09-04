"""Spotify playlist management tools."""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _version

try:
    __version__ = _version("spotify-tools")
except PackageNotFoundError:
    # Not installed (e.g. run from a source checkout without `uv sync`/`pip install`).
    __version__ = "0.0.0+unknown"
