# python-spotify-tools

> **このファイルは正本（日本語版）です。**
> 英語版（参照）は [README.md](README.md) を参照してください。

[![CI](https://github.com/y-marui/python-spotify-tools/actions/workflows/ci.yml/badge.svg)](https://github.com/y-marui/python-spotify-tools/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

大きくなりすぎた Spotify プレイリストを利用シーン別に分割し、新しいプレイリストへ移すための個人用スクリプト。

## Setup

**1. Spotify アプリを作成**

[Spotify Developer Dashboard](https://developer.spotify.com/dashboard) でアプリを作成し、Redirect URI に `http://localhost:8888/callback` を追加する。

**2. 環境変数を設定**

~~~sh
cp .env.example .env
# .env を編集して Client ID / Client Secret を入力
~~~

**3. 依存関係をインストール**

~~~sh
uv sync
~~~

## Configuration

| 変数 | 説明 |
|---|---|
| `SPOTIFY_CLIENT_ID` | Spotify アプリの Client ID |
| `SPOTIFY_CLIENT_SECRET` | Spotify アプリの Client Secret |
| `SPOTIFY_REDIRECT_URI` | OAuth コールバック URI（デフォルト: `http://localhost:8888/callback`） |

## Usage

~~~sh
uv run split-playlist
~~~

初回実行時にブラウザが開き OAuth 認証が走る。認証後はトークンがキャッシュされ、次回以降は自動更新される。

**操作フロー:**

1. ソースプレイリストを番号で選択
2. 曲一覧を確認し、移動したい曲番号を入力（例: `1,3,5-8`）
3. 移動先プレイリストを選択（新規作成も可）
4. 確認後に実行

## Commands

| コマンド | 内容 |
|---|---|
| `make install` | 依存関係インストール（`uv sync`） |
| `make lint` | linting（`ruff check .`） |
| `make type` | 型チェック（`mypy src`） |
| `make test` | テスト実行（`pytest`） |
| `make all` | lint + type + test |

## License

MIT License — [LICENSE](LICENSE) を参照

---
*この文書には英語版 [README.md](README.md) があります。編集時は同一コミットで更新してください。*
