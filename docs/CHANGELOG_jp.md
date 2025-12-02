# 変更履歴

このプロジェクトに対する注目すべき変更はこのファイルに記載されます。

フォーマットは[Keep a Changelog](https://keepachangelog.com/ja/1.1.0/)に基づいており、
このプロジェクトは[セマンティックバージョニング](https://semver.org/lang/ja/)に従います。

## [Unreleased]

## [1.1.0] - 2025-12-03

### 追加

- ディレクトリ一括処理：複数のMarkdownファイルを一度にアップロード
- 再帰的ディレクトリ検索（デフォルトで有効）
- `--no-recursive` フラグでサブディレクトリ検索を無効化
- `--pattern` オプションでカスタムファイルパターンを指定（デフォルト: `*.md`）
- `--exclude` オプションでファイルを除外（複数回指定可能）
- `--continue-on-error` フラグでエラー後も処理を継続
- 進捗表示 `[1/10] Processing: file.md`
- 成功/失敗件数のサマリーレポート

### 変更

- 位置引数を `markdown_file` から `path` に変更（ファイルまたはディレクトリを受け付け）
- 複数ファイル処理時は `--wiki-name` を無視（警告を表示）

## [1.0.0] - 2025-11-26

### 追加

- 初回リリース
- MarkdownファイルをBacklog Wikiにアップロード
- 画像の自動アップロードとリンク変換
- MermaidJS図のPNG変換（mermaid-cli必要）
- H1タイトルからWikiページ名を自動抽出
- 階層構造のWikiページ名をサポート
- 柔軟な認証情報管理：
  - CLI引数
  - 環境変数
  - .envファイル（ローカルおよびグローバル）
- アップロードせずにテストするドライランモード
- 包括的なユニットテスト（82テスト、73%カバレッジ）

### 依存関係

- Python 3.10+
- requests >= 2.28.0
- python-dotenv >= 1.0.0

### オプション依存関係

- mermaid-cli（npmパッケージ）：MermaidJSサポート用

[Unreleased]: https://github.com/gorosun/gospelo-backlog-docs/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/gorosun/gospelo-backlog-docs/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/gorosun/gospelo-backlog-docs/releases/tag/v1.0.0
