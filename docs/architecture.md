# Architecture

## Module Structure

| モジュール | 役割 |
|---|---|
| `core` | ビジネスロジック |
| `api` | HTTP interface |
| `repository` | データアクセス |

## Layer Architecture

```
API → Service → Repository → Storage
```

逆方向・循環依存は禁止。
