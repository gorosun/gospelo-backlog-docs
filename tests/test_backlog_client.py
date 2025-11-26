"""Tests for backlog_client module."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import os
import tempfile

from gospelo_backlog_docs.backlog_client import (
    BacklogClient,
    WikiPage,
    Attachment,
    get_attachment_url,
    _load_env_files,
    CONFIG_DIR,
)


class TestLoadEnvFiles:
    """_load_env_files 関数のテスト"""

    def test_load_explicit_env_file(self, tmp_path: Path):
        """明示的に指定した.envファイルの読み込み"""
        env_file = tmp_path / ".env.test"
        env_file.write_text("TEST_VAR=test_value\n")

        with patch.dict(os.environ, {}, clear=True):
            _load_env_files(str(env_file))
            # dotenvがロードされたことを確認（実際の環境変数は設定されない場合がある）

    def test_load_explicit_env_file_not_found(self, tmp_path: Path):
        """存在しない.envファイルを指定した場合"""
        with pytest.raises(FileNotFoundError) as exc_info:
            _load_env_files(str(tmp_path / "nonexistent.env"))

        assert "指定された環境変数ファイルが見つかりません" in str(exc_info.value)

    def test_load_local_env_file(self, tmp_path: Path, monkeypatch):
        """カレントディレクトリの.envファイルの読み込み"""
        env_file = tmp_path / ".env"
        env_file.write_text("LOCAL_VAR=local_value\n")

        monkeypatch.chdir(tmp_path)

        with patch.dict(os.environ, {}, clear=True):
            _load_env_files(None)
            # ファイルが存在すれば読み込みが試行される

    def test_no_env_file_found(self, tmp_path: Path, monkeypatch):
        """どの.envファイルも見つからない場合"""
        monkeypatch.chdir(tmp_path)

        with patch.dict(os.environ, {}, clear=True):
            # エラーにならずに完了すること
            _load_env_files(None)


class TestBacklogClient:
    """BacklogClient クラスのテスト"""

    def test_init_with_arguments(self):
        """引数で認証情報を渡す場合"""
        client = BacklogClient(
            space_id="test-space",
            api_key="test-api-key",
            domain="backlog.jp"
        )

        assert client.space_id == "test-space"
        assert client.api_key == "test-api-key"
        assert client.domain == "backlog.jp"
        assert client.base_url == "https://test-space.backlog.jp/api/v2"

    def test_init_with_env_vars(self, monkeypatch):
        """環境変数で認証情報を渡す場合"""
        monkeypatch.setenv("BACKLOG_SPACE_ID", "env-space")
        monkeypatch.setenv("BACKLOG_API_KEY", "env-api-key")
        monkeypatch.setenv("BACKLOG_DOMAIN", "backlog.com")

        client = BacklogClient()

        assert client.space_id == "env-space"
        assert client.api_key == "env-api-key"
        assert client.domain == "backlog.com"

    def test_init_missing_space_id(self, monkeypatch):
        """スペースIDが設定されていない場合"""
        monkeypatch.delenv("BACKLOG_SPACE_ID", raising=False)
        monkeypatch.delenv("BACKLOG_API_KEY", raising=False)

        with pytest.raises(ValueError) as exc_info:
            BacklogClient()

        assert "BACKLOG_SPACE_ID が設定されていません" in str(exc_info.value)

    def test_init_missing_api_key(self, monkeypatch):
        """APIキーが設定されていない場合"""
        monkeypatch.setenv("BACKLOG_SPACE_ID", "test-space")
        monkeypatch.delenv("BACKLOG_API_KEY", raising=False)

        with pytest.raises(ValueError) as exc_info:
            BacklogClient()

        assert "BACKLOG_API_KEY が設定されていません" in str(exc_info.value)

    def test_init_default_domain(self, monkeypatch):
        """ドメインのデフォルト値"""
        monkeypatch.setenv("BACKLOG_SPACE_ID", "test-space")
        monkeypatch.setenv("BACKLOG_API_KEY", "test-api-key")
        monkeypatch.delenv("BACKLOG_DOMAIN", raising=False)

        client = BacklogClient()

        assert client.domain == "backlog.jp"

    def test_argument_priority_over_env(self, monkeypatch):
        """引数が環境変数より優先される"""
        monkeypatch.setenv("BACKLOG_SPACE_ID", "env-space")
        monkeypatch.setenv("BACKLOG_API_KEY", "env-api-key")

        client = BacklogClient(
            space_id="arg-space",
            api_key="arg-api-key"
        )

        assert client.space_id == "arg-space"
        assert client.api_key == "arg-api-key"


class TestBacklogClientRequests:
    """BacklogClient のAPIリクエストテスト"""

    @pytest.fixture
    def client(self):
        """テスト用クライアント"""
        return BacklogClient(
            space_id="test-space",
            api_key="test-api-key"
        )

    @patch("gospelo_backlog_docs.backlog_client.requests.request")
    def test_request_success(self, mock_request, client):
        """正常なAPIリクエスト"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {"id": 1, "name": "test"}
        mock_request.return_value = mock_response

        result = client._request("GET", "/test")

        assert result == {"id": 1, "name": "test"}
        mock_request.assert_called_once()

    @patch("gospelo_backlog_docs.backlog_client.requests.request")
    def test_request_api_error(self, mock_request, client):
        """APIエラーレスポンス"""
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 400
        mock_response.json.return_value = {"errors": [{"message": "Bad Request"}]}
        mock_request.return_value = mock_response

        with pytest.raises(Exception) as exc_info:
            client._request("GET", "/test")

        assert "API Error: 400" in str(exc_info.value)

    @patch("gospelo_backlog_docs.backlog_client.requests.request")
    def test_upload_attachment(self, mock_request, client, tmp_path: Path):
        """添付ファイルアップロード"""
        # テストファイル作成
        test_file = tmp_path / "test.png"
        test_file.write_bytes(b"fake png data")

        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "id": 12345,
            "name": "test.png",
            "size": 13
        }
        mock_request.return_value = mock_response

        result = client.upload_attachment(test_file)

        assert isinstance(result, Attachment)
        assert result.id == 12345
        assert result.name == "test.png"
        assert result.size == 13

    @patch("gospelo_backlog_docs.backlog_client.requests.request")
    def test_get_wiki_list(self, mock_request, client):
        """Wiki一覧取得"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = [
            {"id": 1, "name": "Wiki1"},
            {"id": 2, "name": "Wiki2"}
        ]
        mock_request.return_value = mock_response

        result = client.get_wiki_list("PROJECT")

        assert len(result) == 2
        assert result[0]["name"] == "Wiki1"

    @patch("gospelo_backlog_docs.backlog_client.requests.request")
    def test_get_wiki(self, mock_request, client):
        """Wiki取得"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "id": 1,
            "projectId": 100,
            "name": "Test Wiki",
            "content": "# Content",
            "tags": [{"name": "tag1"}],
            "created": "2025-01-01T00:00:00Z",
            "updated": "2025-01-02T00:00:00Z"
        }
        mock_request.return_value = mock_response

        result = client.get_wiki(1)

        assert isinstance(result, WikiPage)
        assert result.id == 1
        assert result.name == "Test Wiki"
        assert result.tags == ["tag1"]

    @patch("gospelo_backlog_docs.backlog_client.requests.request")
    def test_create_wiki(self, mock_request, client):
        """Wiki作成"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "id": 123,
            "projectId": 100,
            "name": "New Wiki",
            "content": "# New Content",
            "tags": [],
            "created": "2025-01-01T00:00:00Z",
            "updated": "2025-01-01T00:00:00Z"
        }
        mock_request.return_value = mock_response

        result = client.create_wiki(
            project_id=100,
            name="New Wiki",
            content="# New Content"
        )

        assert isinstance(result, WikiPage)
        assert result.id == 123
        assert result.name == "New Wiki"

    @patch("gospelo_backlog_docs.backlog_client.requests.request")
    def test_update_wiki(self, mock_request, client):
        """Wiki更新"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "id": 123,
            "projectId": 100,
            "name": "Updated Wiki",
            "content": "# Updated Content",
            "tags": [],
            "created": "2025-01-01T00:00:00Z",
            "updated": "2025-01-02T00:00:00Z"
        }
        mock_request.return_value = mock_response

        result = client.update_wiki(
            wiki_id=123,
            content="# Updated Content"
        )

        assert isinstance(result, WikiPage)
        assert result.content == "# Updated Content"

    @patch("gospelo_backlog_docs.backlog_client.requests.request")
    def test_attach_files_to_wiki(self, mock_request, client):
        """Wikiへの添付ファイル紐付け"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = [
            {"id": 1001, "name": "file1.png"},
            {"id": 1002, "name": "file2.png"}
        ]
        mock_request.return_value = mock_response

        result = client.attach_files_to_wiki(123, [101, 102])

        assert len(result) == 2
        assert result[0]["id"] == 1001


class TestWikiPage:
    """WikiPage データクラスのテスト"""

    def test_wiki_page_creation(self):
        """WikiPageの生成"""
        wiki = WikiPage(
            id=1,
            project_id=100,
            name="Test",
            content="# Content",
            tags=["tag1", "tag2"],
            created="2025-01-01",
            updated="2025-01-02"
        )

        assert wiki.id == 1
        assert wiki.project_id == 100
        assert wiki.name == "Test"
        assert len(wiki.tags) == 2


class TestAttachment:
    """Attachment データクラスのテスト"""

    def test_attachment_creation(self):
        """Attachmentの生成"""
        attachment = Attachment(
            id=12345,
            name="image.png",
            size=1024
        )

        assert attachment.id == 12345
        assert attachment.name == "image.png"
        assert attachment.size == 1024


class TestGetAttachmentUrl:
    """get_attachment_url 関数のテスト"""

    def test_default_domain(self):
        """デフォルトドメインでのURL生成"""
        url = get_attachment_url("myspace", 12345)
        assert url == "https://myspace.backlog.jp/ViewWikiAttachment.action?attachmentId=12345"

    def test_custom_domain(self):
        """カスタムドメインでのURL生成"""
        url = get_attachment_url("myspace", 12345, domain="backlog.com")
        assert url == "https://myspace.backlog.com/ViewWikiAttachment.action?attachmentId=12345"
