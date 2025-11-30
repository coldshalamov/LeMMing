# Contributing to LeMMing

Thank you for your interest in contributing to LeMMing! This document provides guidelines for contributing to the project.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/LeMMing.git
   cd LeMMing
   ```
3. **Set up development environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows
   pip install -e ".[dev,api,llm]"
   ```

## Development Workflow

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
make coverage

# Run specific test file
pytest tests/test_messaging.py

# Run with verbose output
pytest -v
```

### Code Quality

```bash
# Format code
make format

# Lint code
make lint

# Fix linting issues
make lint-fix

# Type checking
make typecheck

# Run all checks
make check-all
```

### Development Commands

```bash
# Bootstrap configuration
make bootstrap

# Run engine
make run

# Run single turn
make run-once

# Start API server
python -m lemming.cli serve --reload
```

## Pull Request Process

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following our coding standards

3. **Add tests** for new functionality

4. **Run all checks**:
   ```bash
   make check-all
   ```

5. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Add feature: description of your changes"
   ```

6. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create a Pull Request** on GitHub

## Coding Standards

### Python Style
- Follow PEP 8
- Use Black for formatting (120 char line length)
- Use Ruff for linting
- Add type hints where possible
- Write docstrings for public functions

### Testing
- Write tests for all new features
- Maintain or improve code coverage
- Use pytest fixtures for reusable test data
- Mock external API calls

### Documentation
- Update README.md for user-facing changes
- Add docstrings to new functions/classes
- Update ROADMAP.md for planned features
- Document breaking changes in commit messages

## Commit Message Guidelines

Format: `<type>: <description>`

Types:
- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, etc.)
- **refactor**: Code refactoring
- **test**: Adding or updating tests
- **chore**: Maintenance tasks

Examples:
```
feat: Add WebSocket support for real-time updates
fix: Handle missing agents directory in cleanup
docs: Update API documentation
test: Add tests for memory system
```

## Project Structure

```
LeMMing/
├── lemming/          # Main package
│   ├── cli.py        # CLI commands
│   ├── engine.py     # Turn-based engine
│   ├── messaging.py  # Message system
│   ├── agents.py     # Agent management
│   ├── models.py     # Model registry
│   ├── providers.py  # LLM providers
│   ├── org.py        # Organization management
│   ├── memory.py     # Memory system
│   ├── api.py        # FastAPI backend
│   └── file_dispatcher.py  # File utilities
├── tests/            # Test suite
├── ui/               # Dashboard UIs
└── agents/           # Runtime agent data
```

## Adding a New LLM Provider

1. Create provider class in `lemming/providers.py`:
   ```python
   class MyProvider(LLMProvider):
       def call(self, model_name, messages, temperature, **kwargs):
           # Implementation
           pass
   ```

2. Register the provider:
   ```python
   register_provider("myprovider", MyProvider)
   ```

3. Add to `models.json`:
   ```json
   {
     "my-model": {
       "provider": "myprovider",
       "model_name": "model-id"
     }
   }
   ```

4. Write tests in `tests/test_providers.py`

## Adding New CLI Commands

1. Add command function in `lemming/cli.py`
2. Register in `main()` function
3. Add to Makefile if appropriate
4. Document in README.md

## Questions or Issues?

- Open an issue on GitHub
- Check existing issues and discussions
- Be respectful and constructive

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.
