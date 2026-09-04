"""Cross-cutting CLI usability checks: --version/-V and --help/-h must work
consistently across every typer-based entry point (charter requirement)."""

import pytest
from typer.testing import CliRunner

from spotify_tools import __version__
from spotify_tools.find_duplicates import app as find_duplicates_app
from spotify_tools.inventory_cli import app as inventory_app
from spotify_tools.playlist_cli import app as playlist_app
from spotify_tools.reorder_by_key_cli import app as reorder_app
from spotify_tools.split_playlist import app as split_playlist_app

runner = CliRunner()

_APPS = [
    ("spotify-inventory", inventory_app),
    ("spotify-playlist", playlist_app),
    ("reorder-by-key", reorder_app),
    ("split-playlist", split_playlist_app),
    ("find-duplicates", find_duplicates_app),
]


@pytest.mark.parametrize("prog_name,app", _APPS, ids=[p for p, _ in _APPS])
def test_version_flag_prints_version_and_exits_cleanly(
    prog_name: str, app: object
) -> None:
    for flag in ("--version", "-V"):
        result = runner.invoke(app, [flag])  # type: ignore[arg-type]
        assert result.exit_code == 0, result.output
        assert result.output.strip() == f"{prog_name} {__version__}"


@pytest.mark.parametrize("prog_name,app", _APPS, ids=[p for p, _ in _APPS])
def test_help_flag_exits_cleanly(prog_name: str, app: object) -> None:
    for flag in ("--help", "-h"):
        result = runner.invoke(app, [flag])  # type: ignore[arg-type]
        assert result.exit_code == 0, result.output
