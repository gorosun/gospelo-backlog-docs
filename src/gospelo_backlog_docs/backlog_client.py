#!/usr/bin/env python3
"""
Backlog APIクライアント
- Wiki ページの作成・更新
- 添付ファイルのアップロード
"""

import logging
import os
import requests
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# グローバル設定ディレクトリ
CONFIG_DIR = Path.home() / '.config' / 'gospelo-backlog-docs'


def _load_env_files(env_file: Optional[str] = None) -> None:
    """
    優先順位に従って.envファイルを読み込み

    優先順位:
    1. 明示的に指定されたファイル（最優先）
    2. カレントディレクトリの .env
    3. グローバル設定ディレクトリ ~/.config/gospelo-backlog-docs/.env
    """
    # 1. 明示的に指定されたファイル（最優先）
    if env_file:
        env_path = Path(env_file)
        if env_path.exists():
            logger.debug(f"Loading environment from explicit file: {env_file}")
            load_dotenv(env_file, override=False)
            return
        else:
            raise FileNotFoundError(f"指定された環境変数ファイルが見つかりません: {env_file}")

    # 2. カレントディレクトリの .env
    local_env = Path('.env')
    if local_env.exists():
        logger.debug(f"Loading environment from project .env: {local_env.absolute()}")
        load_dotenv(local_env, override=False)
        return

    # 3. グローバル設定ディレクトリ
    global_env = CONFIG_DIR / '.env'
    if global_env.exists():
        logger.debug(f"Loading environment from global config: {global_env}")
        load_dotenv(global_env, override=False)
        return

    logger.debug("No .env file found, using environment variables only")


@dataclass
class WikiPage:
    """Wikiページ情報"""
    id: int
    project_id: int
    name: str
    content: str
    tags: list[str]
    created: str
    updated: str


@dataclass
class Attachment:
    """添付ファイル情報"""
    id: int
    name: str
    size: int


class BacklogClient:
    """Backlog APIクライアント"""

    def __init__(
        self,
        space_id: Optional[str] = None,
        api_key: Optional[str] = None,
        env_file: Optional[str] = None,
        domain: Optional[str] = None
    ):
        """
        Args:
            space_id: BacklogスペースID (例: 'mycompany')
            api_key: Backlog APIキー
            env_file: 環境変数ファイルパス
            domain: Backlogドメイン (例: 'backlog.jp' or 'backlog.com')

        認証情報の優先順位:
            1. コマンドライン引数（最優先）
            2. 環境変数
            3. .envファイル（カレントディレクトリ）
            4. グローバル設定ファイル（~/.config/gospelo-backlog-docs/.env）
        """
        # 環境変数ファイルを読み込み（override=Falseで既存の環境変数を尊重）
        _load_env_files(env_file)

        # 優先順位: 引数 > 環境変数 > デフォルト値
        self.space_id = space_id or os.getenv('BACKLOG_SPACE_ID')
        self.api_key = api_key or os.getenv('BACKLOG_API_KEY')
        self.domain = domain or os.getenv('BACKLOG_DOMAIN', 'backlog.jp')

        if not self.space_id:
            raise ValueError(
                "BACKLOG_SPACE_ID が設定されていません。\n"
                "以下のいずれかの方法で設定してください:\n"
                "  1. --space-id 引数で指定\n"
                "  2. BACKLOG_SPACE_ID 環境変数を設定\n"
                "  3. .env ファイルに BACKLOG_SPACE_ID を記述\n"
                f"  4. {CONFIG_DIR}/.env にグローバル設定を作成"
            )
        if not self.api_key:
            raise ValueError(
                "BACKLOG_API_KEY が設定されていません。\n"
                "以下のいずれかの方法で設定してください:\n"
                "  1. --api-key 引数で指定\n"
                "  2. BACKLOG_API_KEY 環境変数を設定\n"
                "  3. .env ファイルに BACKLOG_API_KEY を記述\n"
                f"  4. {CONFIG_DIR}/.env にグローバル設定を作成"
            )

        self.base_url = f"https://{self.space_id}.{self.domain}/api/v2"

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict] = None,
        data: Optional[dict] = None,
        files: Optional[dict] = None
    ) -> dict | list:
        """APIリクエストを実行"""
        url = f"{self.base_url}{endpoint}"

        # APIキーをパラメータに追加
        if params is None:
            params = {}
        params['apiKey'] = self.api_key

        response = requests.request(
            method=method,
            url=url,
            params=params,
            data=data,
            files=files
        )

        if not response.ok:
            error_msg = f"API Error: {response.status_code}"
            try:
                error_detail = response.json()
                error_msg += f" - {error_detail}"
            except:
                error_msg += f" - {response.text}"
            raise Exception(error_msg)

        return response.json()

    # ========== 添付ファイル ==========

    def upload_attachment(self, file_path: str | Path) -> Attachment:
        """
        添付ファイルをアップロード

        Args:
            file_path: アップロードするファイルのパス

        Returns:
            Attachment情報
        """
        file_path = Path(file_path)

        with open(file_path, 'rb') as f:
            files = {'file': (file_path.name, f)}
            result = self._request('POST', '/space/attachment', files=files)

        return Attachment(
            id=result['id'],
            name=result['name'],
            size=result['size']
        )

    def upload_attachments(self, file_paths: list[str | Path]) -> list[Attachment]:
        """
        複数の添付ファイルをアップロード

        Args:
            file_paths: ファイルパスのリスト

        Returns:
            Attachment情報のリスト
        """
        return [self.upload_attachment(fp) for fp in file_paths]

    # ========== Wiki ==========

    def get_wiki_list(self, project_id_or_key: str | int) -> list[dict]:
        """
        Wikiページ一覧を取得

        Args:
            project_id_or_key: プロジェクトIDまたはキー

        Returns:
            Wikiページ一覧
        """
        return self._request(
            'GET',
            '/wikis',
            params={'projectIdOrKey': project_id_or_key}
        )

    def get_wiki(self, wiki_id: int) -> WikiPage:
        """
        Wikiページを取得

        Args:
            wiki_id: WikiページID

        Returns:
            WikiPage情報
        """
        result = self._request('GET', f'/wikis/{wiki_id}')
        return WikiPage(
            id=result['id'],
            project_id=result['projectId'],
            name=result['name'],
            content=result['content'],
            tags=[t['name'] for t in result.get('tags', [])],
            created=result['created'],
            updated=result['updated']
        )

    def find_wiki_by_name(
        self,
        project_id_or_key: str | int,
        name: str
    ) -> Optional[WikiPage]:
        """
        名前でWikiページを検索

        Args:
            project_id_or_key: プロジェクトIDまたはキー
            name: ページ名

        Returns:
            WikiPage情報 (見つからない場合はNone)
        """
        wiki_list = self.get_wiki_list(project_id_or_key)
        for wiki in wiki_list:
            if wiki['name'] == name:
                return self.get_wiki(wiki['id'])
        return None

    def create_wiki(
        self,
        project_id: int,
        name: str,
        content: str,
        mail_notify: bool = False
    ) -> WikiPage:
        """
        Wikiページを作成

        Args:
            project_id: プロジェクトID
            name: ページ名
            content: コンテンツ (Markdown)
            mail_notify: メール通知を送信するか

        Returns:
            作成されたWikiPage情報
        """
        data = {
            'projectId': project_id,
            'name': name,
            'content': content,
            'mailNotify': 'true' if mail_notify else 'false'
        }

        result = self._request('POST', '/wikis', data=data)

        return WikiPage(
            id=result['id'],
            project_id=result['projectId'],
            name=result['name'],
            content=result['content'],
            tags=[t['name'] for t in result.get('tags', [])],
            created=result['created'],
            updated=result['updated']
        )

    def update_wiki(
        self,
        wiki_id: int,
        name: Optional[str] = None,
        content: Optional[str] = None,
        mail_notify: bool = False
    ) -> WikiPage:
        """
        Wikiページを更新

        Args:
            wiki_id: WikiページID
            name: 新しいページ名 (Noneの場合は変更なし)
            content: 新しいコンテンツ (Noneの場合は変更なし)
            mail_notify: メール通知を送信するか

        Returns:
            更新されたWikiPage情報
        """
        data = {'mailNotify': 'true' if mail_notify else 'false'}
        if name is not None:
            data['name'] = name
        if content is not None:
            data['content'] = content

        result = self._request('PATCH', f'/wikis/{wiki_id}', data=data)

        return WikiPage(
            id=result['id'],
            project_id=result['projectId'],
            name=result['name'],
            content=result['content'],
            tags=[t['name'] for t in result.get('tags', [])],
            created=result['created'],
            updated=result['updated']
        )

    def attach_files_to_wiki(
        self,
        wiki_id: int,
        attachment_ids: list[int]
    ) -> list[dict]:
        """
        Wikiページに添付ファイルを紐付け

        Args:
            wiki_id: WikiページID
            attachment_ids: 添付ファイルIDのリスト

        Returns:
            添付ファイル情報のリスト
        """
        data = {'attachmentId[]': attachment_ids}
        return self._request('POST', f'/wikis/{wiki_id}/attachments', data=data)

    def create_or_update_wiki(
        self,
        project_id_or_key: str | int,
        name: str,
        content: str,
        mail_notify: bool = False
    ) -> tuple[WikiPage, bool]:
        """
        Wikiページを作成または更新

        Args:
            project_id_or_key: プロジェクトIDまたはキー
            name: ページ名
            content: コンテンツ
            mail_notify: メール通知を送信するか

        Returns:
            (WikiPage情報, 新規作成かどうか)
        """
        existing = self.find_wiki_by_name(project_id_or_key, name)

        if existing:
            updated = self.update_wiki(
                wiki_id=existing.id,
                content=content,
                mail_notify=mail_notify
            )
            return updated, False
        else:
            # project_id_or_key が文字列の場合、プロジェクトIDを取得する必要がある
            if isinstance(project_id_or_key, str):
                project_info = self._request(
                    'GET',
                    f'/projects/{project_id_or_key}'
                )
                project_id = project_info['id']
            else:
                project_id = project_id_or_key

            created = self.create_wiki(
                project_id=project_id,
                name=name,
                content=content,
                mail_notify=mail_notify
            )
            return created, True

    # ========== プロジェクト ==========

    def get_project(self, project_id_or_key: str | int) -> dict:
        """
        プロジェクト情報を取得

        Args:
            project_id_or_key: プロジェクトIDまたはキー

        Returns:
            プロジェクト情報
        """
        return self._request('GET', f'/projects/{project_id_or_key}')


def get_attachment_url(space_id: str, attachment_id: int, domain: str = 'backlog.jp') -> str:
    """
    添付ファイルのURLを生成

    Args:
        space_id: BacklogスペースID
        attachment_id: 添付ファイルID
        domain: Backlogドメイン (デフォルト: 'backlog.jp')

    Returns:
        添付ファイルのURL
    """
    return f"https://{space_id}.{domain}/ViewWikiAttachment.action?attachmentId={attachment_id}"


if __name__ == '__main__':
    import sys

    # 接続テスト
    print("Backlog API接続テスト...")

    try:
        client = BacklogClient()
        print(f"✓ スペースID: {client.space_id}")
        print(f"✓ APIキー: {client.api_key[:10]}...")

        # プロジェクト一覧は取得しない (権限が必要な場合があるため)
        print("✓ クライアント初期化成功")

    except Exception as e:
        print(f"✗ エラー: {e}")
        sys.exit(1)
