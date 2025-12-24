# uv Package Manager Setup

This project uses [uv](https://github.com/astral-sh/uv) for fast Python package management, following Pulumi best practices.

## Why uv?

- **10-100x faster** than pip
- Drop-in replacement for pip, pip-tools, poetry, and more
- Built in Rust for maximum performance
- Works seamlessly with Pulumi

## Installation

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or via Homebrew
brew install uv

# Or via pip (if you have Python)
pip install uv
```

## Usage

### Install Dependencies

```bash
# Install all dependencies (including dev)
uv pip install -e ".[dev]"

# Install only runtime dependencies
uv pip install -e .

# Install in virtual environment (recommended)
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"
```

### Add Dependencies

```bash
# Add a new runtime dependency
uv pip install <package-name>

# Add a dev dependency
uv pip install --dev <package-name>

# Add and update pyproject.toml
uv add <package-name>
uv add --dev <package-name>
```

### Update Dependencies

```bash
# Update all dependencies
uv pip install --upgrade -e ".[dev]"

# Update specific package
uv pip install --upgrade <package-name>
```

### Sync Dependencies

```bash
# Sync from pyproject.toml
uv pip sync pyproject.toml
```

## Pulumi Integration

The project is configured to use `uv` in `Pulumi.yaml`:

```yaml
runtime:
  name: python
  options:
    toolchain: uv
    virtualenv: .venv
```

Pulumi will automatically:
- Use `uv` to manage dependencies
- Create virtual environment in `.venv/`
- Install packages from `pyproject.toml`

## Project Structure

```
pulumi-provisioning/
├── app/
│   └── pyproject.toml      # FastAPI app dependencies
├── infrastructure/
│   └── pyproject.toml      # Pulumi infrastructure dependencies
├── Pulumi.yaml            # Pulumi config (uses uv, root: infrastructure)
├── .python-version        # Python version (3.11)
└── .venv/                 # Virtual environment (gitignored)
```

## Dependencies

### FastAPI Application (`app/pyproject.toml`)
**Runtime Dependencies:**
- FastAPI and related packages
- AWS SDK (boto3)
- Database drivers (psycopg2-binary)
- SQLAlchemy

**Development Dependencies:**
- Testing tools (pytest, httpx)
- Code quality tools (black, ruff)

### Pulumi Infrastructure (`infrastructure/pyproject.toml`)
**Runtime Dependencies:**
- Pulumi and Pulumi AWS

**Development Dependencies:**
- Testing tools (pytest)
- Code quality tools (black, flake8, mypy, ruff)

## CI/CD Integration

GitHub Actions workflows use `uv` for faster builds:

```yaml
- name: Install uv
  uses: astral-sh/setup-uv@v3
  with:
    version: "latest"

- name: Install dependencies
  run: uv pip install -e ".[dev]"
```

## Project Structure

The project uses separate `pyproject.toml` files:
- ✅ `app/pyproject.toml` - FastAPI application dependencies
- ✅ `infrastructure/pyproject.toml` - Pulumi infrastructure dependencies
- ✅ Modern Python standard (PEP 621)
- ✅ Better dependency management
- ✅ Faster installation with uv
- ✅ Clear separation of concerns

## Best Practices

1. **Always use virtual environment**
   ```bash
   uv venv
   source .venv/bin/activate
   ```

2. **Install in editable mode for development**
   ```bash
   uv pip install -e ".[dev]"
   ```

3. **Keep pyproject.toml updated**
   - Use `uv add` to add dependencies
   - Manually edit for version constraints

4. **Use uv in CI/CD**
   - Faster builds
   - More reliable dependency resolution

## Troubleshooting

### Virtual environment not found
```bash
uv venv
source .venv/bin/activate
```

### Pulumi can't find dependencies
```bash
# Make sure Pulumi.yaml has toolchain: uv
# Then run:
pulumi preview  # Pulumi will install dependencies automatically
```

### Dependency conflicts
```bash
# Clear cache and reinstall
rm -rf .venv
uv venv
uv pip install -e ".[dev]"
```

## Resources

- [uv Documentation](https://github.com/astral-sh/uv)
- [Pulumi Python with uv](https://www.pulumi.com/blog/python-uv-toolchain/)
- [PEP 621 - Project metadata](https://peps.python.org/pep-0621/)

