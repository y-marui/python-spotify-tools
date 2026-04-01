# Python Package Template

> **このファイルは正本（日本語版）です。**
> 英語版（参照）は [README.md](README.md) を参照してください。

[![CI](https://github.com/y-marui/python-package-template/actions/workflows/ci.yml/badge.svg)](https://github.com/y-marui/python-package-template/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

| 項目 | 内容 |
|---|---|
| 開発対象 | Python パッケージ / アプリケーション |
| 開発環境 | 個人〜小規模チーム（1〜3人） |
| 主言語 | 英語 |
| AI ツール | Claude Code / GitHub Copilot / Gemini CLI |
| 動作環境 | Python ^3.11 |

AI支援開発向けの Python パッケージ/アプリケーションテンプレート。
uv + Claude Code + GitHub Copilot 前提の OSS テンプレート。

## Features

✅ uv による依存管理
✅ ruff による linting / formatting（line-length=88）
✅ mypy による型チェック（strict モード）
✅ pytest によるテスト（unit / integration 分離）
✅ GitHub Actions CI（ruff → mypy → pytest）
✅ Claude Code + GitHub Copilot 向け AI コンテキスト設定済み
✅ pre-commit セキュリティフック設定済み

## Quick Start

```sh
# 1. テンプレートからリポジトリを作成
#    GitHub の "Use this template" ボタンを使用するか、クローンする
git clone https://github.com/[user]/[repo].git my-project
cd my-project

# 2. パッケージ名を変更
mv src/project_name src/your_package_name
# pyproject.toml の name フィールドも更新すること

# 3. 依存関係をインストール
make install

# 4. 動作確認
make all
```

## Commands

| コマンド | 内容 |
|---|---|
| `make install` | `uv sync`（依存関係インストール） |
| `make lint` | `ruff check .`（linting） |
| `make type` | `mypy src`（型チェック） |
| `make test` | `pytest`（テスト実行） |
| `make all` | lint + type + test |
| `make update-charter` | dev-charter を最新化（git subtree pull） |

## Project Structure

```
.
├── src/
│   └── project_name/      # パッケージ本体（名前を変更すること）
├── tests/
│   ├── unit/              # 単体テスト
│   └── integration/       # 統合テスト
├── ai/
│   ├── context/           # AI 向け制約要約
│   ├── review/            # AI レビューチェックリスト
│   └── tasks/             # AI タスクプロンプトテンプレート
├── docs/
│   ├── dev-charter/       # 開発憲章（git subtree）
│   ├── architecture.md    # アーキテクチャ設計
│   ├── specification.md   # 仕様書
│   └── guardrails.md      # 開発制約
├── examples/              # 実装パターンサンプル
├── AI_CONTEXT.md          # AI ツール向けコンテキスト
├── pyproject.toml         # プロジェクト設定
└── Makefile               # 開発コマンド
```

## Documentation

| ドキュメント | 内容 |
|---|---|
| [docs/architecture.md](docs/architecture.md) | アーキテクチャ設計 |
| [docs/specification.md](docs/specification.md) | 仕様書 |
| [docs/guardrails.md](docs/guardrails.md) | 開発制約・ガードレール |
| [AI_CONTEXT.md](AI_CONTEXT.md) | AI ツール向けコンテキスト |

## AI-Assisted Development

`AI_CONTEXT.md` に AI ツール向けコンテキストが設定済みです。

| ツール | 担当 |
|---|---|
| Claude Code | 立ち上げ・大規模変更・アーキテクチャ設計 |
| GitHub Copilot | バグ修正・細かな実装・テスト作成 |
| Gemini CLI | ドキュメント管理・翻訳補助 |

## Customization

1. `src/project_name/` → `src/your_package_name/` にリネーム
2. `pyproject.toml` の `name` フィールドを更新
3. `AI_CONTEXT.md` のプロジェクト概要を更新
4. `LICENSE` の `[YEAR]` と `[AUTHOR]` を置換
5. バッジ URL の `[user]` と `[repo]` を置換
6. `make all` で動作確認

## License

MIT License — [LICENSE](LICENSE) を参照

---
*この文書には英語版 [README.md](README.md) があります。編集時は同一コミットで更新してください。*
