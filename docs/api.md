---
layout: default
title: API Reference
---

# API Reference

Programmatic API for using zipbundler in your Python code. Zipbundler provides both a zipapp-compatible API and extended functionality.

## zipapp-Compatible API

### `create_archive()` (zipapp-compatible)

Create a zipapp archive matching Python's `zipapp.create_archive()` API exactly:

```python
from zipbundler import create_archive

# Basic usage (matches zipapp.create_archive)
create_archive(
    source="src/myapp",
    target="app.pyz",
    interpreter="/usr/bin/env python3",
    main="myapp:main",
    compressed=True
)
```

**Parameters:**
- `source` (str | Path): Source directory or existing archive
- `target` (str | Path, optional): Output archive path (required if source is archive)
- `interpreter` (str, optional): Python interpreter path for shebang (default: None)
- `main` (str, optional): Main entry point as `module:function` or `module` (default: None, uses `__main__.py`)
- `filter` (callable, optional): Filter function for files (default: None)
- `compressed` (bool, optional): Enable compression (default: False)

**Returns:**
- `Path`: Path to created archive

**Raises:**
- `ValueError`: Invalid arguments
- `FileNotFoundError`: Source not found

This function is **100% compatible** with Python's `zipapp.create_archive()` and can be used as a drop-in replacement.

## Extended API

### `build_zip()`

Build a zip file from configuration or parameters.

```python
from zipbundler import build_zip

# Build from config file
result = build_zip(config_path=".zipbundler.jsonc")

# Build with parameters
result = build_zip(
    packages=["src/my_package"],
    output_path="dist/my_package.zip",
    exclude=["**/__pycache__/**"]
)
```

**Parameters:**
- `config_path` (str, optional): Path to configuration file
- `packages` (list[str], optional): List of package paths/patterns
- `exclude` (list[str], optional): List of exclude patterns
- `output_path` (str, optional): Output zip file path
- `entry_point` (str, optional): Entry point for executable zip (equivalent to `main` in zipapp)
- `interpreter` (str, optional): Python interpreter path for shebang (equivalent to `interpreter` in zipapp, default: None)
- `main_guard` (bool, optional): Enable main guard insertion (default: True)
- `compressed` (bool, optional): Enable compression (default: False, matches zipapp default)
- `compression` (str, optional): Compression method when compressed=True (default: "deflate")
- `dry_run` (bool, optional): Preview without building (default: False)

**Returns:**
- `BuildResult`: Object containing build information

**Raises:**
- `ConfigError`: Invalid configuration
- `BuildError`: Build failure

### `load_config()`

Load and validate a configuration file.

```python
from zipbundler import load_config

config = load_config(".zipbundler.jsonc")
```

**Parameters:**
- `config_path` (str): Path to configuration file

**Returns:**
- `Config`: Configuration object

**Raises:**
- `ConfigError`: Invalid configuration file

### `list_packages()`

List packages and files that would be included.

```python
from zipbundler import list_packages

files = list_packages(
    packages=["src/my_package"],
    exclude=["**/__pycache__/**"]
)
```

**Parameters:**
- `packages` (list[str]): List of package paths/patterns
- `exclude` (list[str], optional): List of exclude patterns
- `config_path` (str, optional): Path to configuration file

**Returns:**
- `list[Path]`: List of file paths that would be included

### `get_interpreter()` (zipapp-compatible)

Get the interpreter from an existing archive (matches `zipapp.get_interpreter()`):

```python
from zipbundler import get_interpreter

# Get interpreter from archive
interpreter = get_interpreter("app.pyz")
print(interpreter)  # "/usr/bin/env python3" or None
```

**Parameters:**
- `archive` (str | Path): Path to existing `.pyz` archive

**Returns:**
- `str | None`: Interpreter path from shebang, or None if no shebang

**Raises:**
- `FileNotFoundError`: Archive not found
- `ValueError`: Invalid archive format

### `validate_config()`

Validate a configuration file.

```python
from zipbundler import validate_config

try:
    validate_config(".zipbundler.jsonc")
    print("Config is valid")
except ConfigError as e:
    print(f"Config error: {e}")
```

**Parameters:**
- `config_path` (str): Path to configuration file
- `strict` (bool, optional): Fail on warnings (default: False)

**Raises:**
- `ConfigError`: Invalid configuration

## Classes

### `Config`

Configuration object representing a zipbundler config.

```python
from zipbundler import Config, load_config

config = load_config(".zipbundler.jsonc")

# Access configuration values
print(config.packages)
print(config.output.path)
print(config.options.shebang)
```

**Attributes:**
- `packages` (list[str]): Package paths/patterns
- `exclude` (list[str]): Exclude patterns
- `output` (OutputConfig): Output configuration
- `entry_point` (str | None): Entry point
- `options` (OptionsConfig): Options configuration
- `metadata` (MetadataConfig | None): Metadata

### `BuildResult`

Result object from a build operation.

```python
result = build_zip(...)

print(f"Built: {result.output_path}")
print(f"Files: {result.file_count}")
print(f"Size: {result.size_bytes}")
```

**Attributes:**
- `output_path` (Path): Path to created zip file
- `file_count` (int): Number of files included
- `size_bytes` (int): Size of zip file in bytes
- `duration` (float): Build duration in seconds

## Exceptions

### `ZipbundlerError`

Base exception for all zipbundler errors.

### `ConfigError`

Raised when configuration is invalid.

```python
from zipbundler import ConfigError

try:
    load_config("invalid.jsonc")
except ConfigError as e:
    print(f"Config error: {e}")
```

### `BuildError`

Raised when build fails.

```python
from zipbundler import BuildError

try:
    build_zip(...)
except BuildError as e:
    print(f"Build failed: {e}")
```

## Examples

### zipapp-Compatible Usage

```python
from zipbundler import create_archive, get_interpreter

# Create archive (matches zipapp.create_archive exactly)
create_archive(
    source="src/myapp",
    target="app.pyz",
    interpreter="/usr/bin/env python3",
    main="myapp:main",
    compressed=True
)

# Get interpreter from archive (matches zipapp.get_interpreter)
interpreter = get_interpreter("app.pyz")
print(f"Interpreter: {interpreter}")
```

### Extended API Usage

```python
from zipbundler import build_zip

# Simple build
result = build_zip(
    packages=["src/my_package"],
    output_path="dist/my_package.pyz"
)

print(f"Created {result.output_path} with {result.file_count} files")
```

### Advanced Configuration

```python
from zipbundler import build_zip, Config

# Build with full options (using zipapp-compatible parameter names)
result = build_zip(
    packages=["src/my_package", "src/utils"],
    exclude=["**/tests/**", "**/__pycache__/**"],
    output_path="dist/my_package.pyz",
    entry_point="my_package.__main__:main",  # equivalent to 'main' in zipapp
    interpreter="/usr/bin/env python3",      # equivalent to 'interpreter' in zipapp
    main_guard=True,
    compressed=True,                         # equivalent to 'compressed' in zipapp
    compression="deflate"
)
```

### Programmatic Config

```python
from zipbundler import build_zip, Config

# Create config programmatically
config = Config(
    packages=["src/my_package"],
    exclude=["**/tests/**"],
    output=OutputConfig(path="dist/my_package.zip"),
    options=OptionsConfig(shebang=True, main_guard=True)
)

result = build_zip(config=config)
```

### Watch Mode

```python
from zipbundler import watch

# Watch for changes
watch(
    config_path=".zipbundler.jsonc",
    interval=1.0,
    callback=lambda result: print(f"Rebuilt: {result.output_path}")
)
```

