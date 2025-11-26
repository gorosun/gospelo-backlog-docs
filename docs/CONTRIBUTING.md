# Contributing Guide

Thank you for your interest in contributing to gospelo-backlog-docs!

## Development Setup

### Prerequisites

- Python 3.10+
- Node.js (for mermaid-cli, optional)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/gorosun/gospelo-backlog-docs.git
cd gospelo-backlog-docs
```

2. Install development dependencies:
```bash
pip install -e ".[dev]"
```

3. (Optional) Install mermaid-cli for MermaidJS support:
```bash
npm install -g @mermaid-js/mermaid-cli
```

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=gospelo_backlog_docs --cov-report=term-missing

# Run specific test file
pytest tests/test_markdown_parser.py -v
```

## Code Style

This project uses:
- **black** for code formatting
- **isort** for import sorting
- **mypy** for type checking

```bash
# Format code
black src/ tests/
isort src/ tests/

# Type checking
mypy src/
```

## Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and ensure they pass
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Commit Message Guidelines

- Use clear and descriptive commit messages
- Start with a verb (Add, Fix, Update, Remove, etc.)
- Reference issues when applicable

Examples:
```
Add support for SVG output format
Fix image path resolution for Windows
Update README with new examples
```

## Reporting Issues

When reporting issues, please include:

1. Python version (`python --version`)
2. Package version (`gospelo-backlog-docs --version`)
3. Operating system
4. Steps to reproduce
5. Expected behavior
6. Actual behavior
7. Error messages (if any)

## Feature Requests

Feature requests are welcome! Please open an issue with:

1. Clear description of the feature
2. Use case / motivation
3. (Optional) Proposed implementation approach

## Testing Guidelines

- Write tests for new features
- Maintain or improve code coverage
- Mock external dependencies (API calls, external commands)
- Follow existing test patterns

See [Test Report](test/test_report.md) for current test coverage and strategy.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
