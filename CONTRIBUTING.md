# Contributing to context-and-impact

Thank you for your interest in contributing!

## How to Contribute

### Reporting Issues

- Search [existing issues](https://github.com/ShunsukeHayashi/context-and-impact/issues) before creating a new one
- Use clear, descriptive titles
- Include reproduction steps, expected vs actual behavior, and your environment

### Submitting Pull Requests

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes following the code style guidelines below
4. Add or update tests if applicable
5. Commit using [Conventional Commits](https://www.conventionalcommits.org/): `feat:`, `fix:`, `docs:`, `chore:`
6. Push to your fork and open a Pull Request against `main`

### Code Style

- **Shell scripts**: `#!/usr/bin/env bash`, `set -euo pipefail`
- **Python**: PEP 8 + Black formatting
- **Markdown**: GitHub Flavored Markdown

### Areas for Contribution

- New workflow examples (`examples/w{N}-*.sh`)
- Additional Cypher queries for knowledge graph traversal (`src/gitnexus/queries.md`)
- Improvements to the semantic search CLI (`src/cli/semantic-search.py`)
- Documentation and translations
- Bug fixes and performance improvements

## Code of Conduct

Be respectful and constructive. This is an open-source project built for the AI agent community.

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
