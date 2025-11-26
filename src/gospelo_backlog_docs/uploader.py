#!/usr/bin/env python3
"""
Backlog Wikiアップローダー

画面設計書(Markdown)をBacklog Wikiにアップロード
- 埋め込み画像を自動アップロード
- MermaidJS図をPNG変換してアップロード
- 画像パスをBacklog URLに置換
"""

import hashlib
import re
from pathlib import Path
from typing import Optional

from .markdown_parser import MarkdownParser, ImageReference, MermaidBlock
from .mermaid_converter import MermaidConverter, check_mermaid_cli_installed
from .backlog_client import BacklogClient, Attachment, get_attachment_url


def remove_emojis(text: str) -> str:
    """
    テキストから絵文字を除去（Backlog APIが絵文字を受け付けないため）

    Args:
        text: 入力テキスト

    Returns:
        絵文字を除去したテキスト
    """
    # 日本語文字に影響しない、限定的な絵文字パターン
    # 主にサロゲートペア領域（U+1F000以上）の絵文字のみを対象
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons (顔文字)
        "\U0001F300-\U0001F5FF"  # symbols & pictographs (記号・絵文字)
        "\U0001F680-\U0001F6FF"  # transport & map symbols (乗り物・地図)
        "\U0001F1E0-\U0001F1FF"  # flags (国旗)
        "\U0001F900-\U0001F9FF"  # supplemental symbols (追加記号)
        "\U0001FA00-\U0001FA6F"  # chess symbols (チェス記号)
        "\U0001FA70-\U0001FAFF"  # symbols extended-A (拡張記号)
        "\U0001F004-\U0001F0CF"  # mahjong, playing cards (麻雀・トランプ)
        "]+",
        flags=re.UNICODE
    )
    return emoji_pattern.sub('', text)


class WikiUploader:
    """Wiki アップローダー"""

    def __init__(
        self,
        project_key: str,
        space_id: Optional[str] = None,
        api_key: Optional[str] = None,
        domain: Optional[str] = None,
        env_file: Optional[str] = None
    ):
        """
        Args:
            project_key: Backlogプロジェクトキー
            space_id: BacklogスペースID
            api_key: Backlog APIキー
            domain: Backlogドメイン (例: 'backlog.jp')
            env_file: 環境変数ファイルパス
        """
        self.project_key = project_key
        self.client = BacklogClient(
            space_id=space_id,
            api_key=api_key,
            domain=domain,
            env_file=env_file
        )
        self.mermaid_converter: Optional[MermaidConverter] = None

        # MermaidJS変換が可能か確認
        self.mermaid_available = check_mermaid_cli_installed()
        if not self.mermaid_available:
            print("警告: mermaid-cli (mmdc) が見つかりません。MermaidJS図は変換されません。")

    def _generate_mermaid_filename(self, code: str, index: int) -> str:
        """MermaidJSコードからファイル名を生成"""
        # コードのハッシュを使ってユニークな名前を生成
        hash_suffix = hashlib.md5(code.encode()).hexdigest()[:8]
        return f"mermaid_{index}_{hash_suffix}"

    def _convert_mermaid_blocks(
        self,
        blocks: list[MermaidBlock],
        output_dir: Path
    ) -> list[tuple[MermaidBlock, Path]]:
        """
        MermaidJSブロックをPNG画像に変換

        Args:
            blocks: MermaidBlockのリスト
            output_dir: 出力ディレクトリ

        Returns:
            (MermaidBlock, 生成された画像パス) のタプルリスト
        """
        if not self.mermaid_available or not blocks:
            return []

        if not self.mermaid_converter:
            self.mermaid_converter = MermaidConverter(output_dir=output_dir)

        results = []
        for i, block in enumerate(blocks):
            filename = self._generate_mermaid_filename(block.code, i)
            result = self.mermaid_converter.convert(
                mermaid_code=block.code,
                output_name=filename,
                format='png'
            )

            if result.success and result.output_path:
                results.append((block, result.output_path))
                print(f"  ✓ MermaidJS図 {i+1} を変換: {result.output_path.name}")
            else:
                print(f"  ✗ MermaidJS図 {i+1} の変換に失敗: {result.error_message}")

        return results

    def upload(
        self,
        markdown_path: str,
        wiki_name: Optional[str] = None,
        dry_run: bool = False
    ) -> dict:
        """
        MarkdownファイルをBacklog Wikiにアップロード

        Args:
            markdown_path: Markdownファイルのパス
            wiki_name: Wikiページ名 (Noneの場合はファイル名から生成)
            dry_run: Trueの場合、実際のアップロードは行わない

        Returns:
            アップロード結果の辞書
        """
        markdown_path = Path(markdown_path)

        if not markdown_path.exists():
            raise FileNotFoundError(f"ファイルが見つかりません: {markdown_path}")

        # Markdownを解析
        parser = MarkdownParser(str(markdown_path))

        # Wikiページ名を決定（優先順位: 引数 > H1タイトル > ファイル名）
        if wiki_name is None:
            h1_title = parser.extract_h1_title()
            if h1_title:
                wiki_name = h1_title
            else:
                wiki_name = markdown_path.stem

        print(f"\n{'='*60}")
        print(f"Backlog Wiki アップロード")
        print(f"{'='*60}")
        print(f"ファイル: {markdown_path}")
        print(f"プロジェクト: {self.project_key}")
        print(f"Wiki名: {wiki_name}")
        print(f"{'='*60}\n")

        print("1. Markdownファイルを解析中...")
        images = parser.get_all_local_images()
        mermaid_blocks = parser.extract_mermaid_blocks()

        print(f"   - ローカル画像: {len(images)} 件")
        print(f"   - MermaidJS図: {len(mermaid_blocks)} 件")

        # MermaidJS図を変換
        temp_dir = markdown_path.parent / '.mermaid_temp'
        mermaid_images: list[tuple[MermaidBlock, Path]] = []

        if mermaid_blocks and self.mermaid_available:
            print("\n2. MermaidJS図を変換中...")
            temp_dir.mkdir(exist_ok=True)
            mermaid_images = self._convert_mermaid_blocks(mermaid_blocks, temp_dir)

        if dry_run:
            print("\n[DRY RUN] 実際のアップロードはスキップします")
            return {
                'wiki_name': wiki_name,
                'local_images': len(images),
                'mermaid_images': len(mermaid_images),
                'dry_run': True
            }

        # 画像をアップロード
        print("\n3. 画像をアップロード中...")
        # パスベースでアップロード済み画像を管理（重複アップロード防止）
        uploaded_by_path: dict[str, Attachment] = {}
        # original_text -> Attachment のマッピング（置換用）
        uploaded_attachments: dict[str, Attachment] = {}

        # ローカル画像をアップロード（同一パスは1回だけ）
        for img_ref, img_path in images:
            path_key = str(img_path)
            try:
                if path_key not in uploaded_by_path:
                    # 新規アップロード
                    attachment = self.client.upload_attachment(img_path)
                    uploaded_by_path[path_key] = attachment
                    print(f"   ✓ {img_path.name} (ID: {attachment.id})")
                else:
                    # 既にアップロード済み
                    attachment = uploaded_by_path[path_key]
                    print(f"   ✓ {img_path.name} (既存ID: {attachment.id}を再利用)")

                uploaded_attachments[img_ref.original_text] = attachment
            except Exception as e:
                print(f"   ✗ {img_path.name}: {e}")

        # MermaidJS画像をアップロード
        mermaid_attachments: dict[str, Attachment] = {}
        for block, img_path in mermaid_images:
            try:
                attachment = self.client.upload_attachment(img_path)
                mermaid_attachments[block.original_text] = attachment
                print(f"   ✓ {img_path.name} (ID: {attachment.id})")
            except Exception as e:
                print(f"   ✗ {img_path.name}: {e}")

        # Wikiページを作成/更新（まずプレースホルダーで作成）
        print("\n4. Wikiページを作成/更新中...")

        # コンテンツから絵文字を除去（Backlog APIが絵文字を受け付けないため）
        clean_content = remove_emojis(parser.content)

        # 最初は元のコンテンツでWikiを作成（画像参照はそのまま）
        wiki_page, is_new = self.client.create_or_update_wiki(
            project_id_or_key=self.project_key,
            name=wiki_name,
            content=clean_content
        )

        action = "作成" if is_new else "更新"
        print(f"   ✓ Wikiページを{action}しました (ID: {wiki_page.id})")

        # 添付ファイルをWikiに紐付け（重複IDを排除）
        unique_attachment_ids = list(set(
            [a.id for a in uploaded_attachments.values()] +
            [a.id for a in mermaid_attachments.values()]
        ))
        all_attachment_ids = unique_attachment_ids

        # 元のファイル名と新しいattachmentIdのマッピング
        filename_to_new_attachment_id: dict[str, int] = {}

        if all_attachment_ids:
            print("\n5. 添付ファイルをWikiに紐付け中...")
            try:
                # 紐付け結果から新しいattachmentIdを取得
                attached_files = self.client.attach_files_to_wiki(wiki_page.id, all_attachment_ids)
                print(f"   ✓ {len(all_attachment_ids)} 件の添付ファイルを紐付けました")

                # 新しいattachmentIdをファイル名でマッピング
                for attached in attached_files:
                    filename_to_new_attachment_id[attached['name']] = attached['id']
                    print(f"   - {attached['name']} -> attachmentId: {attached['id']}")

            except Exception as e:
                print(f"   ✗ 添付ファイルの紐付けに失敗: {e}")

        # 新しいattachmentIdでコンテンツを更新
        if filename_to_new_attachment_id:
            print("\n6. 画像参照を更新中...")
            # 元のコンテンツから画像参照を置換してから絵文字除去する
            content = parser.content
            replacement_count = 0

            # ローカル画像参照をBacklog記法 ![image][ファイル名] に置換
            for original_text, attachment in uploaded_attachments.items():
                new_attachment_id = filename_to_new_attachment_id.get(attachment.name)
                if new_attachment_id:
                    # Backlog Wiki独自記法: ![image][ファイル名]
                    backlog_image_tag = f"![image][{attachment.name}]"
                    # 置換回数をカウント
                    count = content.count(original_text)
                    if count > 0:
                        content = content.replace(original_text, backlog_image_tag)
                        replacement_count += count
                        if count > 1:
                            print(f"   - {attachment.name}: {count}箇所を置換")

            # MermaidJSブロックをBacklog記法に置換
            for block_text, attachment in mermaid_attachments.items():
                new_attachment_id = filename_to_new_attachment_id.get(attachment.name)
                if new_attachment_id:
                    # Backlog Wiki独自記法: ![image][ファイル名]
                    backlog_image_tag = f"![image][{attachment.name}]"
                    count = content.count(block_text)
                    if count > 0:
                        content = content.replace(block_text, backlog_image_tag)
                        replacement_count += count

            # 置換後に絵文字を除去
            content = remove_emojis(content)

            # Wikiページを更新
            self.client.update_wiki(wiki_id=wiki_page.id, content=content)
            print(f"   ✓ 画像参照を更新しました（計 {replacement_count} 箇所）")

        # 一時ディレクトリをクリーンアップ
        if temp_dir.exists():
            import shutil
            shutil.rmtree(temp_dir)

        # 結果を出力
        wiki_url = f"https://{self.client.space_id}.{self.client.domain}/wiki/{self.project_key}/{wiki_name}"

        print(f"\n{'='*60}")
        print(f"✓ アップロード完了!")
        print(f"{'='*60}")
        print(f"Wiki URL: {wiki_url}")
        print(f"{'='*60}\n")

        return {
            'wiki_id': wiki_page.id,
            'wiki_name': wiki_name,
            'wiki_url': wiki_url,
            'is_new': is_new,
            'local_images_uploaded': len(uploaded_attachments),
            'mermaid_images_uploaded': len(mermaid_attachments),
            'total_attachments': len(all_attachment_ids)
        }
