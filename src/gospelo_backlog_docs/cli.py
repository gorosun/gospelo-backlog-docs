#!/usr/bin/env python3
"""CLI entry point for Backlog Wiki Uploader."""

import argparse
import sys
from pathlib import Path

from .uploader import WikiUploader


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="gospelo-backlog-docs",
        description="Upload Markdown documents to Backlog Wiki with image and MermaidJS support"
    )
    parser.add_argument(
        "markdown_file",
        help="Path to the Markdown file to upload"
    )
    parser.add_argument(
        "--project", "-p",
        required=True,
        help="Backlog project key (e.g., MYPROJECT)"
    )
    parser.add_argument(
        "--wiki-name", "-n",
        help="Wiki page name (defaults to H1 title or filename)"
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
        "--version", "-v",
        action="version",
        version=f"%(prog)s {__import__('gospelo_backlog_docs').__version__}"
    )

    args = parser.parse_args()

    try:
        uploader = WikiUploader(
            project_key=args.project,
            space_id=args.space_id,
            api_key=args.api_key,
            domain=args.domain,
            env_file=args.env_file
        )

        result = uploader.upload(
            markdown_path=args.markdown_file,
            wiki_name=args.wiki_name,
            dry_run=args.dry_run
        )

        if not args.dry_run:
            print(f"\nResult: {result}")

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
