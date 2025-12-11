# Contributing to KAI ERP Connector

Thank you for your interest in contributing to the KAI ERP Connector! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Development Setup](#development-setup)
- [Code Style](#code-style)
- [Testing](#testing)
- [Commit Messages](#commit-messages)
- [Pull Request Process](#pull-request-process)
- [Security](#security)

## Development Setup

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker (optional, for containerized development)
- [uv](https://github.com/astral-sh/uv) (recommended Python package manager)

### Backend Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/kaspar-companies/bedrock-schedule-connector.git
   cd bedrock-schedule-connector
   ```

2. **Install Python dependencies with uv:**
   ```bash
   # Install uv if not already installed
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Create virtual environment and install dependencies
   uv sync --all-extras
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Install pre-commit hooks:**
   ```bash
   uv run pre-commit install
   ```

5. **Run the backend server:**
   ```bash
   uv run uvicorn kai_erp.api.main:app --reload --port 8100
   ```

### Frontend Setup

1. **Navigate to client directory:**
   ```bash
   cd client
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Run development server:**
   ```bash
   npm run dev
   ```

### Docker Development

For a fully containerized development environment:

```bash
# Build and start all services
docker compose up -d

# View logs
docker compose logs -f

# Stop services
docker compose down
```

## Code Style

We use automated tools to ensure consistent code style:

### Python

- **Ruff** for linting and formatting
- **mypy** for type checking
- **bandit** for security scanning

All style rules are defined in `pyproject.toml`.

```bash
# Run linter
uv run ruff check src/ tests/

# Run formatter
uv run ruff format src/ tests/

# Run type checker
uv run mypy src/

# Run all checks at once (via pre-commit)
uv run pre-commit run --all-files
```

### TypeScript/React

- **ESLint** for linting
- **TypeScript** for type checking

```bash
cd client
npm run lint
npx tsc --noEmit
```

### Key Style Guidelines

1. **Use type hints** for all function parameters and return values
2. **Write docstrings** for all public modules, classes, and functions
3. **Keep functions small** - aim for < 30 lines per function
4. **Use meaningful variable names** - avoid single-letter names except in loops
5. **Follow security best practices** - never interpolate user input into SQL

## Testing

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=kai_erp --cov-report=html

# Run specific test file
uv run pytest tests/test_connectors/test_bedrock_ops.py

# Run tests matching a pattern
uv run pytest -k "test_transform"
```

### Writing Tests

1. **Place tests in the appropriate directory:**
   - `tests/test_core/` - Core engine tests
   - `tests/test_connectors/` - Connector tests
   - `tests/test_api/` - API endpoint tests
   - `tests/test_mcp/` - MCP server tests

2. **Use fixtures from `conftest.py`** for common test data

3. **Test both success and error cases**

4. **Use `pytest.mark.asyncio`** for async tests

Example test:

```python
import pytest
from kai_erp.connectors.bedrock_ops import BedrockOpsScheduler

class TestBedrockOpsScheduler:
    @pytest.fixture
    def connector(self, mock_rest_engine):
        return BedrockOpsScheduler(mock_rest_engine)

    def test_get_rest_spec_no_filters(self, connector):
        spec = connector.get_rest_spec()
        assert len(spec.idos) == 6

    @pytest.mark.asyncio
    async def test_execute_returns_result(self, connector):
        result = await connector.execute()
        assert result.source == DataSource.REST
```

## Commit Messages

We follow [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or modifying tests
- `chore`: Maintenance tasks

### Examples

```
feat(connectors): add order availability connector

fix(security): escape OData filter values to prevent injection

docs: update API endpoint documentation

test(bedrock): add integration tests for schedule endpoint
```

## Pull Request Process

1. **Create a feature branch:**
   ```bash
   git checkout -b feat/your-feature-name
   ```

2. **Make your changes** and ensure all checks pass:
   ```bash
   uv run pre-commit run --all-files
   uv run pytest
   ```

3. **Push to your branch:**
   ```bash
   git push origin feat/your-feature-name
   ```

4. **Create a Pull Request** on GitHub with:
   - Clear description of changes
   - Link to any related issues
   - Screenshots for UI changes

5. **Address review feedback** and update as needed

6. **Merge** once approved (maintainers will merge)

### PR Checklist

- [ ] Code follows style guidelines
- [ ] Tests pass locally
- [ ] New code has test coverage
- [ ] Documentation updated if needed
- [ ] Commit messages follow convention
- [ ] No sensitive data in code

## Security

### Reporting Vulnerabilities

If you discover a security vulnerability, please:

1. **Do NOT** open a public issue
2. Email security concerns to it@kasparcompanies.com
3. Include detailed description and steps to reproduce

### Security Guidelines

When contributing, please follow these security practices:

1. **Never hardcode credentials** - use environment variables
2. **Use parameterized queries** - prevent SQL injection
3. **Validate all input** - use Pydantic models
4. **Escape output** - prevent XSS in frontend
5. **Follow least privilege** - minimize permissions

## Questions?

If you have questions about contributing, please:

1. Check existing documentation
2. Search closed issues for similar questions
3. Open a new issue with the `question` label

Thank you for contributing to KAI ERP Connector! 🚀
