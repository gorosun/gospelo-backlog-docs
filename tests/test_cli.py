#!/usr/bin/env python3
"""Tests for CLI module."""

import pytest
from pathlib import Path
import tempfile
import os
import io
import sys

from gospelo_backlog_docs.cli import collect_markdown_files, ProgressSpinner, SPINNER_FRAMES


class TestCollectMarkdownFiles:
    """Tests for collect_markdown_files function."""

    def test_single_file(self, tmp_path):
        """Test collecting a single markdown file."""
        md_file = tmp_path / "test.md"
        md_file.write_text("# Test")

        result = collect_markdown_files(md_file)

        assert len(result) == 1
        assert result[0] == md_file

    def test_single_file_non_markdown(self, tmp_path):
        """Test that non-markdown files are ignored."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("Test")

        result = collect_markdown_files(txt_file)

        assert len(result) == 0

    def test_directory_flat(self, tmp_path):
        """Test collecting files from a flat directory."""
        (tmp_path / "file1.md").write_text("# File 1")
        (tmp_path / "file2.md").write_text("# File 2")
        (tmp_path / "file3.txt").write_text("Not markdown")

        result = collect_markdown_files(tmp_path, recursive=False)

        assert len(result) == 2
        names = [f.name for f in result]
        assert "file1.md" in names
        assert "file2.md" in names

    def test_directory_recursive(self, tmp_path):
        """Test recursive directory search."""
        (tmp_path / "root.md").write_text("# Root")
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "nested.md").write_text("# Nested")

        result = collect_markdown_files(tmp_path, recursive=True)

        assert len(result) == 2
        names = [f.name for f in result]
        assert "root.md" in names
        assert "nested.md" in names

    def test_directory_non_recursive(self, tmp_path):
        """Test non-recursive directory search."""
        (tmp_path / "root.md").write_text("# Root")
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "nested.md").write_text("# Nested")

        result = collect_markdown_files(tmp_path, recursive=False)

        assert len(result) == 1
        assert result[0].name == "root.md"

    def test_custom_pattern(self, tmp_path):
        """Test custom file pattern."""
        (tmp_path / "design_spec.md").write_text("# Design")
        (tmp_path / "api_spec.md").write_text("# API")
        (tmp_path / "readme.md").write_text("# Readme")

        result = collect_markdown_files(tmp_path, pattern="*_spec.md")

        assert len(result) == 2
        names = [f.name for f in result]
        assert "design_spec.md" in names
        assert "api_spec.md" in names
        assert "readme.md" not in names

    def test_exclude_pattern(self, tmp_path):
        """Test excluding files by pattern."""
        (tmp_path / "doc.md").write_text("# Doc")
        (tmp_path / "draft.md").write_text("# Draft")
        (tmp_path / "README.md").write_text("# Readme")

        result = collect_markdown_files(tmp_path, exclude=["README.md", "draft.md"])

        assert len(result) == 1
        assert result[0].name == "doc.md"

    def test_exclude_multiple_patterns(self, tmp_path):
        """Test excluding multiple patterns."""
        (tmp_path / "doc.md").write_text("# Doc")
        (tmp_path / "doc_draft.md").write_text("# Draft")
        (tmp_path / "test_doc.md").write_text("# Test")

        result = collect_markdown_files(tmp_path, exclude=["*_draft.md", "test_*.md"])

        assert len(result) == 1
        assert result[0].name == "doc.md"

    def test_empty_directory(self, tmp_path):
        """Test empty directory returns empty list."""
        result = collect_markdown_files(tmp_path)

        assert len(result) == 0

    def test_nonexistent_path(self, tmp_path):
        """Test nonexistent path returns empty list."""
        nonexistent = tmp_path / "nonexistent"

        result = collect_markdown_files(nonexistent)

        assert len(result) == 0

    def test_sorted_results(self, tmp_path):
        """Test that results are sorted by path."""
        (tmp_path / "c.md").write_text("# C")
        (tmp_path / "a.md").write_text("# A")
        (tmp_path / "b.md").write_text("# B")

        result = collect_markdown_files(tmp_path)

        names = [f.name for f in result]
        assert names == ["a.md", "b.md", "c.md"]

    def test_deep_nesting(self, tmp_path):
        """Test deeply nested directories."""
        deep_dir = tmp_path / "a" / "b" / "c" / "d"
        deep_dir.mkdir(parents=True)
        (deep_dir / "deep.md").write_text("# Deep")
        (tmp_path / "root.md").write_text("# Root")

        result = collect_markdown_files(tmp_path, recursive=True)

        assert len(result) == 2
        names = [f.name for f in result]
        assert "deep.md" in names
        assert "root.md" in names

    def test_case_insensitive_extension(self, tmp_path):
        """Test that .MD extension is also recognized for single file."""
        md_file = tmp_path / "test.MD"
        md_file.write_text("# Test")

        result = collect_markdown_files(md_file)

        assert len(result) == 1


class TestProgressSpinner:
    """Tests for ProgressSpinner class."""

    def test_init(self):
        """Test spinner initialization."""
        spinner = ProgressSpinner(total=10)

        assert spinner.total == 10
        assert spinner.current == 0
        assert spinner.current_file == ""
        assert spinner.spinning is False

    def test_get_progress_bar_empty(self):
        """Test progress bar at 0%."""
        spinner = ProgressSpinner(total=10)

        bar = spinner._get_progress_bar(width=10)

        assert bar == "─" * 10

    def test_get_progress_bar_half(self):
        """Test progress bar at 50%."""
        spinner = ProgressSpinner(total=10)
        spinner.current = 5

        bar = spinner._get_progress_bar(width=10)

        assert bar == "█" * 5 + "─" * 5

    def test_get_progress_bar_full(self):
        """Test progress bar at 100%."""
        spinner = ProgressSpinner(total=10)
        spinner.current = 10

        bar = spinner._get_progress_bar(width=10)

        assert bar == "█" * 10

    def test_get_progress_bar_zero_total(self):
        """Test progress bar with zero total."""
        spinner = ProgressSpinner(total=0)

        bar = spinner._get_progress_bar(width=10)

        assert bar == "─" * 10

    def test_get_percentage_zero(self):
        """Test percentage at 0%."""
        spinner = ProgressSpinner(total=10)

        assert spinner._get_percentage() == 0

    def test_get_percentage_half(self):
        """Test percentage at 50%."""
        spinner = ProgressSpinner(total=10)
        spinner.current = 5

        assert spinner._get_percentage() == 50

    def test_get_percentage_full(self):
        """Test percentage at 100%."""
        spinner = ProgressSpinner(total=10)
        spinner.current = 10

        assert spinner._get_percentage() == 100

    def test_get_percentage_zero_total(self):
        """Test percentage with zero total."""
        spinner = ProgressSpinner(total=0)

        assert spinner._get_percentage() == 0

    def test_stop_increments_current(self):
        """Test that stop() increments current counter."""
        spinner = ProgressSpinner(total=3)
        spinner.current_file = "test.md"

        # Capture stdout
        captured = io.StringIO()
        sys.stdout = captured

        spinner.stop(success=True)

        sys.stdout = sys.__stdout__

        assert spinner.current == 1

    def test_stop_success_icon(self):
        """Test that success shows checkmark icon."""
        spinner = ProgressSpinner(total=3)
        spinner.current_file = "test.md"

        captured = io.StringIO()
        sys.stdout = captured

        spinner.stop(success=True)

        sys.stdout = sys.__stdout__
        output = captured.getvalue()

        assert "✓" in output

    def test_stop_failure_icon(self):
        """Test that failure shows X icon."""
        spinner = ProgressSpinner(total=3)
        spinner.current_file = "test.md"

        captured = io.StringIO()
        sys.stdout = captured

        spinner.stop(success=False)

        sys.stdout = sys.__stdout__
        output = captured.getvalue()

        assert "✗" in output

    def test_finish_prints_newline(self):
        """Test that finish() prints a newline."""
        spinner = ProgressSpinner(total=1)

        captured = io.StringIO()
        sys.stdout = captured

        spinner.finish()

        sys.stdout = sys.__stdout__
        output = captured.getvalue()

        assert output == "\n"

    def test_spinner_frames_constant(self):
        """Test that spinner frames are defined correctly."""
        assert len(SPINNER_FRAMES) == 8
        assert SPINNER_FRAMES == ['⣾', '⣽', '⣻', '⢿', '⡿', '⣟', '⣯', '⣷']
