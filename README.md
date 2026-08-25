# python-spotify-tools

> **This is the reference (English) version.**
> The canonical (Japanese) version is [README-jp.md](README-jp.md).

[![CI](https://github.com/y-marui/python-spotify-tools/actions/workflows/ci.yml/badge.svg)](https://github.com/y-marui/python-spotify-tools/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Personal scripts to split an oversized Spotify playlist into new playlists organized by use case.

## Setup

**1. Create a Spotify app**

Create an app in the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard) and add `http://localhost:8888/callback` as a Redirect URI.

**2. Configure credentials**

If installed via `pipx`, place the credentials file at `~/.config/spotify-tools` (loaded automatically regardless of the current directory):

~~~sh
cp .env.example ~/.config/spotify-tools
# Edit ~/.config/spotify-tools and fill in your Client ID / Client Secret
~~~

If running directly with `uv`, a `.env` in the current directory also works:

~~~sh
cp .env.example .env
# Edit .env and fill in your Client ID / Client Secret
~~~

**3. Install dependencies**

~~~sh
uv sync
~~~

## Configuration

| Variable | Description |
|---|---|
| `SPOTIFY_CLIENT_ID` | Spotify app Client ID |
| `SPOTIFY_CLIENT_SECRET` | Spotify app Client Secret |
| `SPOTIFY_REDIRECT_URI` | OAuth callback URI (default: `http://localhost:8888/callback`) |

## Usage

### split-playlist

~~~sh
uv run split-playlist
~~~

On first run, a browser window opens for OAuth authentication. The token is cached and auto-refreshed on subsequent runs.

**Workflow:**

1. Select the source playlist by number (Liked Songs can be selected too)
2. Review the track list and enter track numbers to move (e.g. `1,3,5-8`)
3. Select or create a target playlist
4. Confirm to execute

### spotify-inventory

A read-only command that never modifies data on Spotify. Exports playlist and track listings as Markdown or JSON, and requests only read-only OAuth scopes.

~~~sh
# List playlists (includes Liked Songs)
uv run spotify-inventory playlists
uv run spotify-inventory playlists --prefix "Work" --format json

# List tracks in a playlist (use "liked" as playlist_id for Liked Songs)
uv run spotify-inventory tracks <playlist-id>
uv run spotify-inventory tracks liked --format json
~~~

## Commands

| Command | Description |
|---|---|
| `make install` | Install dependencies (`uv sync`) |
| `make lint` | Linting (`ruff check .`) |
| `make type` | Type checking (`mypy src`) |
| `make test` | Run tests (`pytest`) |
| `make all` | lint + type + test |

## License

MIT License — see [LICENSE](LICENSE)

---
*This document has a Japanese canonical version [README-jp.md](README-jp.md). Update both in the same commit when editing.*
