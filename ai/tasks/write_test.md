# Write Test

1. テスト対象の仕様をspecification.mdで確認
2. 正常系・異常系・境界値を洗い出す
3. fixtureはtests/conftest.pyに定義
4. モックはProtocolベースで注入する
5. テスト名は `test_<対象>_<条件>_<期待結果>` の形式
