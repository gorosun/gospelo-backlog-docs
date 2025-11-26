"""Tests for mermaid_converter module."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import subprocess
import tempfile

from gospelo_backlog_docs.mermaid_converter import (
    MermaidConverter,
    ConversionResult,
    check_mermaid_cli_installed,
)


class TestCheckMermaidCliInstalled:
    """check_mermaid_cli_installed 関数のテスト"""

    @patch("gospelo_backlog_docs.mermaid_converter.shutil.which")
    def test_mmdc_installed(self, mock_which):
        """mmdcがインストールされている場合"""
        mock_which.return_value = "/usr/local/bin/mmdc"

        result = check_mermaid_cli_installed()

        assert result is True
        mock_which.assert_called_once_with("mmdc")

    @patch("gospelo_backlog_docs.mermaid_converter.shutil.which")
    def test_mmdc_not_installed(self, mock_which):
        """mmdcがインストールされていない場合"""
        mock_which.return_value = None

        result = check_mermaid_cli_installed()

        assert result is False
        mock_which.assert_called_once_with("mmdc")


class TestConversionResult:
    """ConversionResult データクラスのテスト"""

    def test_success_result(self, tmp_path: Path):
        """成功結果の生成"""
        output_path = tmp_path / "test.png"

        result = ConversionResult(
            success=True,
            output_path=output_path
        )

        assert result.success is True
        assert result.output_path == output_path
        assert result.error_message is None

    def test_failure_result(self):
        """失敗結果の生成"""
        result = ConversionResult(
            success=False,
            output_path=None,
            error_message="変換に失敗しました"
        )

        assert result.success is False
        assert result.output_path is None
        assert result.error_message == "変換に失敗しました"


class TestMermaidConverterInit:
    """MermaidConverter 初期化のテスト"""

    @patch("gospelo_backlog_docs.mermaid_converter.shutil.which")
    def test_init_with_output_dir(self, mock_which, tmp_path: Path):
        """出力ディレクトリを指定して初期化"""
        mock_which.return_value = "/usr/local/bin/mmdc"

        converter = MermaidConverter(output_dir=tmp_path)

        assert converter.output_dir == tmp_path
        assert converter._temp_dir is None

    @patch("gospelo_backlog_docs.mermaid_converter.shutil.which")
    def test_init_without_output_dir(self, mock_which):
        """出力ディレクトリなしで初期化（一時ディレクトリ使用）"""
        mock_which.return_value = "/usr/local/bin/mmdc"

        converter = MermaidConverter()

        assert converter.output_dir is None
        assert converter._temp_dir is None  # まだ作成されていない

    @patch("gospelo_backlog_docs.mermaid_converter.shutil.which")
    def test_init_mmdc_not_installed(self, mock_which):
        """mmdcがインストールされていない場合の初期化エラー"""
        mock_which.return_value = None

        with pytest.raises(RuntimeError) as exc_info:
            MermaidConverter()

        assert "mermaid-cli (mmdc) がインストールされていません" in str(exc_info.value)

    @patch("gospelo_backlog_docs.mermaid_converter.shutil.which")
    def test_init_with_string_path(self, mock_which, tmp_path: Path):
        """文字列パスでの初期化"""
        mock_which.return_value = "/usr/local/bin/mmdc"

        converter = MermaidConverter(output_dir=str(tmp_path))

        assert converter.output_dir == tmp_path


class TestMermaidConverterGetOutputDir:
    """_get_output_dir メソッドのテスト"""

    @patch("gospelo_backlog_docs.mermaid_converter.shutil.which")
    def test_get_output_dir_with_specified_dir(self, mock_which, tmp_path: Path):
        """指定したディレクトリを返す"""
        mock_which.return_value = "/usr/local/bin/mmdc"
        output_dir = tmp_path / "output"

        converter = MermaidConverter(output_dir=output_dir)
        result = converter._get_output_dir()

        assert result == output_dir
        assert output_dir.exists()  # ディレクトリが作成される

    @patch("gospelo_backlog_docs.mermaid_converter.shutil.which")
    def test_get_output_dir_creates_temp_dir(self, mock_which):
        """一時ディレクトリを作成して返す"""
        mock_which.return_value = "/usr/local/bin/mmdc"

        converter = MermaidConverter()
        result = converter._get_output_dir()

        assert converter._temp_dir is not None
        assert result.exists()

        # クリーンアップ
        converter.cleanup()


class TestMermaidConverterConvert:
    """convert メソッドのテスト"""

    @pytest.fixture
    def mock_mmdc(self):
        """mmdcコマンドのモック"""
        with patch("gospelo_backlog_docs.mermaid_converter.shutil.which") as mock_which:
            mock_which.return_value = "/usr/local/bin/mmdc"
            yield mock_which

    @patch("gospelo_backlog_docs.mermaid_converter.subprocess.run")
    def test_convert_success(self, mock_run, mock_mmdc, tmp_path: Path):
        """変換成功"""
        # サブプロセスの成功をモック
        mock_run.return_value = Mock(returncode=0, stderr="", stdout="")

        converter = MermaidConverter(output_dir=tmp_path)

        # 出力ファイルを事前に作成（mmdcの動作をシミュレート）
        output_file = tmp_path / "test.png"
        output_file.write_bytes(b"fake png data")

        result = converter.convert(
            mermaid_code="graph TD\n    A-->B",
            output_name="test",
            format="png"
        )

        assert result.success is True
        assert result.output_path == output_file
        assert result.error_message is None

        # mmdcが正しい引数で呼ばれたか確認
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == "mmdc"
        assert "-i" in call_args
        assert "-o" in call_args

    @patch("gospelo_backlog_docs.mermaid_converter.subprocess.run")
    def test_convert_failure_nonzero_return(self, mock_run, mock_mmdc, tmp_path: Path):
        """変換失敗（非ゼロリターンコード）"""
        mock_run.return_value = Mock(
            returncode=1,
            stderr="Error: Invalid mermaid syntax",
            stdout=""
        )

        converter = MermaidConverter(output_dir=tmp_path)

        result = converter.convert(
            mermaid_code="invalid mermaid",
            output_name="test",
            format="png"
        )

        assert result.success is False
        assert result.output_path is None
        assert "Invalid mermaid syntax" in result.error_message

    @patch("gospelo_backlog_docs.mermaid_converter.subprocess.run")
    def test_convert_failure_no_output_file(self, mock_run, mock_mmdc, tmp_path: Path):
        """変換失敗（出力ファイルが生成されない）"""
        mock_run.return_value = Mock(returncode=0, stderr="", stdout="")

        converter = MermaidConverter(output_dir=tmp_path)

        # 出力ファイルを作成しない（mmdcが失敗した場合をシミュレート）

        result = converter.convert(
            mermaid_code="graph TD\n    A-->B",
            output_name="test",
            format="png"
        )

        assert result.success is False
        assert result.output_path is None
        assert "出力ファイルが生成されませんでした" in result.error_message

    @patch("gospelo_backlog_docs.mermaid_converter.subprocess.run")
    def test_convert_timeout(self, mock_run, mock_mmdc, tmp_path: Path):
        """変換タイムアウト"""
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="mmdc", timeout=60)

        converter = MermaidConverter(output_dir=tmp_path)

        result = converter.convert(
            mermaid_code="graph TD\n    A-->B",
            output_name="test",
            format="png"
        )

        assert result.success is False
        assert result.output_path is None
        assert "タイムアウト" in result.error_message

    @patch("gospelo_backlog_docs.mermaid_converter.subprocess.run")
    def test_convert_exception(self, mock_run, mock_mmdc, tmp_path: Path):
        """変換中の例外"""
        mock_run.side_effect = Exception("Unexpected error")

        converter = MermaidConverter(output_dir=tmp_path)

        result = converter.convert(
            mermaid_code="graph TD\n    A-->B",
            output_name="test",
            format="png"
        )

        assert result.success is False
        assert result.output_path is None
        assert "Unexpected error" in result.error_message

    @patch("gospelo_backlog_docs.mermaid_converter.subprocess.run")
    def test_convert_svg_format(self, mock_run, mock_mmdc, tmp_path: Path):
        """SVG形式での変換"""
        mock_run.return_value = Mock(returncode=0, stderr="", stdout="")

        converter = MermaidConverter(output_dir=tmp_path)

        # SVG出力ファイルを作成
        output_file = tmp_path / "test.svg"
        output_file.write_text("<svg></svg>")

        result = converter.convert(
            mermaid_code="graph TD\n    A-->B",
            output_name="test",
            format="svg"
        )

        assert result.success is True
        assert result.output_path.suffix == ".svg"

    @patch("gospelo_backlog_docs.mermaid_converter.subprocess.run")
    def test_convert_with_theme(self, mock_run, mock_mmdc, tmp_path: Path):
        """テーマ指定での変換"""
        mock_run.return_value = Mock(returncode=0, stderr="", stdout="")

        converter = MermaidConverter(output_dir=tmp_path)

        # 出力ファイルを作成
        output_file = tmp_path / "test.png"
        output_file.write_bytes(b"fake png")

        result = converter.convert(
            mermaid_code="graph TD\n    A-->B",
            output_name="test",
            format="png",
            theme="dark",
            background="transparent"
        )

        # テーマと背景が引数に含まれているか確認
        call_args = mock_run.call_args[0][0]
        assert "-t" in call_args
        assert "dark" in call_args
        assert "-b" in call_args
        assert "transparent" in call_args

    @patch("gospelo_backlog_docs.mermaid_converter.subprocess.run")
    def test_convert_cleans_up_input_file(self, mock_run, mock_mmdc, tmp_path: Path):
        """入力ファイルがクリーンアップされる"""
        mock_run.return_value = Mock(returncode=0, stderr="", stdout="")

        converter = MermaidConverter(output_dir=tmp_path)

        # 出力ファイルを作成
        output_file = tmp_path / "test.png"
        output_file.write_bytes(b"fake png")

        converter.convert(
            mermaid_code="graph TD\n    A-->B",
            output_name="test",
            format="png"
        )

        # 入力ファイル (.mmd) が削除されているか確認
        input_file = tmp_path / "test.mmd"
        assert not input_file.exists()


class TestMermaidConverterConvertMultiple:
    """convert_multiple メソッドのテスト"""

    @patch("gospelo_backlog_docs.mermaid_converter.subprocess.run")
    @patch("gospelo_backlog_docs.mermaid_converter.shutil.which")
    def test_convert_multiple_success(self, mock_which, mock_run, tmp_path: Path):
        """複数の変換成功"""
        mock_which.return_value = "/usr/local/bin/mmdc"
        mock_run.return_value = Mock(returncode=0, stderr="", stdout="")

        converter = MermaidConverter(output_dir=tmp_path)

        # 出力ファイルを作成
        (tmp_path / "diagram1.png").write_bytes(b"fake png 1")
        (tmp_path / "diagram2.png").write_bytes(b"fake png 2")

        mermaid_codes = [
            ("graph TD\n    A-->B", "diagram1"),
            ("graph LR\n    X-->Y", "diagram2"),
        ]

        results = converter.convert_multiple(mermaid_codes)

        assert len(results) == 2
        assert all(r.success for r in results)

    @patch("gospelo_backlog_docs.mermaid_converter.subprocess.run")
    @patch("gospelo_backlog_docs.mermaid_converter.shutil.which")
    def test_convert_multiple_partial_failure(self, mock_which, mock_run, tmp_path: Path):
        """複数変換で一部失敗"""
        mock_which.return_value = "/usr/local/bin/mmdc"

        # 1回目は成功、2回目は失敗
        mock_run.side_effect = [
            Mock(returncode=0, stderr="", stdout=""),
            Mock(returncode=1, stderr="Error", stdout=""),
        ]

        converter = MermaidConverter(output_dir=tmp_path)

        # 1つ目の出力ファイルのみ作成
        (tmp_path / "diagram1.png").write_bytes(b"fake png")

        mermaid_codes = [
            ("graph TD\n    A-->B", "diagram1"),
            ("invalid", "diagram2"),
        ]

        results = converter.convert_multiple(mermaid_codes)

        assert len(results) == 2
        assert results[0].success is True
        assert results[1].success is False


class TestMermaidConverterCleanup:
    """cleanup メソッドのテスト"""

    @patch("gospelo_backlog_docs.mermaid_converter.shutil.which")
    def test_cleanup_temp_dir(self, mock_which):
        """一時ディレクトリのクリーンアップ"""
        mock_which.return_value = "/usr/local/bin/mmdc"

        converter = MermaidConverter()

        # 一時ディレクトリを作成
        temp_dir_path = converter._get_output_dir()
        assert temp_dir_path.exists()

        # クリーンアップ
        converter.cleanup()

        assert converter._temp_dir is None
        # 一時ディレクトリが削除されているか確認
        assert not temp_dir_path.exists()

    @patch("gospelo_backlog_docs.mermaid_converter.shutil.which")
    def test_cleanup_no_temp_dir(self, mock_which, tmp_path: Path):
        """一時ディレクトリがない場合のクリーンアップ"""
        mock_which.return_value = "/usr/local/bin/mmdc"

        converter = MermaidConverter(output_dir=tmp_path)

        # クリーンアップを呼んでもエラーにならない
        converter.cleanup()

        assert converter._temp_dir is None

    @patch("gospelo_backlog_docs.mermaid_converter.shutil.which")
    def test_cleanup_multiple_times(self, mock_which):
        """複数回のクリーンアップ"""
        mock_which.return_value = "/usr/local/bin/mmdc"

        converter = MermaidConverter()
        converter._get_output_dir()  # 一時ディレクトリを作成

        # 複数回クリーンアップしてもエラーにならない
        converter.cleanup()
        converter.cleanup()

        assert converter._temp_dir is None


class TestMermaidConverterIntegration:
    """統合テスト（モックなし、実際のmmdc使用）"""

    @pytest.fixture
    def mmdc_available(self):
        """mmdcが利用可能な場合のみテストを実行"""
        if not check_mermaid_cli_installed():
            pytest.skip("mermaid-cli (mmdc) is not installed")

    @pytest.mark.skip(reason="CI環境ではmmdcがインストールされていない可能性がある")
    def test_real_conversion(self, mmdc_available, tmp_path: Path):
        """実際の変換テスト（mmdcがインストールされている場合）"""
        converter = MermaidConverter(output_dir=tmp_path)

        mermaid_code = """
graph TD
    A[Start] --> B[End]
"""

        result = converter.convert(mermaid_code, "real_test", format="png")

        assert result.success is True
        assert result.output_path.exists()
        assert result.output_path.stat().st_size > 0

        converter.cleanup()
