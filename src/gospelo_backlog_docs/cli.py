#!/usr/bin/env python3
"""CLI entry point for Backlog Wiki Uploader."""

import argparse
import sys
import time
import threading
from pathlib import Path
from typing import List

from .uploader import WikiUploader


# Braille spinner pattern
SPINNER_FRAMES = ['⣾', '⣽', '⣻', '⢿', '⡿', '⣟', '⣯', '⣷']


class ProgressSpinner:
    """Progress indicator with spinner and percentage."""

    def __init__(self, total: int):
        self.total = total
        self.current = 0
        self.current_file = ""
        self.spinning = False
        self.spinner_thread = None
        self.frame_index = 0

    def _get_progress_bar(self, width: int = 20) -> str:
        """Generate a progress bar string."""
        if self.total == 0:
            return "─" * width
        filled = int(width * self.current / self.total)
        return "█" * filled + "─" * (width - filled)

    def _get_percentage(self) -> int:
        """Calculate current percentage."""
        if self.total == 0:
            return 0
        return int(100 * self.current / self.total)

    def _spin(self):
        """Spinner animation thread."""
        while self.spinning:
            frame = SPINNER_FRAMES[self.frame_index % len(SPINNER_FRAMES)]
            percentage = self._get_percentage()
            progress_bar = self._get_progress_bar()
            status = f"{frame} {percentage:3d}% {progress_bar} [{self.current}/{self.total}] {self.current_file}"
            # Clear line and write status
            sys.stdout.write(f"\r\033[K{status}")
            sys.stdout.flush()
            self.frame_index += 1
            time.sleep(0.1)

    def start(self, filename: str):
        """Start spinner for a file."""
        self.current_file = filename
        self.spinning = True
        self.spinner_thread = threading.Thread(target=self._spin, daemon=True)
        self.spinner_thread.start()

    def stop(self, success: bool = True):
        """Stop spinner and show result (updates same line)."""
        self.spinning = False
        if self.spinner_thread:
            self.spinner_thread.join(timeout=0.2)
        self.current += 1
        percentage = self._get_percentage()
        progress_bar = self._get_progress_bar()
        status_icon = "✓" if success else "✗"
        status = f"{status_icon} {percentage:3d}% {progress_bar} [{self.current}/{self.total}] {self.current_file}"
        # Clear line with ANSI escape and print status (no newline)
        sys.stdout.write(f"\r\033[K{status}")
        sys.stdout.flush()

    def finish(self):
        """Print final newline when all processing is complete."""
        sys.stdout.write("\n")
        sys.stdout.flush()


def collect_markdown_files(
    path: Path,
    recursive: bool = True,
    pattern: str = "*.md",
    exclude: List[str] = None
) -> List[Path]:
    """
    Collect Markdown files from a path.

    Args:
        path: File or directory path
        recursive: Search subdirectories recursively
        pattern: Glob pattern for matching files
        exclude: List of patterns to exclude

    Returns:
        List of Markdown file paths
    """
    exclude = exclude or []

    if path.is_file():
        # Single file
        if path.suffix.lower() == '.md':
            return [path]
        return []

    if path.is_dir():
        # Directory - collect markdown files
        if recursive:
            files = list(path.rglob(pattern))
        else:
            files = list(path.glob(pattern))

        # Apply exclusions
        if exclude:
            filtered = []
            for f in files:
                excluded = False
                for exc_pattern in exclude:
                    if f.match(exc_pattern):
                        excluded = True
                        break
                if not excluded:
                    filtered.append(f)
            files = filtered

        # Sort by path for consistent ordering
        return sorted(files)

    return []


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="gospelo-backlog-docs",
        description="Upload Markdown documents to Backlog Wiki with image and MermaidJS support"
    )
    parser.add_argument(
        "path",
        help="Path to Markdown file or directory containing Markdown files"
    )
    parser.add_argument(
        "--project", "-p",
        required=True,
        help="Backlog project key (e.g., MYPROJECT)"
    )
    parser.add_argument(
        "--wiki-name", "-n",
        help="Wiki page name (defaults to H1 title or filename). Only used for single file."
    )
    parser.add_argument(
        "--space-id", "-s",
        help="Backlog space ID (env: BACKLOG_SPACE_ID, or ~/.config/gospelo-backlog-docs/.env)"
    )
    parser.add_argument(
        "--api-key", "-k",
        help="Backlog API key (env: BACKLOG_API_KEY, or ~/.config/gospelo-backlog-docs/.env)"
    )
    parser.add_argument(
        "--domain", "-d",
        help="Backlog domain (default: backlog.jp, env: BACKLOG_DOMAIN)"
    )
    parser.add_argument(
        "--env-file", "-e",
        help="Path to .env file (default: ./.env or ~/.config/gospelo-backlog-docs/.env)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse only, do not upload"
    )
    parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="Do not search subdirectories (default: search recursively)"
    )
    parser.add_argument(
        "--pattern",
        default="*.md",
        help="File pattern to match (default: *.md)"
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="Patterns to exclude (can be specified multiple times)"
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Continue uploading remaining files even if one fails"
    )
    parser.add_argument(
        "--version", "-v",
        action="version",
        version=f"%(prog)s {__import__('gospelo_backlog_docs').__version__}"
    )

    args = parser.parse_args()

    try:
        path = Path(args.path)

        # Collect markdown files
        files = collect_markdown_files(
            path=path,
            recursive=not args.no_recursive,
            pattern=args.pattern,
            exclude=args.exclude
        )

        if not files:
            print(f"Error: No Markdown files found in '{args.path}'", file=sys.stderr)
            sys.exit(1)

        # Single file with custom wiki-name
        if len(files) == 1 and args.wiki_name:
            wiki_names = [args.wiki_name]
        else:
            # Multiple files - wiki-name is ignored
            if args.wiki_name and len(files) > 1:
                print("Warning: --wiki-name is ignored when processing multiple files", file=sys.stderr)
            wiki_names = [None] * len(files)

        # Create uploader (quiet mode for batch processing with progress spinner)
        uploader = WikiUploader(
            project_key=args.project,
            space_id=args.space_id,
            api_key=args.api_key,
            domain=args.domain,
            env_file=args.env_file,
            quiet=True
        )

        # Process files
        total = len(files)
        success_count = 0
        failed_count = 0
        results = []

        # Show file list first
        print(f"\nFound {total} Markdown file(s) to process:")
        print("-" * 60)
        for i, f in enumerate(files, 1):
            print(f"  {i:3d}. {f}")
        print("-" * 60)
        print()

        # Initialize progress spinner
        progress = ProgressSpinner(total)

        for md_file, wiki_name in zip(files, wiki_names):
            filename = str(md_file)
            progress.start(filename)

            try:
                result = uploader.upload(
                    markdown_path=filename,
                    wiki_name=wiki_name,
                    dry_run=args.dry_run
                )
                results.append({'file': filename, 'success': True, 'result': result})
                success_count += 1
                progress.stop(success=True)

            except Exception as e:
                progress.stop(success=False)
                print(f"  Error: {e}", file=sys.stderr)
                results.append({'file': filename, 'success': False, 'error': str(e)})
                failed_count += 1

                if not args.continue_on_error:
                    progress.finish()
                    print("Aborting due to error. Use --continue-on-error to continue.", file=sys.stderr)
                    sys.exit(1)

        # Finish progress display (print newline)
        progress.finish()

        # Summary
        print(f"{'='*60}")
        print(f"Summary")
        print(f"{'='*60}")
        print(f"Total files: {total}")
        print(f"Successful: {success_count}")
        print(f"Failed: {failed_count}")

        if failed_count > 0:
            print(f"\nFailed files:")
            for r in results:
                if not r['success']:
                    print(f"  - {r['file']}: {r['error']}")

        print(f"{'='*60}\n")

        if failed_count > 0:
            sys.exit(1)

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
