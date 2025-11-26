"""Tests for markdown_parser module."""

import pytest
from pathlib import Path
import tempfile
import os

from gospelo_backlog_docs.markdown_parser import (
    MarkdownParser,
    ImageReference,
    MermaidBlock,
    analyze_markdown,
)


class TestMarkdownParser:
    """MarkdownParser クラスのテスト"""

    @pytest.fixture
    def sample_markdown(self, tmp_path: Path) -> Path:
        """テスト用Markdownファイルを作成"""
        content = """# テストドキュメント

これはテストです。

## 画像セクション

![画像1](./images/test1.png)
![画像2](../assets/test2.jpg)
![外部画像](https://example.com/image.png)

## Mermaidセクション

```mermaid
graph TD
    A[Start] --> B[End]
```

通常のコードブロック:

```python
print("Hello")
```

別のMermaid:

```mermaid
sequenceDiagram
    Alice->>Bob: Hello
```
"""
        md_file = tmp_path / "test.md"
        md_file.write_text(content, encoding="utf-8")
        return md_file

    @pytest.fixture
    def markdown_with_images(self, tmp_path: Path) -> Path:
        """実際の画像ファイルがあるMarkdownを作成"""
        # ディレクトリ構造を作成
        images_dir = tmp_path / "images"
        images_dir.mkdir()

        # ダミー画像ファイルを作成
        (images_dir / "existing.png").write_bytes(b"fake png data")

        content = """# 画像テスト

![存在する画像](./images/existing.png)
![存在しない画像](./images/missing.png)
![外部画像](https://example.com/image.png)
"""
        md_file = tmp_path / "test.md"
        md_file.write_text(content, encoding="utf-8")
        return md_file

    def test_extract_images(self, sample_markdown: Path):
        """画像参照の抽出テスト"""
        parser = MarkdownParser(str(sample_markdown))
        images = parser.extract_images()

        assert len(images) == 3
        assert images[0].alt_text == "画像1"
        assert images[0].path == "./images/test1.png"
        assert images[1].alt_text == "画像2"
        assert images[1].path == "../assets/test2.jpg"
        assert images[2].alt_text == "外部画像"
        assert images[2].path == "https://example.com/image.png"

    def test_extract_mermaid_blocks(self, sample_markdown: Path):
        """MermaidJSブロックの抽出テスト"""
        parser = MarkdownParser(str(sample_markdown))
        blocks = parser.extract_mermaid_blocks()

        assert len(blocks) == 2
        assert "graph TD" in blocks[0].code
        assert "sequenceDiagram" in blocks[1].code

    def test_extract_h1_title(self, sample_markdown: Path):
        """H1タイトルの抽出テスト"""
        parser = MarkdownParser(str(sample_markdown))
        title = parser.extract_h1_title()

        assert title == "テストドキュメント"

    def test_extract_h1_title_not_found(self, tmp_path: Path):
        """H1タイトルがない場合のテスト"""
        content = "## これはH2です\n\n本文"
        md_file = tmp_path / "no_h1.md"
        md_file.write_text(content, encoding="utf-8")

        parser = MarkdownParser(str(md_file))
        title = parser.extract_h1_title()

        assert title is None

    def test_resolve_image_path_local_exists(self, markdown_with_images: Path):
        """ローカル画像パスの解決テスト（存在する場合）"""
        parser = MarkdownParser(str(markdown_with_images))
        images = parser.extract_images()

        # 存在する画像
        resolved = parser.resolve_image_path(images[0])
        assert resolved is not None
        assert resolved.name == "existing.png"

    def test_resolve_image_path_local_not_exists(self, markdown_with_images: Path):
        """ローカル画像パスの解決テスト（存在しない場合）"""
        parser = MarkdownParser(str(markdown_with_images))
        images = parser.extract_images()

        # 存在しない画像
        resolved = parser.resolve_image_path(images[1])
        assert resolved is None

    def test_resolve_image_path_external(self, markdown_with_images: Path):
        """外部URL画像パスの解決テスト"""
        parser = MarkdownParser(str(markdown_with_images))
        images = parser.extract_images()

        # 外部URL
        resolved = parser.resolve_image_path(images[2])
        assert resolved is None

    def test_get_all_local_images(self, markdown_with_images: Path):
        """ローカル画像の一覧取得テスト"""
        parser = MarkdownParser(str(markdown_with_images))
        local_images = parser.get_all_local_images()

        assert len(local_images) == 1
        img_ref, path = local_images[0]
        assert img_ref.alt_text == "存在する画像"
        assert path.name == "existing.png"

    def test_replace_content(self, sample_markdown: Path):
        """コンテンツ置換テスト"""
        parser = MarkdownParser(str(sample_markdown))

        replacements = {
            "![画像1](./images/test1.png)": "![image][test1.png]",
            "![画像2](../assets/test2.jpg)": "![image][test2.jpg]",
        }

        result = parser.replace_content(replacements)

        assert "![image][test1.png]" in result
        assert "![image][test2.jpg]" in result
        assert "![外部画像](https://example.com/image.png)" in result


class TestImageReference:
    """ImageReference データクラスのテスト"""

    def test_image_reference_creation(self):
        """ImageReferenceの生成テスト"""
        ref = ImageReference(
            original_text="![alt](path.png)",
            alt_text="alt",
            path="path.png",
            start_pos=0,
            end_pos=16
        )

        assert ref.original_text == "![alt](path.png)"
        assert ref.alt_text == "alt"
        assert ref.path == "path.png"
        assert ref.start_pos == 0
        assert ref.end_pos == 16


class TestMermaidBlock:
    """MermaidBlock データクラスのテスト"""

    def test_mermaid_block_creation(self):
        """MermaidBlockの生成テスト"""
        block = MermaidBlock(
            original_text="```mermaid\ngraph TD\n```",
            code="graph TD",
            start_pos=0,
            end_pos=24
        )

        assert "mermaid" in block.original_text
        assert block.code == "graph TD"


class TestAnalyzeMarkdown:
    """analyze_markdown 関数のテスト"""

    def test_analyze_markdown(self, tmp_path: Path):
        """Markdown分析関数のテスト"""
        # テスト用ファイル作成
        images_dir = tmp_path / "images"
        images_dir.mkdir()
        (images_dir / "test.png").write_bytes(b"fake")

        content = """# 分析テスト

![ローカル](./images/test.png)
![外部](https://example.com/img.png)

```mermaid
graph LR
    A --> B
```
"""
        md_file = tmp_path / "analyze_test.md"
        md_file.write_text(content, encoding="utf-8")

        result = analyze_markdown(str(md_file))

        assert result["total_images"] == 2
        assert result["local_images"] == 1
        assert result["external_images"] == 1
        assert result["mermaid_blocks"] == 1
        assert len(result["images"]) == 2
        assert result["images"][0]["exists"] is True
        assert result["images"][1]["exists"] is False


class TestEdgeCases:
    """エッジケースのテスト"""

    def test_empty_markdown(self, tmp_path: Path):
        """空のMarkdownファイル"""
        md_file = tmp_path / "empty.md"
        md_file.write_text("", encoding="utf-8")

        parser = MarkdownParser(str(md_file))

        assert parser.extract_images() == []
        assert parser.extract_mermaid_blocks() == []
        assert parser.extract_h1_title() is None

    def test_markdown_with_only_text(self, tmp_path: Path):
        """画像やMermaidのないMarkdown"""
        content = """# タイトル

これは本文です。

## セクション

さらに本文。
"""
        md_file = tmp_path / "text_only.md"
        md_file.write_text(content, encoding="utf-8")

        parser = MarkdownParser(str(md_file))

        assert parser.extract_images() == []
        assert parser.extract_mermaid_blocks() == []
        assert parser.extract_h1_title() == "タイトル"

    def test_hierarchical_wiki_title(self, tmp_path: Path):
        """階層構造を含むWikiタイトル"""
        content = "# 画面設計/メンバー日次/MD0001 日次レポートタブ 画面仕様書\n\n本文"
        md_file = tmp_path / "hierarchical.md"
        md_file.write_text(content, encoding="utf-8")

        parser = MarkdownParser(str(md_file))
        title = parser.extract_h1_title()

        assert title == "画面設計/メンバー日次/MD0001 日次レポートタブ 画面仕様書"

    def test_image_with_empty_alt(self, tmp_path: Path):
        """altテキストが空の画像"""
        content = "![](image.png)"
        md_file = tmp_path / "empty_alt.md"
        md_file.write_text(content, encoding="utf-8")

        parser = MarkdownParser(str(md_file))
        images = parser.extract_images()

        assert len(images) == 1
        assert images[0].alt_text == ""
        assert images[0].path == "image.png"

    def test_multiple_h1_titles(self, tmp_path: Path):
        """複数のH1タイトルがある場合（最初のものを取得）"""
        content = """# 最初のタイトル

本文

# 2番目のタイトル

さらに本文
"""
        md_file = tmp_path / "multi_h1.md"
        md_file.write_text(content, encoding="utf-8")

        parser = MarkdownParser(str(md_file))
        title = parser.extract_h1_title()

        assert title == "最初のタイトル"
