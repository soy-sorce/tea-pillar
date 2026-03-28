# IMPLEMENTATION.md — 開発ルール
---

## 1. Overview

| 項目 | 内容 |
|------|------|
| 開発期間 | 2026/03/16 〜 2026/03/21 |
| チーム人数 | 2名 |
| 主要言語 | python, typescript |
| インフラ | GCP |

---

## 2. Repository Structure

```
/
├── backend/          # Python バックエンド（uv 管理）
├── frontend/         # TypeScript フロントエンド（フレームワーク未定）
├── infra/
│   ├── terraform/    # インフラ定義（Terraform）
│   └── docs/         # インフラ関連ドキュメント
├── docs/
│   └── ja/           # 日本語ドキュメント
├── .env.example      # 環境変数サンプル（必ずコミットする）
```

---

## 3. Team Roles（担当分担）

| メンバー | 担当領域 |
|----------|----------|
| soy-sorce | フロントエンド、インフラ（Terraform、GCP設定） |
| kitsuneudon155 | バックエンド・機能開発（主担当） |

- `infra/terraform/` の変更は **soy-sorce のみ** が行う。
- バックエンドの機能実装は **kitsuneudon155 が主導** し、必要に応じて相互レビューを行う。

---

## 4. Branch Strategy（ブランチ運用）

### ブランチ命名規則

```
<name><type>/<short-description>

例：
  <soy-sorce>feature/user-auth
  <soy-sorce>fix/login-redirect
  <soy-sorce>chore/update-dependencies
  <kitsuneudon155>docs/add-api-reference
  <kitsuneudon155>ci/add-ruff-check
  <kitsuneudon155>infra/setup-cloud-run
```

- `<short-description>` は **英語・kebab-case** で記述する。
- 日本語・スペース・大文字の使用は禁止。

### main ブランチの保護

- `main` への **直接 push は禁止**。必ず PR を経由すること。
- `main` は常にデプロイ可能な状態を維持する。
---

## 5. Commit Convention（コミット規約）

[Conventional Commits](https://www.conventionalcommits.org/ja/v1.0.0/) を参考までに。

### ルール

- `<subject>` は **英語** で記述し、文末にピリオドをつけない。
- 1コミット複数の変更を詰め込みすぎなない。
- `WIP:` プレフィックスは PR draft 中のみ許可。

---

## 6. Pull Request Rules

### タイトル

わかりやすければなんでもいいよ。

### レビュールール

- **相互レビュー制**：もう一方のメンバーが必ずレビューする。
- 初期の開発期間だったらいらないが、ci周りがfixしてきた、開発終盤では必須としたい。

---

## 7. CI Rules

### Backend（Python）

| チェック | コマンド | 必須通過 |
|----------|----------|----------|
| Lint・Format | `ruff check . && ruff format --check .` | ✅ |
| 型チェック | `mypy .` | ✅ |

- ライブラリの追加は **`uv add <package>`** のみ使用する。`pip install` の直接実行は禁止。
- `pyproject.toml` と `uv.lock` を必ずコミットに含める。

### Frontend（TypeScript）

| チェック | コマンド | 必須通過 |
|----------|----------|----------|
| 型チェック | `tsc --noEmit` | ✅ |
| Lint | `eslint .` | ✅ |
| Format | `prettier --check .` | ✅ |

---

## 8. Coding Guidelines（コーディング規約）

### 命名規則

| 対象 | Python | TypeScript |
|------|--------|------------|
| 変数・関数 | `snake_case` | `camelCase` |
| クラス | `PascalCase` | `PascalCase` |
| 定数 | `UPPER_SNAKE_CASE` | `UPPER_SNAKE_CASE` |
| ファイル名 | `snake_case.py` | `kebab-case.ts / .tsx` |
| コンポーネント | — | `PascalCase.tsx` |

### Backend（Python）

- **型アノテーション必須**。すべての関数の引数・戻り値に型を付与すること（`mypy` が通ることで保証）。
- **docstring は Google スタイル** で記述する。

```python
def get_user(user_id: int) -> User:
    """ユーザー情報を取得する.

    Args:
        user_id: fetching user id.

    Returns:
        the objects of User.

    Raises:
        UserNotFoundError: the case of user not found.
    """
```

- 素の `except Exception` は禁止。必ず例外の型を明示する。
- `print()` デバッグはコミットに含めない。ログ出力は `logging` モジュールを使用する。

---

## 9. 環境変数

### シークレット・環境変数の管理

- **APIキー・シークレットは絶対にコミットしない。**
- `.env` ファイルは `.gitignore` に追加済みであることを確認すること。
- 環境変数を追加した場合は、**必ず `.env.example` を同時に更新**してコミットする。

```
# .env.example の例
GCP_PROJECT_ID=REPLACE_ME_PROJECT_ID
DATABASE_URL=postgresql://user:password@host:5432/dbname
API_SECRET_KEY=your-secret-key
```

---

## 10. Infrastructure Rules

### 環境構成
今回、dev, stg, prd環境は分けない（!?）。

---
