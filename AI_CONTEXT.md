# AI_CONTEXT.md

> このファイルは Claude Code・GitHub Copilot など AI ツールが唯一参照するコンテキストファイルです。
> セッション開始時に必ず読み込んでください。

---

## Project Overview

**目的:** AI支援開発用の Python パッケージ/アプリケーションテンプレート。
uv + Claude Code + GitHub Copilot 前提の OSS テンプレート。

**チーム規模:** 個人〜3人（小規模チーム）。アジャイルで迅速な意思決定を重視。

**技術スタック:**

| 項目 | バージョン |
|------|-----------|
| Python | ^3.11 |
| uv | 最新安定版 |
| pytest | ^8 |
| ruff | ^0.3（linter / formatter, line-length=88） |
| mypy | ^1.8（strict モード） |

**主要ディレクトリ:**

```
src/project_name/   # パッケージ本体
tests/unit/         # 単体テスト
tests/integration/  # 統合テスト
ai/context/         # AI向け制約要約（毎回読み込む）
docs/               # 人間が書き・読む仕様書（AI は参照のみ）
docs/dev-charter/   # 開発憲章（git subtree で取り込み）
examples/           # 実装パターンサンプル
```

**モジュール構成と依存方向:**

```
API → Service → Repository
```
逆依存禁止。循環依存禁止。

**AI コンテキスト優先順位:**
1. タスクコンテキスト（Issue / Pull Request）
2. プロジェクトコンテキスト（`AI_CONTEXT.md`・プロジェクトドキュメント）
3. 開発憲章（`docs/dev-charter/`）
4. グローバルコンテキスト

**ファイル読み込み順序:**
1. `AI_CONTEXT.md`（このファイル）
2. `ai/context/`（全ファイル）
3. `docs/specification.md`（詳細が必要な場合のみ）
4. `docs/architecture.md`（詳細が必要な場合のみ）
5. `docs/guardrails.md`

---

## Applied Charter Principles

### Pre-Coding Checklist

不明・未定の項目があれば**作業前に1回でまとめて**質問する。推測で進めない。

**確認必須:**
- ゴール（完了条件）
- 言語・FW・バージョン制約
- 新規 or 既存コード修正
- テストの要否
- 影響範囲

**確認不要（既存コードに合わせて進める）:**
- コードスタイル / ファイル配置 / 軽微な実装詳細

### Development Philosophy

- まず小さなツールを構築する（段階的に拡張する）
- ローカルファーストのデザインを優先する（外部サービス依存を避ける）
- インフラストラクチャを最小限に保つ
- **最小限の依存関係**: 新規依存追加前に既存の依存で解決できないか必ず検討する
- オフライン機能を優先する（外部サービスなしで動作することを基本とする）

### Code Design Principles

- **変更範囲は必要最小限**（Over-engineering しない）
- **YAGNI**: 今必要ない機能は実装しない
- **DRY の判断**: 2回の重複では抽象化しない、3回目で検討
- **既存コードの再利用**: 新規実装前に類似機能がないか確認
- **TODO/FIXME を残さない**: 実装するか、issue として記録する
- **既存コードのパターンに従う**: 命名規則・アーキテクチャ・ディレクトリ構造

### Coding Rules

- 可読性優先
- 関数は **50行以内**
- 単一責務
- コメントは「なぜそうするか」のみ。コードから自明な処理には書かない

### Git Workflow

- **Conventional Commits** 形式（`feat` / `fix` / `refactor` / `docs` / `chore`）
- **WIP 禁止**: 動作しないコードはコミットしない
- コミット粒度: 機能単位・動作確認 OK 後

### Work Stance

- **スコープ厳守**: 会話の主題・タスク・ゴールを AI が勝手に変更しない。話題変更はユーザーが明示するか、AI の提案をユーザーが許可した場合のみ
- **不明点の扱い**: 重要な情報不足や曖昧さは質問する。軽微な不足は合理的な仮定で補い、仮定を明示する。推測で断定しない
- 大きな変更前に方針を説明してから着手する
- 不要な依存追加禁止: 既存の依存で解決できないか先に検討する

### Error & Debug Handling

- エラー発生時は **原因分析 → 修正方針説明 → 実装** の順で進める
- エラーログ・スタックトレースは必ず**全文確認**してから対応（推測で修正しない）
- デバッグ用の `print` 文は本番コードに残さない

---

## Project-Specific Rules

### Monetization Policy

- 独自の課金システムは**原則禁止**（メンテナンスコスト・セキュリティリスクのため）
- OSS の場合: **Buy Me a Coffee + GitHub Sponsors** を使用する
- マネタイズを本格検討する場合は `MONETIZATION.md` をリポジトリに作成し、この `AI_CONTEXT.md` に概要を追記する

### Language Policy

このプロジェクトは **OSS** のため、ドキュメント・コード・コメントは**英語**を基本とする。

| ファイル | 言語 |
|---|---|
| `README.md` | 英語（国際的な参照用） |
| `README-jp.md` | 日本語（正本）※ 必要に応じて作成 |
| ソースコード・コメント | 英語 |
| `AI_CONTEXT.md` | 日本語（開発チーム内部ツール、ユーザー判断による） |

日英両方のドキュメントが存在する場合は**日本語版を正本**として編集し、英語版をそれに合わせて更新する（英語版を独立して編集しない）。

### docs/ and ai/context/ Roles

| ディレクトリ | 役割 | AI の編集 |
|---|---|---|
| `docs/` | 人間が書き・読む詳細仕様書 | **禁止**（参照のみ） |
| `ai/context/` | AI向け制約要約。`docs/` と競合する場合は **こちらを優先** | 更新可 |

### CI / Local Development Commands

```sh
make install        # uv sync
make lint           # ruff check .
make type           # mypy src
make test           # pytest
make all            # lint + type + test
make update-charter # git subtree pull で dev-charter を最新化
```

CI（GitHub Actions）は push / PR のたびに `ruff check` → `mypy src` → `pytest` を実行。

### Pre-commit Hooks (.pre-commit-config.yaml)

セキュリティ・品質チェックが自動で走る。以下が有効:

| フック | 内容 |
|---|---|
| gitleaks | シークレット検出（`.gitleaks.toml` 設定） |
| detect-private-key | SSH 秘密鍵検出 |
| detect-dotenv | `.env` ファイルのコミットをブロック |
| no-hardcoded-local-paths | ローカル絶対パスのハードコードをブロック |
| check-added-large-files | 500 KB 超ファイルをブロック |
| trailing-whitespace / end-of-file-fixer | 空白・改行の正規化 |
| check-yaml / check-json / check-merge-conflict | 構文・競合チェック |
| shellcheck | シェルスクリプト静的解析 |

**セキュリティの二層構造:**
- **層1**: 個人のグローバル git フック（`~/.config/git/hooks/pre-commit`）— 開発者個人の全リポジトリに適用される安全網
- **層2**: per-repo の `.pre-commit-config.yaml` — チームとしての強制手段。CI でも必ず動作させる

セットアップ:

```sh
cp docs/dev-charter/.pre-commit-config.yaml .
cp docs/dev-charter/.gitleaks.toml .
# core.hooksPath が設定済みの場合は pre-commit install 不要
git config core.hooksPath 2>/dev/null \
  && echo "core.hooksPath 設定済み。次のコマンドで確認:" \
  || pre-commit install
pre-commit run --all-files  # 動作確認（必須）
```

**コードレビュー要件:**
- `main` に到達するコミットは必ず他の開発者がレビューする
- 認証・認可・暗号化・データアクセスに関わる変更はセキュリティレビューを必須とする

---

## AI Tool Assignments

| ツール | 担当範囲 |
|---|---|
| **Claude Code** | プロジェクト立ち上げ、大規模なコード変更、アーキテクチャ設計・リファクタリング提案 |
| **GitHub Copilot** | バグ修正、細かな実装・コーディング補助、単体テスト作成 |
| **Gemini CLI** | プライバシーポリシー作成・更新、ストア説明文、審査用ドキュメント、プロジェクト全体のドキュメント管理 |

**AI_CONTEXT.md の同期ルール:**
- 憲章（`docs/dev-charter/`）を `git subtree pull` で更新した後、AI に差分を確認させて `AI_CONTEXT.md` を更新する

**AI 並用時のルール:**
- Claude Code 作業中は Copilot 提案を**参考程度**に（盲目的に受け入れない）
- Copilot の提案がプロジェクト規約に反する場合は無視し、Claude Code でレビュー後に採用判断する
- Gemini CLI は `GEMINI.md` 経由で `@AI_CONTEXT.md` の自動読み込みをサポート

---

## Prohibited Actions

### Security Constraints

- シークレット・API キー・パスワード・トークンを**絶対にコードに書かない**（環境変数または Secret Manager を使う）
- `.env` ファイルをコミットしない（ダミー値のみの `.env.example` をコミットする）
- SSH 秘密鍵・クラウドトークンをコミットしない
- ローカル絶対パス（`/Users/...`、`/home/...`、`C:\Users\...`）をコードにハードコードしない
- 500 KB を超えるファイルをコミットしない
- AI との会話ログをリポジトリにコミットしない
- **シークレットを含むファイルやコードを AI に渡さない**（プロンプト・コンテキスト・スクリーンショット含む）
- **AI が生成したコードは必ずレビューしてからコミットする**

### Prohibited Out-of-Scope Changes

- **API 仕様変更禁止**: API レスポンス変更・エンドポイント削除（破壊的変更で他サービスに影響）
- **設計変更禁止**: ディレクトリ構造変更・モジュール移動（アーキテクチャの一貫性を保つため）
- **大規模リファクタ禁止**: 意図しない挙動変化を防ぐため（明示的に依頼された場合を除く）
- **依存追加禁止**: ライセンス・セキュリティリスクを人間がレビューするため。必要な場合は Issue を作成する
- **WIP コミット禁止**: 動作しないコードはコミットしない
- `docs/` ディレクトリを AI が直接編集しない（参照のみ）
