#!/usr/bin/env python3
"""
Markdown解析モジュール
- 画像パスの抽出
- MermaidJSコードブロックの抽出
- パス置換処理
"""

import re
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


@dataclass
class ImageReference:
    """画像参照情報"""
    original_text: str  # 元のMarkdownテキスト (例: ![alt](path))
    alt_text: str       # 代替テキスト
    path: str           # 画像パス
    start_pos: int      # 開始位置
    end_pos: int        # 終了位置


@dataclass
class MermaidBlock:
    """MermaidJSコードブロック情報"""
    original_text: str  # 元のコードブロック全体
    code: str           # Mermaidコード本体
    start_pos: int      # 開始位置
    end_pos: int        # 終了位置


class MarkdownParser:
    """Markdownファイル解析クラス"""

    # 画像参照パターン: ![alt text](image/path.png)
    IMAGE_PATTERN = re.compile(
        r'!\[([^\]]*)\]\(([^)]+)\)',
        re.MULTILINE
    )

    # MermaidJSコードブロックパターン
    MERMAID_PATTERN = re.compile(
        r'```mermaid\s*\n(.*?)\n```',
        re.DOTALL | re.MULTILINE
    )

    # H1タイトルパターン: # タイトル
    H1_PATTERN = re.compile(
        r'^#\s+(.+)$',
        re.MULTILINE
    )

    def __init__(self, markdown_path: str):
        """
        Args:
            markdown_path: Markdownファイルのパス
        """
        self.markdown_path = Path(markdown_path)
        self.base_dir = self.markdown_path.parent
        self.content = self._read_file()

    def _read_file(self) -> str:
        """ファイルを読み込む"""
        with open(self.markdown_path, 'r', encoding='utf-8') as f:
            return f.read()

    def extract_images(self) -> list[ImageReference]:
        """
        Markdownから画像参照を抽出

        Returns:
            ImageReference のリスト
        """
        images = []
        for match in self.IMAGE_PATTERN.finditer(self.content):
            images.append(ImageReference(
                original_text=match.group(0),
                alt_text=match.group(1),
                path=match.group(2),
                start_pos=match.start(),
                end_pos=match.end()
            ))
        return images

    def extract_mermaid_blocks(self) -> list[MermaidBlock]:
        """
        MarkdownからMermaidJSコードブロックを抽出

        Returns:
            MermaidBlock のリスト
        """
        blocks = []
        for match in self.MERMAID_PATTERN.finditer(self.content):
            blocks.append(MermaidBlock(
                original_text=match.group(0),
                code=match.group(1).strip(),
                start_pos=match.start(),
                end_pos=match.end()
            ))
        return blocks

    def resolve_image_path(self, image_ref: ImageReference) -> Optional[Path]:
        """
        画像の相対パスを絶対パスに解決

        Args:
            image_ref: 画像参照情報

        Returns:
            解決された絶対パス (存在しない場合はNone)
        """
        # URLの場合はスキップ
        if image_ref.path.startswith(('http://', 'https://', '//')):
            return None

        # 相対パスを解決
        resolved = (self.base_dir / image_ref.path).resolve()

        if resolved.exists():
            return resolved
        return None

    def replace_content(self, replacements: dict[str, str]) -> str:
        """
        コンテンツ内のテキストを置換

        Args:
            replacements: {元のテキスト: 置換後のテキスト} の辞書

        Returns:
            置換後のコンテンツ
        """
        result = self.content
        for original, replacement in replacements.items():
            result = result.replace(original, replacement)
        return result

    def get_all_local_images(self) -> list[tuple[ImageReference, Path]]:
        """
        ローカルに存在する全画像を取得

        Returns:
            (ImageReference, 絶対パス) のタプルリスト
        """
        results = []
        for img in self.extract_images():
            resolved = self.resolve_image_path(img)
            if resolved:
                results.append((img, resolved))
        return results

    def extract_h1_title(self) -> Optional[str]:
        """
        MarkdownからH1タイトル（最初の # で始まる行）を抽出

        Returns:
            H1タイトル (見つからない場合はNone)
        """
        match = self.H1_PATTERN.search(self.content)
        if match:
            return match.group(1).strip()
        return None


def analyze_markdown(markdown_path: str) -> dict:
    """
    Markdownファイルを分析してサマリーを返す

    Args:
        markdown_path: Markdownファイルのパス

    Returns:
        分析結果の辞書
    """
    parser = MarkdownParser(markdown_path)

    images = parser.extract_images()
    local_images = parser.get_all_local_images()
    mermaid_blocks = parser.extract_mermaid_blocks()

    return {
        'file': str(parser.markdown_path),
        'total_images': len(images),
        'local_images': len(local_images),
        'external_images': len(images) - len(local_images),
        'mermaid_blocks': len(mermaid_blocks),
        'images': [
            {
                'alt': img.alt_text,
                'path': img.path,
                'exists': parser.resolve_image_path(img) is not None
            }
            for img in images
        ],
        'mermaid_previews': [
            block.code[:100] + '...' if len(block.code) > 100 else block.code
            for block in mermaid_blocks
        ]
    }


if __name__ == '__main__':
    import sys
    import json

    if len(sys.argv) < 2:
        print("Usage: python markdown_parser.py <markdown_file>")
        sys.exit(1)

    result = analyze_markdown(sys.argv[1])
    print(json.dumps(result, indent=2, ensure_ascii=False))
