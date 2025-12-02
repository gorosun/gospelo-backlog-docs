"""Tests for uploader module."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import os
import io
import sys

from gospelo_backlog_docs.uploader import (
    WikiUploader,
    remove_emojis,
)
from gospelo_backlog_docs.backlog_client import WikiPage, Attachment


class TestRemoveEmojis:
    """remove_emojis 関数のテスト"""

    def test_remove_basic_emojis(self):
        """基本的な絵文字の除去"""
        text = "Hello 😀 World 🎉"
        result = remove_emojis(text)
        assert result == "Hello  World "

    def test_preserve_japanese_text(self):
        """日本語テキストは保持される"""
        text = "こんにちは世界"
        result = remove_emojis(text)
        assert result == "こんにちは世界"

    def test_mixed_content(self):
        """絵文字と日本語が混在するテキスト"""
        text = "テスト🚀ドキュメント📝です"
        result = remove_emojis(text)
        assert result == "テストドキュメントです"

    def test_no_emojis(self):
        """絵文字がない場合は変更なし"""
        text = "Plain text without emojis"
        result = remove_emojis(text)
        assert result == text

    def test_empty_string(self):
        """空文字列"""
        result = remove_emojis("")
        assert result == ""

    def test_transport_emojis(self):
        """乗り物絵文字"""
        text = "Go 🚗 Fast 🚀"
        result = remove_emojis(text)
        assert result == "Go  Fast "

    def test_flag_emojis(self):
        """国旗絵文字"""
        text = "Japan 🇯🇵 USA 🇺🇸"
        result = remove_emojis(text)
        assert result == "Japan  USA "

    def test_preserve_symbols(self):
        """通常の記号は保持"""
        text = "Test! @#$%^&*() Done"
        result = remove_emojis(text)
        assert result == text


class TestWikiUploader:
    """WikiUploader クラスのテスト"""

    @pytest.fixture
    def mock_backlog_client(self):
        """モック化されたBacklogClient"""
        with patch("gospelo_backlog_docs.uploader.BacklogClient") as mock:
            client_instance = Mock()
            client_instance.space_id = "test-space"
            client_instance.domain = "backlog.jp"
            mock.return_value = client_instance
            yield client_instance

    @pytest.fixture
    def mock_mermaid_check(self):
        """MermaidCLIチェックのモック"""
        with patch("gospelo_backlog_docs.uploader.check_mermaid_cli_installed") as mock:
            mock.return_value = False  # デフォルトはインストールされていない
            yield mock

    def test_init(self, mock_backlog_client, mock_mermaid_check):
        """WikiUploaderの初期化"""
        uploader = WikiUploader(
            project_key="TEST_PROJECT",
            space_id="test-space",
            api_key="test-key"
        )

        assert uploader.project_key == "TEST_PROJECT"
        assert uploader.mermaid_available is False
        assert uploader.quiet is False

    def test_init_with_quiet_mode(self, mock_backlog_client, mock_mermaid_check):
        """quietモードでの初期化"""
        uploader = WikiUploader(
            project_key="TEST_PROJECT",
            space_id="test-space",
            api_key="test-key",
            quiet=True
        )

        assert uploader.quiet is True

    def test_log_outputs_when_not_quiet(self, mock_backlog_client, mock_mermaid_check):
        """quietモードでない場合はログを出力"""
        uploader = WikiUploader(
            project_key="TEST_PROJECT",
            space_id="test-space",
            api_key="test-key",
            quiet=False
        )

        captured = io.StringIO()
        sys.stdout = captured

        uploader._log("Test message")

        sys.stdout = sys.__stdout__
        output = captured.getvalue()

        assert "Test message" in output

    def test_log_suppressed_when_quiet(self, mock_backlog_client, mock_mermaid_check):
        """quietモードの場合はログを出力しない"""
        uploader = WikiUploader(
            project_key="TEST_PROJECT",
            space_id="test-space",
            api_key="test-key",
            quiet=True
        )

        captured = io.StringIO()
        sys.stdout = captured

        uploader._log("Test message")

        sys.stdout = sys.__stdout__
        output = captured.getvalue()

        assert output == ""

    def test_init_with_mermaid(self, mock_backlog_client, mock_mermaid_check):
        """Mermaid CLIがインストールされている場合"""
        mock_mermaid_check.return_value = True

        uploader = WikiUploader(
            project_key="TEST_PROJECT",
            space_id="test-space",
            api_key="test-key"
        )

        assert uploader.mermaid_available is True

    def test_generate_mermaid_filename(self, mock_backlog_client, mock_mermaid_check):
        """Mermaidファイル名の生成"""
        uploader = WikiUploader(
            project_key="TEST_PROJECT",
            space_id="test-space",
            api_key="test-key"
        )

        filename = uploader._generate_mermaid_filename("graph TD\nA-->B", 0)

        assert filename.startswith("mermaid_0_")
        assert len(filename) == len("mermaid_0_") + 8  # 8文字のハッシュ

    def test_generate_mermaid_filename_unique(self, mock_backlog_client, mock_mermaid_check):
        """異なるコードで異なるファイル名が生成される"""
        uploader = WikiUploader(
            project_key="TEST_PROJECT",
            space_id="test-space",
            api_key="test-key"
        )

        filename1 = uploader._generate_mermaid_filename("graph TD\nA-->B", 0)
        filename2 = uploader._generate_mermaid_filename("graph LR\nX-->Y", 0)

        assert filename1 != filename2


class TestWikiUploaderUpload:
    """WikiUploader.upload メソッドのテスト"""

    @pytest.fixture
    def sample_markdown(self, tmp_path: Path) -> Path:
        """テスト用Markdownファイル"""
        content = """# テストWikiページ

これはテストです。

## セクション1

本文
"""
        md_file = tmp_path / "test.md"
        md_file.write_text(content, encoding="utf-8")
        return md_file

    @pytest.fixture
    def markdown_with_image(self, tmp_path: Path) -> Path:
        """画像付きMarkdownファイル"""
        # 画像ディレクトリ作成
        images_dir = tmp_path / "images"
        images_dir.mkdir()
        (images_dir / "test.png").write_bytes(b"fake png")

        content = """# 画像テスト

![テスト画像](./images/test.png)
"""
        md_file = tmp_path / "test.md"
        md_file.write_text(content, encoding="utf-8")
        return md_file

    @patch("gospelo_backlog_docs.uploader.check_mermaid_cli_installed")
    @patch("gospelo_backlog_docs.uploader.BacklogClient")
    def test_upload_file_not_found(self, mock_client_class, mock_mermaid):
        """存在しないファイルのアップロード"""
        mock_mermaid.return_value = False
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        uploader = WikiUploader(
            project_key="TEST",
            space_id="space",
            api_key="key"
        )

        with pytest.raises(FileNotFoundError) as exc_info:
            uploader.upload("/nonexistent/file.md")

        assert "ファイルが見つかりません" in str(exc_info.value)

    @patch("gospelo_backlog_docs.uploader.check_mermaid_cli_installed")
    @patch("gospelo_backlog_docs.uploader.BacklogClient")
    def test_upload_dry_run(self, mock_client_class, mock_mermaid, sample_markdown):
        """ドライランモード"""
        mock_mermaid.return_value = False
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        uploader = WikiUploader(
            project_key="TEST",
            space_id="space",
            api_key="key"
        )

        result = uploader.upload(str(sample_markdown), dry_run=True)

        assert result["dry_run"] is True
        assert result["wiki_name"] == "テストWikiページ"
        # ドライランではAPIは呼ばれない
        mock_client.create_or_update_wiki.assert_not_called()

    @patch("gospelo_backlog_docs.uploader.check_mermaid_cli_installed")
    @patch("gospelo_backlog_docs.uploader.BacklogClient")
    def test_upload_wiki_name_from_h1(self, mock_client_class, mock_mermaid, sample_markdown):
        """H1タイトルからWiki名を取得"""
        mock_mermaid.return_value = False
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        uploader = WikiUploader(
            project_key="TEST",
            space_id="space",
            api_key="key"
        )

        result = uploader.upload(str(sample_markdown), dry_run=True)

        assert result["wiki_name"] == "テストWikiページ"

    @patch("gospelo_backlog_docs.uploader.check_mermaid_cli_installed")
    @patch("gospelo_backlog_docs.uploader.BacklogClient")
    def test_upload_wiki_name_override(self, mock_client_class, mock_mermaid, sample_markdown):
        """Wiki名を引数で上書き"""
        mock_mermaid.return_value = False
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        uploader = WikiUploader(
            project_key="TEST",
            space_id="space",
            api_key="key"
        )

        result = uploader.upload(
            str(sample_markdown),
            wiki_name="カスタム名",
            dry_run=True
        )

        assert result["wiki_name"] == "カスタム名"

    @patch("gospelo_backlog_docs.uploader.check_mermaid_cli_installed")
    @patch("gospelo_backlog_docs.uploader.BacklogClient")
    def test_upload_with_images(self, mock_client_class, mock_mermaid, markdown_with_image):
        """画像付きアップロード"""
        mock_mermaid.return_value = False
        mock_client = Mock()
        mock_client.space_id = "test-space"
        mock_client.domain = "backlog.jp"

        # アップロード結果
        mock_client.upload_attachment.return_value = Attachment(
            id=12345,
            name="test.png",
            size=8
        )

        # Wiki作成結果
        mock_wiki = WikiPage(
            id=1,
            project_id=100,
            name="画像テスト",
            content="",
            tags=[],
            created="",
            updated=""
        )
        mock_client.create_or_update_wiki.return_value = (mock_wiki, True)

        # 添付ファイル紐付け結果
        mock_client.attach_files_to_wiki.return_value = [
            {"id": 99999, "name": "test.png"}
        ]

        mock_client_class.return_value = mock_client

        uploader = WikiUploader(
            project_key="TEST",
            space_id="space",
            api_key="key"
        )

        result = uploader.upload(str(markdown_with_image))

        assert result["wiki_id"] == 1
        assert result["local_images_uploaded"] == 1
        assert result["is_new"] is True
        mock_client.upload_attachment.assert_called_once()


class TestWikiUploaderWikiNameFallback:
    """Wiki名のフォールバックテスト"""

    @pytest.fixture
    def markdown_no_h1(self, tmp_path: Path) -> Path:
        """H1がないMarkdownファイル"""
        content = """## これはH2

本文のみ
"""
        md_file = tmp_path / "no_h1_test.md"
        md_file.write_text(content, encoding="utf-8")
        return md_file

    @patch("gospelo_backlog_docs.uploader.check_mermaid_cli_installed")
    @patch("gospelo_backlog_docs.uploader.BacklogClient")
    def test_wiki_name_fallback_to_filename(self, mock_client_class, mock_mermaid, markdown_no_h1):
        """H1がない場合はファイル名を使用"""
        mock_mermaid.return_value = False
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        uploader = WikiUploader(
            project_key="TEST",
            space_id="space",
            api_key="key"
        )

        result = uploader.upload(str(markdown_no_h1), dry_run=True)

        assert result["wiki_name"] == "no_h1_test"


class TestWikiUploaderHierarchicalName:
    """階層構造のWiki名テスト"""

    @pytest.fixture
    def markdown_hierarchical(self, tmp_path: Path) -> Path:
        """階層構造のタイトルを持つMarkdown"""
        content = """# 画面設計/メンバー日次/MD0001 日次レポートタブ 画面仕様書

本文
"""
        md_file = tmp_path / "hierarchical.md"
        md_file.write_text(content, encoding="utf-8")
        return md_file

    @patch("gospelo_backlog_docs.uploader.check_mermaid_cli_installed")
    @patch("gospelo_backlog_docs.uploader.BacklogClient")
    def test_hierarchical_wiki_name(self, mock_client_class, mock_mermaid, markdown_hierarchical):
        """階層構造のWiki名が正しく抽出される"""
        mock_mermaid.return_value = False
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        uploader = WikiUploader(
            project_key="TEST",
            space_id="space",
            api_key="key"
        )

        result = uploader.upload(str(markdown_hierarchical), dry_run=True)

        assert result["wiki_name"] == "画面設計/メンバー日次/MD0001 日次レポートタブ 画面仕様書"
