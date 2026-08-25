# Changelog

## [Unreleased]

### Added
- `split-playlist` can now use Liked Songs as a move source, in addition to regular playlists (#14).
- `spotify-inventory` command: read-only export of playlist and track listings as Markdown or JSON, using a read-only OAuth scope (#15).
- Local playlist group config (`spotify-tools-groups.toml`) to protect playlists from being used as a move source/target, standing in for playlist folders that the official API doesn't expose (#16).
- Pre-commit hooks `check-local-charter-version` and `check-markdown-heading-language` from the updated dev-charter.

### Changed
- Updated `docs/dev-charter/` subtree to the latest version.
- CI now runs the test job across a Python 3.11/3.12/3.13 matrix and uses `actions/checkout@v7` / `astral-sh/setup-uv@v8`.
- Synced `AI_CONTEXT.md` (AI tool assignment format, pre-commit hook table, code review requirement) with the updated charter.

### Fixed
