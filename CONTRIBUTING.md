# CONTRIBUTING

PR ルールとレビューチェックリスト。ブランチ運用・開発フローは `docs/development_rules.md` を参照。

## Pull Request Flow

`docs/development_rules.md` の Flow を参照。

## Review Checklist

- [ ] **仕様準拠**: `docs/architecture.md` の設計を満たしているか
- [ ] **テスト存在**: 変更箇所にテストが追加されているか
- [ ] **可読性**: 関数 50 行以内・単一責務・適切なコメント
- [ ] **依存関係問題なし**: 循環依存・逆方向依存がないか
- [ ] **型チェック**: mypy strict を通過するか
- [ ] **リント**: ruff check を通過するか
