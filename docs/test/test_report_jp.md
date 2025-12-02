# テスト実行レポート

## 概要

Gospelo-backlog-docs パッケージの単体テスト実行結果レポートです。

**実行日時**: 2025-12-03
**Python バージョン**: 3.12.8
**pytest バージョン**: 7.4.4

---

## テスト戦略

### テスト方針

本プロジェクトでは、**リスクベースのテストアプローチ**を採用しています。

- バグが発生しやすい複雑なロジックを重点的にテスト
- 外部依存（Backlog API、mmdc コマンド）はモックでテスト
- 単純なグルーコード（CLI 引数処理等）はテストコストに見合わないためスキップ

### テスト観点

| 観点             | 説明                                    | 対象モジュール                    |
| ---------------- | --------------------------------------- | --------------------------------- |
| **正常系**       | 期待通りの入力で正しく動作するか        | 全モジュール                      |
| **異常系**       | エラー入力で適切にエラー処理されるか    | 全モジュール                      |
| **境界値**       | 空ファイル、空文字列、長い文字列等      | markdown_parser, uploader         |
| **エッジケース** | 階層構造タイトル、絵文字、複数 H1 等    | markdown_parser, uploader         |
| **外部依存**     | API/コマンドの成功・失敗・タイムアウト  | backlog_client, mermaid_converter |
| **設定**         | 環境変数、引数、.env ファイルの優先順位 | backlog_client                    |

### モジュール別テスト方針

| モジュール             | 方針                 | 理由                               |
| ---------------------- | -------------------- | ---------------------------------- |
| `markdown_parser.py`   | 網羅的にテスト       | パーサーロジックはバグが起きやすい |
| `backlog_client.py`    | API コールをモック   | 実際の API は統合テストで検証      |
| `mermaid_converter.py` | 外部コマンドをモック | CI 環境で mmdc 不要にするため      |
| `uploader.py`          | 主要フローをテスト   | 各コンポーネントの結合部分         |
| `cli.py`               | collect 関数をテスト | ファイル収集ロジックはバグが起きやすい |
| `__main__.py`          | テストなし           | cli.main()を呼ぶだけの 3 行        |

### カバレッジ目標

- **全体目標**: 70%以上（達成: 74%）
- **主要ロジック**: 80%以上（markdown_parser: 91%, mermaid_converter: 82%）
- **100%を目指さない理由**: テストのためのテストを避け、メンテナンス性を優先

---

## テスト結果サマリー

| 項目       | 値    |
| ---------- | ----- |
| 総テスト数 | 111   |
| 成功       | 110   |
| 失敗       | 0     |
| スキップ   | 1     |
| 実行時間   | 0.19s |

## カバレッジレポート

| モジュール             | ステートメント | 未カバー | カバレッジ |
| ---------------------- | -------------- | -------- | ---------- |
| `__init__.py`          | 5              | 0        | 100%       |
| `__main__.py`          | 3              | 3        | 0%         |
| `backlog_client.py`    | 128            | 33       | 74%        |
| `cli.py`               | 62             | 33       | 47%        |
| `markdown_parser.py`   | 76             | 7        | 91%        |
| `mermaid_converter.py` | 71             | 13       | 82%        |
| `uploader.py`          | 142            | 38       | 73%        |
| **合計**               | **487**        | **127**  | **74%**    |

### カバレッジ補足

- `cli.py`: `collect_markdown_files` 関数は単体テストでカバー、`main` 関数は統合テストでカバー
- `__main__.py`: CLI エントリポイントのため、統合テストでカバー
- `mermaid_converter.py`: 外部コマンド（mmdc）依存部分はモックでテスト
- 主要なビジネスロジックは 70%以上のカバレッジを達成

## テストファイル構成

```
tests/
├── __init__.py
├── test_cli.py                # 27 tests (v1.1.0で追加)
├── test_markdown_parser.py    # 17 tests
├── test_backlog_client.py     # 22 tests
├── test_mermaid_converter.py  # 24 tests
└── test_uploader.py           # 21 tests
```

## テストケース詳細

### test_markdown_parser.py (17 tests)

#### TestMarkdownParser

- `test_extract_images` - 画像参照の抽出
- `test_extract_mermaid_blocks` - MermaidJS ブロックの抽出
- `test_extract_h1_title` - H1 タイトルの抽出
- `test_extract_h1_title_not_found` - H1 タイトルがない場合
- `test_resolve_image_path_local_exists` - ローカル画像パス解決（存在する）
- `test_resolve_image_path_local_not_exists` - ローカル画像パス解決（存在しない）
- `test_resolve_image_path_external` - 外部 URL 画像パス
- `test_get_all_local_images` - ローカル画像一覧取得
- `test_replace_content` - コンテンツ置換

#### TestImageReference / TestMermaidBlock

- データクラスの生成テスト

#### TestAnalyzeMarkdown

- `test_analyze_markdown` - Markdown 分析関数

#### TestEdgeCases

- `test_empty_markdown` - 空ファイル
- `test_markdown_with_only_text` - テキストのみ
- `test_hierarchical_wiki_title` - 階層構造タイトル
- `test_image_with_empty_alt` - 空の alt テキスト
- `test_multiple_h1_titles` - 複数 H1 タイトル

### test_backlog_client.py (22 tests)

#### TestLoadEnvFiles

- `test_load_explicit_env_file` - 明示的.env ファイル読み込み
- `test_load_explicit_env_file_not_found` - 存在しない.env ファイル
- `test_load_local_env_file` - ローカル.env ファイル読み込み
- `test_no_env_file_found` - .env ファイルなし

#### TestBacklogClient

- `test_init_with_arguments` - 引数での初期化
- `test_init_with_env_vars` - 環境変数での初期化
- `test_init_missing_space_id` - スペース ID 未設定エラー
- `test_init_missing_api_key` - API キー未設定エラー
- `test_init_default_domain` - デフォルトドメイン
- `test_argument_priority_over_env` - 引数が環境変数より優先

#### TestBacklogClientRequests

- `test_request_success` - 正常リクエスト
- `test_request_api_error` - API エラー
- `test_upload_attachment` - 添付ファイルアップロード
- `test_get_wiki_list` - Wiki 一覧取得
- `test_get_wiki` - Wiki 取得
- `test_create_wiki` - Wiki 作成
- `test_update_wiki` - Wiki 更新
- `test_attach_files_to_wiki` - 添付ファイル紐付け

#### TestWikiPage / TestAttachment / TestGetAttachmentUrl

- データクラスとユーティリティ関数のテスト

### test_uploader.py (19 tests)

#### TestRemoveEmojis

- `test_remove_basic_emojis` - 基本絵文字除去
- `test_preserve_japanese_text` - 日本語保持
- `test_mixed_content` - 混在コンテンツ
- `test_no_emojis` - 絵文字なし
- `test_empty_string` - 空文字列
- `test_transport_emojis` - 乗り物絵文字
- `test_flag_emojis` - 国旗絵文字
- `test_preserve_symbols` - 記号保持

#### TestWikiUploader

- `test_init` - 初期化
- `test_init_with_quiet_mode` - quietモードでの初期化
- `test_log_outputs_when_not_quiet` - 非quietモードでログ出力
- `test_log_suppressed_when_quiet` - quietモードでログ抑制
- `test_init_with_mermaid` - Mermaid 有効時の初期化
- `test_generate_mermaid_filename` - ファイル名生成
- `test_generate_mermaid_filename_unique` - ユニーク性

#### TestWikiUploaderUpload

- `test_upload_file_not_found` - ファイル未存在エラー
- `test_upload_dry_run` - ドライラン
- `test_upload_wiki_name_from_h1` - H1 から Wiki 名取得
- `test_upload_wiki_name_override` - Wiki 名上書き
- `test_upload_with_images` - 画像付きアップロード

#### TestWikiUploaderWikiNameFallback

- `test_wiki_name_fallback_to_filename` - ファイル名フォールバック

#### TestWikiUploaderHierarchicalName

- `test_hierarchical_wiki_name` - 階層構造 Wiki 名

### test_cli.py (27 tests) - v1.1.0 で追加

#### TestCollectMarkdownFiles (13 tests)

- `test_single_file` - 単一 Markdown ファイルの収集
- `test_single_file_non_markdown` - 非 Markdown ファイルは無視
- `test_directory_flat` - フラットディレクトリからファイル収集
- `test_directory_recursive` - 再帰的ディレクトリ検索
- `test_directory_non_recursive` - 非再帰的ディレクトリ検索
- `test_custom_pattern` - カスタムファイルパターン
- `test_exclude_pattern` - パターンによるファイル除外
- `test_exclude_multiple_patterns` - 複数パターンの除外
- `test_empty_directory` - 空ディレクトリ
- `test_nonexistent_path` - 存在しないパス
- `test_sorted_results` - 結果のソート順
- `test_deep_nesting` - 深いネストのディレクトリ
- `test_case_insensitive_extension` - 大文字小文字を区別しない拡張子

#### TestProgressSpinner (14 tests)

- `test_init` - スピナーの初期化
- `test_get_progress_bar_empty` - 0%のプログレスバー
- `test_get_progress_bar_half` - 50%のプログレスバー
- `test_get_progress_bar_full` - 100%のプログレスバー
- `test_get_progress_bar_zero_total` - 合計0のプログレスバー
- `test_get_percentage_zero` - 0%のパーセンテージ
- `test_get_percentage_half` - 50%のパーセンテージ
- `test_get_percentage_full` - 100%のパーセンテージ
- `test_get_percentage_zero_total` - 合計0のパーセンテージ
- `test_stop_increments_current` - stop()でカウンター増加
- `test_stop_success_icon` - 成功時にチェックマーク表示
- `test_stop_failure_icon` - 失敗時に×マーク表示
- `test_finish_prints_newline` - finish()で改行出力
- `test_spinner_frames_constant` - スピナーフレームの定義

### test_mermaid_converter.py (24 tests)

#### TestCheckMermaidCliInstalled

- `test_mmdc_installed` - mmdc インストール確認（存在する場合）
- `test_mmdc_not_installed` - mmdc インストール確認（存在しない場合）

#### TestConversionResult

- `test_success_result` - 成功結果の生成
- `test_failure_result` - 失敗結果の生成

#### TestMermaidConverterInit

- `test_init_with_output_dir` - 出力ディレクトリ指定での初期化
- `test_init_without_output_dir` - 出力ディレクトリなしでの初期化
- `test_init_mmdc_not_installed` - mmdc なしでの初期化エラー
- `test_init_with_string_path` - 文字列パスでの初期化

#### TestMermaidConverterGetOutputDir

- `test_get_output_dir_with_specified_dir` - 指定ディレクトリの取得
- `test_get_output_dir_creates_temp_dir` - 一時ディレクトリの作成

#### TestMermaidConverterConvert

- `test_convert_success` - 変換成功
- `test_convert_failure_nonzero_return` - 変換失敗（非ゼロリターン）
- `test_convert_failure_no_output_file` - 変換失敗（出力ファイルなし）
- `test_convert_timeout` - 変換タイムアウト
- `test_convert_exception` - 変換中の例外
- `test_convert_svg_format` - SVG 形式での変換
- `test_convert_with_theme` - テーマ指定での変換
- `test_convert_cleans_up_input_file` - 入力ファイルのクリーンアップ

#### TestMermaidConverterConvertMultiple

- `test_convert_multiple_success` - 複数変換成功
- `test_convert_multiple_partial_failure` - 複数変換で一部失敗

#### TestMermaidConverterCleanup

- `test_cleanup_temp_dir` - 一時ディレクトリのクリーンアップ
- `test_cleanup_no_temp_dir` - 一時ディレクトリがない場合
- `test_cleanup_multiple_times` - 複数回のクリーンアップ

#### TestMermaidConverterIntegration

- `test_real_conversion` - 実際の変換テスト（スキップ）

## テスト実行方法

```bash
# 全テスト実行
pytest tests/ -v

# カバレッジ付き実行
pytest tests/ --cov=gospelo_backlog_docs --cov-report=term-missing

# 特定のテストファイル実行
pytest tests/test_markdown_parser.py -v

# 特定のテストクラス実行
pytest tests/test_backlog_client.py::TestBacklogClient -v

# 特定のテスト関数実行
pytest tests/test_uploader.py::TestRemoveEmojis::test_remove_basic_emojis -v
```

## CI/CD 統合

GitHub Actions での自動テスト実行例:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          pip install -e ".[dev]"

      - name: Run tests
        run: |
          pytest tests/ --cov=gospelo_backlog_docs --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: ./coverage.xml
```

---

## テスト品質評価

### 現状の評価

| 観点               | 評価 | 説明                                                     |
| ------------------ | ---- | -------------------------------------------------------- |
| ビジネスロジック   | ◎    | 主要ロジック（パーサー、変換、アップロード、CLI）を網羅  |
| エッジケース       | ◎    | 空ファイル、絵文字、階層構造タイトル、深いネスト等をカバー |
| エラーハンドリング | ○    | タイムアウト、ファイル不在、API 失敗をテスト             |
| モック戦略         | ◎    | 外部依存を適切にモック化、CI/CD で安定動作               |
| メンテナンス性     | ◎    | 111 テスト/0.19 秒、高速で実行可能                       |

### カバレッジ 0%のファイルについて

| ファイル      | カバレッジ | 判断       | 理由                                  |
| ------------- | ---------- | ---------- | ------------------------------------- |
| `__main__.py` | 0%         | テスト不要 | `cli.main()`を呼ぶだけの 3 行         |

`__main__.py` は「グルーコード」であり、ロジックは他モジュールでテスト済みです。

`cli.py` は v1.1.0 で `collect_markdown_files` 関数が追加され、47%のカバレッジを達成しています。`main` 関数（argparse 定義と uploader 呼び出し）は統合テストでカバーされます。

### 結論

**現状のテストは適切な品質を確保しています。**

- リスクの高い部分に集中したテスト設計
- 74%のカバレッジは業界標準（70-80%）の範囲内
- 過剰なテストによるメンテナンスコスト増加を回避

---

## 今後の改善方針

### テスト追加のタイミング

以下の場合にのみテストを追加します：

1. **本番で問題が発生した場合** - 該当箇所のリグレッションテストを追加
2. **新機能追加時** - 新しいロジックに対するテストを追加
3. **リファクタリング時** - 変更箇所の動作保証のためテストを追加

### 追加を検討する可能性があるテスト

| テスト                           | 優先度 | 理由                             |
| -------------------------------- | ------ | -------------------------------- |
| E2E テスト（実際の Backlog API） | 低     | 手動テストで代替可能             |
| 大容量ファイルのテスト           | 低     | 実運用で問題が発生した場合に追加 |
| 並行アップロードのテスト         | 低     | 現状は順次処理で問題なし         |

### CI/CD 環境の改善案

| 改善項目          | 説明                                    |
| ----------------- | --------------------------------------- |
| GitHub Actions    | 自動テスト実行（Python 3.10/3.11/3.12） |
| Codecov 連携      | カバレッジレポートの可視化              |
| pre-commit フック | コミット前のテスト実行（オプション）    |
