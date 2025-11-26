# Project Handover Document

## Project Overview

**Project Name**: gospelo-backlog-docs
**Version**: 1.0.0
**Last Updated**: 2025-11-26

A CLI tool that uploads Markdown documents to Backlog Wiki with support for images and MermaidJS diagrams.

---

## Repository Structure

```
gospelo-backlog-docs/
├── src/gospelo_backlog_docs/    # Source code
│   ├── __init__.py              # Package initialization, version
│   ├── __main__.py              # Entry point for `python -m`
│   ├── cli.py                   # CLI argument parsing
│   ├── backlog_client.py        # Backlog API client
│   ├── markdown_parser.py       # Markdown parsing logic
│   ├── mermaid_converter.py     # MermaidJS to PNG conversion
│   └── uploader.py              # Upload orchestration
├── tests/                       # Unit tests (82 tests, 73% coverage)
│   ├── test_backlog_client.py
│   ├── test_markdown_parser.py
│   ├── test_mermaid_converter.py
│   └── test_uploader.py
├── docs/                        # Documentation
│   ├── README_jp.md             # Japanese README
│   ├── CHANGELOG.md / _jp.md    # Changelog (EN/JP)
│   ├── CONTRIBUTING.md / _jp.md # Contributing guide (EN/JP)
│   └── test/                    # Test reports
├── README.md                    # Main documentation
├── pyproject.toml               # Package configuration
├── LICENSE                      # MIT License
└── THIRD_PARTY_LICENSES.md      # Dependency licenses
```

---

## Key Components

### 1. CLI (`cli.py`)
- Entry point: `gospelo-backlog-docs` command
- Argument parsing with argparse
- Calls `WikiUploader` from `uploader.py`

### 2. Backlog Client (`backlog_client.py`)
- Handles all Backlog API communication
- Wiki CRUD operations
- Attachment upload
- Credential management (CLI args > env vars > .env files)
- Global config: `~/.config/gospelo-backlog-docs/.env`

### 3. Markdown Parser (`markdown_parser.py`)
- Extracts images and MermaidJS blocks
- Resolves local image paths
- Extracts H1 title for wiki page name

### 4. Mermaid Converter (`mermaid_converter.py`)
- Converts MermaidJS code blocks to PNG
- Requires `mmdc` (mermaid-cli) to be installed
- Handles timeout and cleanup

### 5. Uploader (`uploader.py`)
- Orchestrates the upload process
- Combines parser, converter, and client
- Handles dry-run mode

---

## Development Setup

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=gospelo_backlog_docs --cov-report=term-missing

# Code formatting
black src/ tests/
isort src/ tests/

# Type checking
mypy src/
```

---

## Testing Strategy

| Module | Coverage | Strategy |
|--------|----------|----------|
| markdown_parser.py | 91% | Comprehensive - parser logic is bug-prone |
| mermaid_converter.py | 82% | Mock external commands |
| backlog_client.py | 74% | Mock API calls |
| uploader.py | 73% | Test main flows |
| cli.py | 0% | No tests - simple entry point |

**Test Results**: 81 passed, 1 skipped (0.18s)

---

## Configuration

### Environment Variables
```
BACKLOG_SPACE_ID=your-space-id
BACKLOG_API_KEY=your-api-key
BACKLOG_DOMAIN=backlog.jp  # or backlog.com
```

### Credential Priority (highest first)
1. CLI arguments
2. Environment variables
3. Specified .env file (`--env-file`)
4. Local `.env` file
5. Global config `~/.config/gospelo-backlog-docs/.env`

---

## Dependencies

### Required
- Python 3.10+
- requests >= 2.28.0
- python-dotenv >= 1.0.0

### Optional
- mermaid-cli (npm package) for MermaidJS support

### Development
- pytest, pytest-cov
- black, isort, mypy

---

## Known Issues / Technical Debt

1. **No E2E tests**: API integration is tested manually
2. **Sequential uploads**: Images uploaded one by one (parallel not implemented)
3. **Error messages in Japanese**: Some error messages are in Japanese

---

## Future Improvements (if needed)

| Feature | Priority | Notes |
|---------|----------|-------|
| Parallel image upload | Low | Current sequential works fine |
| GitHub Actions CI | Medium | Automated testing |
| PyPI publishing | High | For public distribution |

---

## Useful Commands

```bash
# Basic upload
gospelo-backlog-docs document.md --project PROJECT_KEY

# Dry run (no upload)
gospelo-backlog-docs document.md --project PROJECT_KEY --dry-run

# Specify wiki name
gospelo-backlog-docs document.md --project PROJECT_KEY --wiki-name "Parent/Child"

# Use specific env file
gospelo-backlog-docs document.md --project PROJECT_KEY --env-file .env.production
```

---

## Contact / Resources

- **Repository**: https://github.com/gorosun/gospelo-backlog-docs
- **Test Report**: [docs/test/test_report.md](docs/test/test_report.md)
- **Contributing**: [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md)
