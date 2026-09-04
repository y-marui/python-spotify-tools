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

Place credentials at `~/.config/spotify-tools` (loaded automatically regardless of the current directory):

~~~sh
cp .env.example ~/.config/spotify-tools
# Edit ~/.config/spotify-tools and fill in your Client ID / Client Secret
~~~

A `.env` in the current directory is also accepted and takes precedence, which is useful for checkout-local development:

~~~sh
cp .env.example .env
# Edit .env and fill in your Client ID / Client Secret
~~~

**3. Install dependencies**

~~~sh
uv sync
~~~

**Install as commands via pipx (optional)**

To run `split-playlist` / `find-duplicates` as commands from anywhere, install with `pipx`:

~~~sh
pipx install .
~~~

Add `--editable` to keep it in sync while you edit the repo:

~~~sh
pipx install --editable .
~~~

## Configuration

| Variable | Description |
|---|---|
| `SPOTIFY_CLIENT_ID` | Spotify app Client ID |
| `SPOTIFY_CLIENT_SECRET` | Spotify app Client Secret |
| `SPOTIFY_REDIRECT_URI` | OAuth callback URI (default: `http://localhost:8888/callback`) |

## Usage

Every command supports `--version`/`-V` and `--help`/`-h`. Running `--install-completion` enables shell completion (zsh/bash/fish) for the shell you're currently using:

~~~sh
uv run spotify-inventory --install-completion
~~~

### split-playlist

~~~sh
uv run split-playlist
~~~

On first run, a browser window opens for OAuth authentication. The token is cached and auto-refreshed on subsequent runs. Caches are stored in `${XDG_CACHE_HOME:-~/.cache}/spotify-tools/` (`oauth` for read/write and `oauth-readonly` for read-only access), not in the working directory.

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

### spotify-playlist

A write command to create playlists and edit their metadata. `create` makes a new empty playlist; `update` changes an existing playlist's name, description, public/private state, or collaborative flag. The description text itself is expected to be managed in an external source of truth (e.g. Obsidian); this command doesn't depend on any specific file format or personal path.

~~~sh
# Create a new playlist (private by default)
uv run spotify-playlist create "My New Playlist" --description "A description"
uv run spotify-playlist create "Public Mix" --public

# Update an existing playlist (by ID, passing only the fields to change)
uv run spotify-playlist update <playlist-id> --name "New Name"
uv run spotify-playlist update <playlist-id> --description "Updated description" --private
~~~

- Both `create` and `update` show the planned change before writing and require confirmation (skip with `--yes`; without it, the default is to wait for confirmation and not change anything)
- `update` only targets playlists owned by the current user; playlists owned by someone else are refused
- `update` is refused if the target playlist is protected, unclassified, or ambiguous under the Playlist Groups guard (when enabled)
- `update` errors out and changes nothing if no field to update is given
- After writing, it re-fetches and displays the actual name/description/public/collaborative state so you can verify the write; it warns if the result doesn't match what was requested

### reorder-by-key

A write command that reorders a playlist in-place into Camelot Wheel (harmonic mixing) order, starting from the first track's key and walking the rest in adjacent-key priority.

Spotify's Web API has blocked new apps from the Audio Features endpoint (track key/tempo/etc.) since 2024-11-27, so this command doesn't fetch keys itself. As a stopgap, it takes Camelot keys from an external text file instead (e.g. read off the official Spotify app's Mix feature screen and typed in by hand).

~~~sh
# keys.txt: one Camelot key per line, matching the playlist's current
# order 1:1, e.g.:
#   10B
#   10A
#   9B
uv run reorder-by-key <playlist-id> keys.txt
~~~

- Clockwise vs. counterclockwise is chosen automatically by checking which direction packs the playlist's actual keys into a tighter arc from the starting key
- Within the same Camelot number, relative major/minor keys are treated as adjacent
- Shows the planned order and asks for confirmation before writing (skip with `--yes`)
- Refused if the target playlist is protected or unclassified under the required Playlist Groups guard

## Playlist Groups

Local config that stands in for playlist folder boundaries the official API doesn't expose. The Spotify Web API returns playlists as a flat list, with no folder information, so this repo lets you mirror your own client-side folder structure locally instead.

**Set up the config file:**

~~~sh
cp spotify-tools-groups.toml.example ~/.config/spotify-tools-groups.toml
# Edit ~/.config/spotify-tools-groups.toml with your own playlist classification
~~~

For checkout-local development, `./spotify-tools-groups.toml` is also accepted and takes precedence. This file holds a personal mapping and is never committed to the repo (`~/.config/` lives outside it).

**Example config:**

~~~toml
[[playlists]]
id = "37i9dQZF1DXcBWIGoYBM5M"
group = "protected"

[[playlists]]
name = "Family Shared"
group = "protected"

[[playlists]]
name = "Winter 2026 Cleanup"
group = "future_target"
note = "Split into seasonal playlists after New Year"
~~~

**Fail-safe behavior:**

- `spotify-inventory` works without this file and marks every playlist as unclassified, so it can be used to collect stable playlist IDs
- Every write command refuses to start unless a non-empty config file is available
- Playlists in the `protected` group are excluded from both source and target selection, and rejected again right before the move executes
- A playlist that matches neither `id` nor `name` (unclassified), or matches more than one differing group (ambiguous), is excluded and rejected the same way
- A playlist created on the fly during a split (as the new target) is exempt from the unclassified guard for *being unclassified*, but is still rejected if its name collides with a `protected` or ambiguous rule
- Liked Songs is subject to the guard too: add a rule with `name = "Liked Songs"` to your config if you want to keep selecting it as a move source

**Verification and known limits:**

- There's no automatic way to verify this local mapping still matches the actual folder structure in the Spotify client. Check the `Group` column from `uv run spotify-inventory playlists` by eye to confirm it matches what you intend
- This does not rely on any unofficial API, parsing of Spotify client internals, or browser automation

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
