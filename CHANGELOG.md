# Changelog

## [Unreleased]

### Added
- `reorder-by-key` command: reorders a playlist in-place into Camelot Wheel (harmonic-mixing) order from a manually supplied key file, auto-selecting clockwise/counterclockwise by which direction packs the playlist's actual keys more tightly. A stopgap until Spotify's Web API restores third-party access to track key data (Audio Features has been restricted for new apps since 2024-11-27).
- `split-playlist` can now use Liked Songs as a move source, in addition to regular playlists (#14).
- `spotify-inventory` command: read-only export of playlist and track listings as Markdown or JSON, using a read-only OAuth scope (#15).
- Local playlist group config (`spotify-tools-groups.toml`) to protect playlists from being used as a move source/target, standing in for playlist folders that the official API doesn't expose (#16).
- Pre-commit hooks `check-local-charter-version` and `check-markdown-heading-language` from the updated dev-charter.
- `CONTRIBUTING.md` (PR flow and review checklist).
- Further pre-commit hooks from the updated dev-charter (check-ai-context-reference, check-charter-subtree-edit, check-conventional-commit, check-dotenv-gitignore, check-language-pair-footer, check-language-pair-sync, check-license-exists, check-python-package-management, check-readme-placeholders).

### Changed
- Updated `docs/dev-charter/` subtree to the latest version.
- CI now runs the test job across a Python 3.11/3.12/3.13 matrix and uses `actions/checkout@v7` / `astral-sh/setup-uv@v8`.
- Synced `AI_CONTEXT.md` (AI tool assignment format, pre-commit hook table, code review requirement) with the updated charter.
- Removed `ai/context`, `ai/tasks`, and `ai/review` (not part of the dev-charter standard structure); folded their content into `docs/architecture.md`, `docs/development_rules.md`, and the new `CONTRIBUTING.md`. Also dropped the "`ai/context/` wins over `docs/` on conflict" rule, which allowed two sources of truth.

### Fixed
