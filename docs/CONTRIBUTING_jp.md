# コントリビューションガイド

gospelo-backlog-docsへの貢献に興味を持っていただきありがとうございます！

## 開発環境のセットアップ

### 必要要件

- Python 3.10+
- Node.js（mermaid-cli用、オプション）

### インストール

1. リポジトリをクローン：
```bash
git clone https://github.com/gorosun/gospelo-backlog-docs.git
cd gospelo-backlog-docs
```

2. 開発用依存関係をインストール：
```bash
pip install -e ".[dev]"
```

3. （オプション）MermaidJSサポート用にmermaid-cliをインストール：
```bash
npm install -g @mermaid-js/mermaid-cli
```

## テストの実行

```bash
# 全テスト実行
pytest tests/ -v

# カバレッジ付き実行
pytest tests/ --cov=gospelo_backlog_docs --cov-report=term-missing

# 特定のテストファイル実行
pytest tests/test_markdown_parser.py -v
```

## コードスタイル

このプロジェクトでは以下を使用しています：
- **black** - コードフォーマット
- **isort** - インポートの整列
- **mypy** - 型チェック

```bash
# コードフォーマット
black src/ tests/
isort src/ tests/

# 型チェック
mypy src/
```

## プルリクエストの手順

1. リポジトリをフォーク
2. フィーチャーブランチを作成（`git checkout -b feature/amazing-feature`）
3. 変更を加える
4. テストを実行し、パスすることを確認
5. 変更をコミット（`git commit -m 'Add amazing feature'`）
6. ブランチにプッシュ（`git push origin feature/amazing-feature`）
7. プルリクエストを開く

### コミットメッセージのガイドライン

- 明確で説明的なコミットメッセージを使用
- 動詞で開始（Add, Fix, Update, Remove など）
- 該当する場合はIssueを参照

例：
```
Add support for SVG output format
Fix image path resolution for Windows
Update README with new examples
```

## Issue の報告

Issue を報告する際は、以下を含めてください：

1. Python バージョン（`python --version`）
2. パッケージバージョン（`gospelo-backlog-docs --version`）
3. オペレーティングシステム
4. 再現手順
5. 期待される動作
6. 実際の動作
7. エラーメッセージ（ある場合）

## 機能リクエスト

機能リクエストは歓迎します！以下を含むIssueを開いてください：

1. 機能の明確な説明
2. ユースケース / 動機
3. （オプション）提案する実装アプローチ

## テストのガイドライン

- 新機能にはテストを書く
- コードカバレッジを維持または改善する
- 外部依存（APIコール、外部コマンド）はモックする
- 既存のテストパターンに従う

現在のテストカバレッジと戦略については[テストレポート](test/test_report_jp.md)を参照してください。

## ライセンス

貢献することにより、あなたの貢献がMITライセンスの下でライセンスされることに同意したものとみなされます。
