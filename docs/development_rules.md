# Development Rules

## Branch
- main
- develop
- feature/*

## Flow
1. Issue
2. feature branch
3. AI implementation
4. PR
5. Review

## Task Procedures

### Fix Bug
1. 再現確認
2. 原因特定
3. 最小修正
4. テスト追加

### Implement Feature
1. `docs/architecture.md` で設計を確認する
2. 最小変更で実装する
3. テストを追加する

### Write Test
1. テスト対象の仕様を確認する
2. 正常系・異常系・境界値を洗い出す
3. fixture は `tests/conftest.py` に定義する
4. モックは Protocol ベースで注入する
5. テスト名は `test_<対象>_<条件>_<期待結果>` の形式にする
