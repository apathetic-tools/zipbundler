---
layout: default
title: Getting Started
---

# Getting Started with Zipbundler

Zipbundler makes it easy to bundle your Python packages into runnable, importable zip files. This guide will help you get started in minutes.

## Installation

Install zipbundler using your preferred package manager:

```bash
# Using poetry
poetry add zipbundler

# Using pip
pip install zipbundler
```

## Quick Start

### Option 1: zipapp-Style CLI (Quick)

Use the `python -m zipapp` compatible interface (100% feature parity):

```bash
# Build a zipapp-compatible .pyz file
zipbundler src/myapp -o app.pyz -p "/usr/bin/env python3" -m "myapp:main"

# With compression
zipbundler src/myapp -o app.pyz -m "myapp:main" -c

# Display info from existing archive
zipbundler app.pyz --info
```

This creates a **zipapp-compatible** `.pyz` file that is both runnable and importable. All options match `python -m zipapp` exactly.

### Option 2: Configuration File

### 1. Initialize Configuration

Create a configuration file for your project:

```bash
zipbundler init
```

This creates a `.zipbundler.jsonc` file with sensible defaults.

### 2. Build Your First Zip

```bash
zipbundler build
```

This will create a zip file containing your package in the `dist/` directory.

### 3. Use Your Zip File

**As an executable:**
```bash
python dist/my_package.pyz
# or make it executable
chmod +x dist/my_package.pyz
./dist/my_package.pyz
```

**As an importable package:**
```python
# Using zipimport
import zipimport
loader = zipimport.zipimporter('dist/my_package.pyz')
module = loader.load_module('my_package')

# Or using importlib (Python 3.4+)
import importlib.util
spec = importlib.util.spec_from_file_location("my_package", "dist/my_package.pyz")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
```

**Key Features:**
- ✅ **zipapp Compatible** — Works with Python's standard `zipapp` module
- ✅ **Importable** — Can be imported using `zipimport` or `importlib`
- ✅ **Flat Structure** — Preserves original package paths without transformations

## Basic Configuration

The configuration file (`.zipbundler.jsonc`) controls what gets bundled:

```jsonc
{
  // Packages to include (glob patterns)
  "packages": [
    "src/my_package/**/*.py"
  ],
  
  // Files to exclude
  "exclude": [
    "**/__pycache__/**",
    "**/*.pyc",
    "**/tests/**"
  ],
  
  // Output location
  "output": {
    "path": "dist/my_package.zip"
  }
}
```

## Common Workflows

### Bundle a Simple Package

```jsonc
{
  "packages": ["src/my_package"],
  "output": { "path": "dist/my_package.zip" }
}
```

### Create an Executable Zip

```jsonc
{
  "packages": ["src/my_cli"],
  "entry_point": "my_cli.__main__:main",
  "options": {
    "shebang": true,
    "main_guard": true
  },
  "output": { "path": "dist/my_cli.zip" }
}
```

### Bundle with Dependencies

```jsonc
{
  "packages": [
    "src/my_package",
    "installed_package/**/*.py"  // Include installed packages
  ],
  "exclude": ["**/tests/**"],
  "output": { "path": "dist/my_package.zip" }
}
```

## Next Steps

- Read the [Configuration Reference](/zipbundler/configuration) for all options
- Check out [Examples](/zipbundler/examples) for real-world use cases
- See the [CLI Reference](/zipbundler/cli-reference) for all commands

