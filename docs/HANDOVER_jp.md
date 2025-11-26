# プロジェクト引き継ぎドキュメント

## プロジェクト概要

**プロジェクト名**: gospelo-backlog-docs
**バージョン**: 1.0.0
**最終更新日**: 2025-11-26

Markdown ドキュメントを Backlog Wiki にアップロードする CLI ツール。画像と MermaidJS 図のサポート付き。

---

## リポジトリ構成

```
gospelo-backlog-docs/
├── src/gospelo_backlog_docs/    # ソースコード
│   ├── __init__.py              # パッケージ初期化、バージョン
│   ├── __main__.py              # `python -m` 用エントリポイント
│   ├── cli.py                   # CLI 引数解析
│   ├── backlog_client.py        # Backlog API クライアント
│   ├── markdown_parser.py       # Markdown 解析ロジック
│   ├── mermaid_converter.py     # MermaidJS → PNG 変換
│   └── uploader.py              # アップロード統合処理
├── tests/                       # 単体テスト（82テスト、73%カバレッジ）
│   ├── test_backlog_client.py
│   ├── test_markdown_parser.py
│   ├── test_mermaid_converter.py
│   └── test_uploader.py
├── docs/                        # ドキュメント
│   ├── README_jp.md             # 日本語 README
│   ├── CHANGELOG.md / _jp.md    # 変更履歴（英/日）
│   ├── CONTRIBUTING.md / _jp.md # コントリビューションガイド（英/日）
│   └── test/                    # テストレポート
├── README.md                    # メインドキュメント
├── pyproject.toml               # パッケージ設定
├── LICENSE                      # MIT ライセンス
└── THIRD_PARTY_LICENSES.md      # 依存ライブラリのライセンス
```

---

## 主要コンポーネント

### 1. CLI (`cli.py`)
- エントリポイント: `gospelo-backlog-docs` コマンド
- argparse による引数解析
- `uploader.py` の `WikiUploader` を呼び出し

### 2. Backlog クライアント (`backlog_client.py`)
- Backlog API との全通信を担当
- Wiki の CRUD 操作
- 添付ファイルのアップロード
- 認証情報管理（CLI 引数 > 環境変数 > .env ファイル）
- グローバル設定: `~/.config/gospelo-backlog-docs/.env`

### 3. Markdown パーサー (`markdown_parser.py`)
- 画像と MermaidJS ブロックの抽出
- ローカル画像パスの解決
- H1 タイトルから Wiki ページ名を抽出

### 4. Mermaid コンバーター (`mermaid_converter.py`)
- MermaidJS コードブロックを PNG に変換
- `mmdc`（mermaid-cli）が必要
- タイムアウトとクリーンアップ処理

### 5. アップローダー (`uploader.py`)
- アップロード処理全体を統合
- パーサー、コンバーター、クライアントを連携
- ドライランモード対応

---

## 開発環境セットアップ

```bash
# 開発用依存関係をインストール
pip install -e ".[dev]"

# テスト実行
pytest tests/ -v

# カバレッジ付きテスト
pytest tests/ --cov=gospelo_backlog_docs --cov-report=term-missing

# コードフォーマット
black src/ tests/
isort src/ tests/

# 型チェック
mypy src/
```

---

## テスト戦略

| モジュール | カバレッジ | 戦略 |
|-----------|-----------|------|
| markdown_parser.py | 91% | 網羅的 - パーサーロジックはバグが出やすい |
| mermaid_converter.py | 82% | 外部コマンドをモック |
| backlog_client.py | 74% | API コールをモック |
| uploader.py | 73% | 主要フローをテスト |
| cli.py | 0% | テストなし - シンプルなエントリポイント |

**テスト結果**: 81 passed, 1 skipped (0.18s)

---

## 設定

### 環境変数
```
BACKLOG_SPACE_ID=your-space-id
BACKLOG_API_KEY=your-api-key
BACKLOG_DOMAIN=backlog.jp  # または backlog.com
```

### 認証情報の優先順位（高い順）
1. CLI 引数
2. 環境変数
3. 指定された .env ファイル（`--env-file`）
4. ローカル `.env` ファイル
5. グローバル設定 `~/.config/gospelo-backlog-docs/.env`

---

## 依存関係

### 必須
- Python 3.10+
- requests >= 2.28.0
- python-dotenv >= 1.0.0

### オプション
- mermaid-cli（npm パッケージ）：MermaidJS サポート用

### 開発用
- pytest, pytest-cov
- black, isort, mypy

---

## 既知の問題 / 技術的負債

1. **E2E テストなし**: API 連携は手動テスト
2. **順次アップロード**: 画像は1つずつアップロード（並列未実装）
3. **日本語エラーメッセージ**: 一部のエラーメッセージが日本語

---

## 今後の改善案（必要に応じて）

| 機能 | 優先度 | 備考 |
|-----|--------|------|
| 並列画像アップロード | 低 | 現状の順次処理で問題なし |
| GitHub Actions CI | 中 | 自動テスト |

---

## PyPI 公開情報

- **PyPI**: https://pypi.org/project/gospelo-backlog-docs/
- **インストール**: `pip install gospelo-backlog-docs`
- **公開日**: 2025-11-26
- **公開手順**: [internal/docs/pypi_account_setup.md](internal/docs/pypi_account_setup.md)

---

## よく使うコマンド

```bash
# 基本的なアップロード
gospelo-backlog-docs document.md --project PROJECT_KEY

# ドライラン（アップロードなし）
gospelo-backlog-docs document.md --project PROJECT_KEY --dry-run

# Wiki 名を指定
gospelo-backlog-docs document.md --project PROJECT_KEY --wiki-name "親/子"

# 特定の env ファイルを使用
gospelo-backlog-docs document.md --project PROJECT_KEY --env-file .env.production
```

---

## 連絡先 / リソース

- **リポジトリ**: https://github.com/gorosun/gospelo-backlog-docs
- **テストレポート**: [docs/test/test_report_jp.md](docs/test/test_report_jp.md)
- **コントリビューションガイド**: [docs/CONTRIBUTING_jp.md](docs/CONTRIBUTING_jp.md)
