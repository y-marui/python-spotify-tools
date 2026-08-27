# python-spotify-tools

> **このファイルは正本（日本語版）です。**
> 英語版（参照）は [README.md](README.md) を参照してください。

[![CI](https://github.com/y-marui/python-spotify-tools/actions/workflows/ci.yml/badge.svg)](https://github.com/y-marui/python-spotify-tools/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

大きくなりすぎた Spotify プレイリストを利用シーン別に分割し、新しいプレイリストへ移すための個人用スクリプト。

## Setup

**1. Spotify アプリを作成**

[Spotify Developer Dashboard](https://developer.spotify.com/dashboard) でアプリを作成し、Redirect URI に `http://localhost:8888/callback` を追加する。

**2. 認証情報を設定**

`pipx` でインストールした場合は `~/.config/spotify-tools` に配置する（一度置けばどのディレクトリから実行しても読み込まれる）:

~~~sh
cp .env.example ~/.config/spotify-tools
# ~/.config/spotify-tools を編集して Client ID / Client Secret を入力
~~~

`uv` で直接実行する場合はカレントディレクトリの `.env` でも可:

~~~sh
cp .env.example .env
# .env を編集して Client ID / Client Secret を入力
~~~

**3. 依存関係をインストール**

~~~sh
uv sync
~~~

**pipx でコマンドとしてインストールする場合（任意）**

`split-playlist` / `find-duplicates` をコマンドとしてどこからでも実行したい場合は `pipx` でインストールできる:

~~~sh
pipx install .
~~~

リポジトリを編集しながら試す場合は `--editable` を付ける:

~~~sh
pipx install --editable .
~~~

## Configuration

| 変数 | 説明 |
|---|---|
| `SPOTIFY_CLIENT_ID` | Spotify アプリの Client ID |
| `SPOTIFY_CLIENT_SECRET` | Spotify アプリの Client Secret |
| `SPOTIFY_REDIRECT_URI` | OAuth コールバック URI（デフォルト: `http://localhost:8888/callback`） |

## Usage

### split-playlist

~~~sh
uv run split-playlist
~~~

初回実行時にブラウザが開き OAuth 認証が走る。認証後はトークンがキャッシュされ、次回以降は自動更新される。

**操作フロー:**

1. ソースプレイリストを番号で選択（Liked Songs も選択可）
2. 曲一覧を確認し、移動したい曲番号を入力（例: `1,3,5-8`）
3. 移動先プレイリストを選択（新規作成も可）
4. 確認後に実行

### spotify-inventory

Spotify 上のデータを一切変更しない読み取り専用コマンド。プレイリスト一覧・曲一覧を Markdown または JSON で出力する。認証には読み取り専用スコープのみを要求する。

~~~sh
# プレイリスト一覧（Liked Songs を含む）
uv run spotify-inventory playlists
uv run spotify-inventory playlists --prefix "Work" --format json

# 指定プレイリストの曲一覧（Liked Songs は playlist_id に "liked" を指定）
uv run spotify-inventory tracks <playlist-id>
uv run spotify-inventory tracks liked --format json
~~~

### reorder-by-key

プレイリストを Camelot Wheel(ハーモニックミキシング)順に並べ替える、書き込み系コマンド。1曲目のキーを起点に、残りの曲を隣接キー優先の順序に in-place で並べ替える。

Spotify Web API は2024年11月27日以降、新規アプリから Audio Features(曲のキー・BPM等)エンドポイントへのアクセスを許可していない。そのため、このコマンドはキー情報を自動取得せず、外部で調べたキーをテキストファイルとして受け取る暫定仕様になっている(例: Spotify 純正アプリの Mix 機能の画面を見て手動で書き出す)。

~~~sh
# keys.txt: プレイリストの現在の並び順と1対1で対応する Camelot キーを1行ずつ
# 例:
#   10B
#   10A
#   9B
uv run reorder-by-key <playlist-id> keys.txt
~~~

- 時計回り/反時計回りは、プレイリスト内の実際のキー分布を見て、起点からどちらの方向がより密集して収まるかを自動判定する
- 同じ Camelot 番号内ではメジャー/マイナー(relative key)を近接として扱う
- 実行前に並べ替え後の順序を表示して確認を求める(`--yes` でスキップ可能)
- Playlist Groups の保護設定(`protected`)が有効な場合、対象プレイリストが保護・未分類なら拒否される

## Playlist Groups

公式APIにないプレイリストフォルダの保護境界をローカル設定で代替する機能。Spotify Web API はプレイリストをフラットな一覧で返すだけで、Spotify クライアント上の「フォルダ」情報を提供しない。そのため、フォルダによる分類・保護をローカル設定で代替する仕組みを用意している。

**設定ファイルの配置:**

~~~sh
cp spotify-tools-groups.toml.example ~/.config/spotify-tools-groups.toml
# ~/.config/spotify-tools-groups.toml を編集して自分のプレイリスト分類を記述する
~~~

このファイルは個人用マッピングのためリポジトリにはコミットしない（`~/.config/` はリポジトリの外）。

**設定例:**

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

**安全側に倒す挙動（フェイルセーフ）:**

- 設定ファイルが存在しない場合、保護機能は無効。全プレイリストが従来どおり移動元・移動先として選択できる
- 設定ファイルが存在する場合、`protected` グループのプレイリストは移動元・移動先の両方の選択肢から除外され、実行直前にも拒否される
- 設定ファイルが存在する場合、`id`/`name` のどちらにも一致しない（未分類）、または複数の異なるグループに一致する（曖昧）プレイリストも同様に除外・拒否される
- 分割中に新規作成したプレイリストは「未分類」であることを理由には拒否されないが、名前が `protected` や曖昧なルールと衝突する場合は拒否される
- ガードが有効な場合、Liked Songs もガードの対象になる。移動元として使い続けたい場合は設定に `name = "Liked Songs"` のルールを追加すること

**検証方法・既知の制約:**

- このローカル設定と Spotify クライアント上の実際のフォルダ構造が一致しているかは自動検証できない。`uv run spotify-inventory playlists` の出力（Group 列）で意図した分類になっているか目視確認すること
- 非公式 API・Spotify クライアント内部データの解析・ブラウザ自動操作には依存しない

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
