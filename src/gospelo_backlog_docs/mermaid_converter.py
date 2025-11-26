#!/usr/bin/env python3
"""
MermaidJS変換モジュール
- MermaidJSコードをPNG/SVGに変換
- mermaid-cli (mmdc) を使用
"""

import subprocess
import tempfile
import shutil
from pathlib import Path
from dataclasses import dataclass
from typing import Literal, Optional


@dataclass
class ConversionResult:
    """変換結果"""
    success: bool
    output_path: Optional[Path]
    error_message: Optional[str] = None


class MermaidConverter:
    """MermaidJS変換クラス"""

    def __init__(self, output_dir: Optional[str | Path] = None):
        """
        Args:
            output_dir: 出力ディレクトリ (Noneの場合は一時ディレクトリ)
        """
        self.output_dir = Path(output_dir) if output_dir else None
        self._temp_dir: Optional[tempfile.TemporaryDirectory] = None
        self._check_mmdc()

    def _check_mmdc(self) -> None:
        """mmdc (mermaid-cli) がインストールされているか確認"""
        if not shutil.which('mmdc'):
            raise RuntimeError(
                "mermaid-cli (mmdc) がインストールされていません。\n"
                "インストール方法: npm install -g @mermaid-js/mermaid-cli"
            )

    def _get_output_dir(self) -> Path:
        """出力ディレクトリを取得"""
        if self.output_dir:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            return self.output_dir

        if not self._temp_dir:
            self._temp_dir = tempfile.TemporaryDirectory()
        return Path(self._temp_dir.name)

    def convert(
        self,
        mermaid_code: str,
        output_name: str,
        format: Literal['png', 'svg'] = 'png',
        theme: str = 'default',
        background: str = 'white'
    ) -> ConversionResult:
        """
        MermaidJSコードを画像に変換

        Args:
            mermaid_code: MermaidJSコード
            output_name: 出力ファイル名 (拡張子なし)
            format: 出力形式 ('png' or 'svg')
            theme: テーマ ('default', 'dark', 'forest', 'neutral')
            background: 背景色 ('white', 'transparent', etc.)

        Returns:
            ConversionResult
        """
        output_dir = self._get_output_dir()

        # 一時入力ファイルを作成
        input_file = output_dir / f"{output_name}.mmd"
        output_file = output_dir / f"{output_name}.{format}"

        try:
            # Mermaidコードを一時ファイルに書き込み
            input_file.write_text(mermaid_code, encoding='utf-8')

            # mmdc コマンドを実行
            cmd = [
                'mmdc',
                '-i', str(input_file),
                '-o', str(output_file),
                '-t', theme,
                '-b', background,
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0:
                return ConversionResult(
                    success=False,
                    output_path=None,
                    error_message=result.stderr or result.stdout
                )

            if not output_file.exists():
                return ConversionResult(
                    success=False,
                    output_path=None,
                    error_message="出力ファイルが生成されませんでした"
                )

            return ConversionResult(
                success=True,
                output_path=output_file
            )

        except subprocess.TimeoutExpired:
            return ConversionResult(
                success=False,
                output_path=None,
                error_message="変換がタイムアウトしました (60秒)"
            )
        except Exception as e:
            return ConversionResult(
                success=False,
                output_path=None,
                error_message=str(e)
            )
        finally:
            # 入力ファイルを削除
            if input_file.exists():
                input_file.unlink()

    def convert_multiple(
        self,
        mermaid_codes: list[tuple[str, str]],
        format: Literal['png', 'svg'] = 'png',
        theme: str = 'default',
        background: str = 'white'
    ) -> list[ConversionResult]:
        """
        複数のMermaidJSコードを変換

        Args:
            mermaid_codes: [(コード, 出力名), ...] のリスト
            format: 出力形式
            theme: テーマ
            background: 背景色

        Returns:
            ConversionResult のリスト
        """
        results = []
        for code, name in mermaid_codes:
            result = self.convert(code, name, format, theme, background)
            results.append(result)
        return results

    def cleanup(self) -> None:
        """一時ディレクトリをクリーンアップ"""
        if self._temp_dir:
            self._temp_dir.cleanup()
            self._temp_dir = None


def check_mermaid_cli_installed() -> bool:
    """mermaid-cliがインストールされているか確認"""
    return shutil.which('mmdc') is not None


if __name__ == '__main__':
    import sys

    # インストール確認
    if not check_mermaid_cli_installed():
        print("ERROR: mermaid-cli (mmdc) がインストールされていません")
        print("インストール: npm install -g @mermaid-js/mermaid-cli")
        sys.exit(1)

    # テスト変換
    test_code = """
flowchart TD
    A[Start] --> B{Is it working?}
    B -->|Yes| C[Great!]
    B -->|No| D[Debug]
    D --> B
    C --> E[End]
"""

    print("MermaidJS変換テスト...")
    converter = MermaidConverter(output_dir="./test_output")

    result = converter.convert(test_code, "test_diagram", format='png')

    if result.success:
        print(f"✓ 変換成功: {result.output_path}")
    else:
        print(f"✗ 変換失敗: {result.error_message}")

    converter.cleanup()
