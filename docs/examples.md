---
layout: default
title: Examples
---

# Examples

Real-world examples of using zipbundler for different use cases.

## Example 1: zipapp-Style CLI (Quick Start)

Use the `python -m zipapp` compatible interface for quick bundling:

**Project structure:**
```
myapp/
├── src/
│   └── myapp/
│       ├── __init__.py
│       └── __main__.py
```

**Build with zipapp-style CLI:**
```bash
# Basic usage
zipbundler src/myapp -o app.pyz -p "/usr/bin/env python3" -m "myapp:main"

# With compression
zipbundler src/myapp -o app.pyz -m "myapp:main" -c

# Display info from archive
zipbundler app.pyz --info
```

**Usage:**
```bash
# Run as executable
python app.pyz
# or
chmod +x app.pyz
./app.pyz
```

**Import as package:**
```python
# Using zipimport
import zipimport
loader = zipimport.zipimporter('app.pyz')
module = loader.load_module('myapp')

# Using importlib (Python 3.4+)
import importlib.util
spec = importlib.util.spec_from_file_location("myapp", "app.pyz")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
```

**Key Points:**
- ✅ Produces **zipapp-compatible** `.pyz` files
- ✅ **Importable** via `zipimport` or `importlib`
- ✅ **Flat structure** — preserves original package paths
- ✅ Compatible with Python's standard `zipapp` module

## Example 2: Simple Package Bundle

Bundle a basic Python package into a zip file.

**Project structure:**
```
my_package/
├── src/
│   └── my_package/
│       ├── __init__.py
│       ├── module1.py
│       └── module2.py
└── .zipbundler.jsonc
```

**.zipbundler.jsonc:**
```jsonc
{
  "packages": ["src/my_package/**/*.py"],
  "output": {
    "path": "dist/my_package.pyz"
  }
}
```

**Build:**
```bash
zipbundler build
```

**Usage:**
```python
# Importable via zipimport
import zipimport
loader = zipimport.zipimporter('dist/my_package.pyz')
module = loader.load_module('my_package')

# Or using importlib (Python 3.4+)
import importlib.util
spec = importlib.util.spec_from_file_location("my_package", "dist/my_package.pyz")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
```

**Note:** The `.pyz` file is **zipapp-compatible** and preserves the flat package structure.

## Example 3: Executable CLI Tool

Create an executable zip file for a command-line tool.

**Project structure:**
```
my_cli/
├── src/
│   └── my_cli/
│       ├── __init__.py
│       ├── __main__.py
│       └── cli.py
└── .zipbundler.jsonc
```

**.zipbundler.jsonc:**
```jsonc
{
  "packages": ["src/my_cli/**/*.py"],
  "entry_point": "my_cli.__main__:main",
  "options": {
    "shebang": true,
    "main_guard": true
  },
  "output": {
    "path": "dist/my_cli.pyz"
  }
}
```

**Build:**
```bash
zipbundler build
```

**Usage:**
```bash
# Make executable
chmod +x dist/my_cli.zip

# Run directly
./dist/my_cli.zip --help

# Or with Python
python dist/my_cli.zip --help
```

## Example 4: Multi-Package Bundle

Bundle multiple packages into a single zip file.

**.zipbundler.jsonc:**
```jsonc
{
  "packages": [
    "src/package1/**/*.py",
    "src/package2/**/*.py",
    "src/shared/**/*.py"
  ],
  "exclude": [
    "**/__pycache__/**",
    "**/tests/**"
  ],
  "output": {
    "path": "dist/combined.pyz"
  }
}
```

## Example 5: Bundle with Dependencies

Include installed packages in your bundle.

**.zipbundler.jsonc:**
```jsonc
{
  "packages": [
    "src/my_package/**/*.py",
    "site-packages/dependency_package/**/*.py"
  ],
  "exclude": [
    "**/__pycache__/**",
    "**/tests/**",
    "**/*.dist-info/**"
  ],
  "output": {
    "path": "dist/my_package_with_deps.pyz"
  }
}
```

## Example 6: Development Workflow

Use watch mode during development.

**.zipbundler.jsonc:**
```jsonc
{
  "packages": ["src/my_package"],
  "output": {
    "path": "dist/my_package.pyz"
  }
}
```

**Development:**
```bash
# Terminal 1: Watch for changes
zipbundler watch

# Terminal 2: Test the zip
python dist/my_package.zip
```

## Example 7: CI/CD Integration

Build zip files in CI/CD pipelines.

**.github/workflows/build.yml:**
```yaml
name: Build

on: [push]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install zipbundler
      - run: zipbundler build
      - uses: actions/upload-artifact@v3
        with:
          name: dist
          path: dist/*.zip
```

## Example 8: pyproject.toml Configuration

Configure zipbundler in `pyproject.toml`.

**pyproject.toml:**
```toml
[tool.zipbundler]
packages = ["src/my_package/**/*.py"]
exclude = ["**/__pycache__/**", "**/tests/**"]

[tool.zipbundler.output]
path = "dist/my_package.zip"

[tool.zipbundler.options]
shebang = true
main_guard = true

[tool.zipbundler.metadata]
display_name = "My Package"
version = "1.0.0"
```

## Example 9: Programmatic API

Use zipbundler from Python code.

```python
from zipbundler import build_zip

# Build programmatically
result = build_zip(
    packages=["src/my_package"],
    exclude=["**/tests/**"],
    output_path="dist/my_package.zip",
    entry_point="my_package.__main__:main",
    shebang=True
)

print(f"Built {result.output_path} with {result.file_count} files")
```

## Example 10: Custom Entry Point

Create a zip with a custom entry point function.

**src/my_app/__main__.py:**
```python
def main():
    print("Hello from zipbundler!")

if __name__ == "__main__":
    main()
```

**.zipbundler.jsonc:**
```jsonc
{
  "packages": ["src/my_app"],
  "entry_point": "my_app.__main__:main",
  "options": {
    "shebang": true,
    "main_guard": true
  },
  "output": {
    "path": "dist/my_app.pyz"
  }
}
```

## Example 11: Exclude Patterns

Fine-grained control over what gets included.

**.zipbundler.jsonc:**
```jsonc
{
  "packages": ["src/my_package"],
  "exclude": [
    "**/__pycache__/**",
    "**/*.pyc",
    "**/tests/**",
    "**/test_*.py",
    "**/docs/**",
    "**/.git/**",
    "**/.*",
    "**/README.md",
    "**/LICENSE"
  ],
  "output": {
    "path": "dist/my_package.pyz"
  }
}
```

## Example 12: Adding Includes at Build Time

Use `--add-include` to append additional files and directories at build time without modifying the config file.

**.zipbundler.jsonc:**
```jsonc
{
  "packages": ["src/my_app"],
  "output": {
    "path": "dist/my_app.pyz"
  }
}
```

**Build with additional files:**
```bash
# Append another package directory
zipbundler build --add-include extras/plugins

# Append multiple files with custom destinations
zipbundler build \
  --add-include config.yaml:etc/config.yaml \
  --add-include README.md:docs/README.md \
  --add-include data/default.db:data/default.db

# Mix directories and files
zipbundler build \
  --add-include src/utils \
  --add-include assets/icons:static/icons \
  --add-include VERSION:VERSION
```

**Key Points:**
- ✅ `--add-include` appends to config packages (doesn't replace them)
- ✅ Use `path:dest` format for custom destinations
- ✅ Supports directories (as packages) and individual files
- ✅ CLI-only feature — not available in config files
- ✅ Useful for adding data files, configs, or supplementary code at build time

**Example: Building with Data Files**

```bash
# Config defines the main package
zipbundler build \
  --add-include config.json:etc/config.json \
  --add-include templates/:templates/ \
  --add-include data/initial.db:data/initial.db
```

This bundles:
- Python code from `src/my_app/`
- Configuration file at `etc/config.json` in the zip
- Template files in `templates/` directory
- Database file at `data/initial.db` in the zip

