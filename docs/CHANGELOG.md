# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2025-11-26

### Added

- Initial release
- Upload Markdown files to Backlog Wiki
- Automatic image upload and link conversion
- MermaidJS diagram conversion to PNG (requires mermaid-cli)
- Extract wiki page name from H1 title
- Support for hierarchical wiki page names
- Flexible credential management:
  - CLI arguments
  - Environment variables
  - .env files (local and global)
- Dry-run mode for testing without uploading
- Comprehensive unit tests (82 tests, 73% coverage)

### Dependencies

- Python 3.10+
- requests >= 2.28.0
- python-dotenv >= 1.0.0

### Optional Dependencies

- mermaid-cli (npm package) for MermaidJS support

[Unreleased]: https://github.com/gorosun/gospelo-backlog-docs/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/gorosun/gospelo-backlog-docs/releases/tag/v1.0.0
