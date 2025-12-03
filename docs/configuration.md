---
layout: default
title: Configuration Reference
---

# Configuration Reference

Zipbundler uses a JSONC (JSON with Comments) configuration file to control how packages are bundled. You can use either `.zipbundler.jsonc` in your project root or add configuration to `pyproject.toml`.

**Important:** Zipbundler produces **zipapp-compatible** `.pyz` files that:
- ✅ Are importable via `zipimport` or `importlib`
- ✅ Preserve flat package structure without path transformations
- ✅ Work with Python's standard `zipapp` module

## Configuration File Location

Zipbundler looks for configuration in this order:

1. `.zipbundler.jsonc` in the current directory
2. `pyproject.toml` under `[tool.zipbundler]`
3. Command-line arguments override config file values

## Configuration Schema

### Top-Level Options

#### `packages` (required)
Array of package paths or glob patterns to include in the zip.

```jsonc
{
  "packages": [
    "src/my_package/**/*.py",
    "my_other_package",
    "installed_package/**/*.py"
  ]
}
```

- Glob patterns are relative to the project root
- Package names will be discovered automatically
- Installed packages can be included by path

#### `exclude` (optional)
Array of glob patterns for files/directories to exclude.

```jsonc
{
  "exclude": [
    "**/__pycache__/**",
    "**/*.pyc",
    "**/*.pyo",
    "**/tests/**",
    "**/.git/**",
    "**/.*"
  ]
}
```

Default exclusions (always applied):
- `__pycache__/`
- `*.pyc`, `*.pyo`
- `.git/`
- `.hg/`, `.svn/`

#### `output` (optional)
Output configuration for the zip file.

```jsonc
{
  "output": {
    "path": "dist/my_package.zip",
    "name": "my_package"  // Optional: override zip name
  }
}
```

- `path`: Full path to output zip file (default: `dist/{package_name}.zip`)
- `name`: Optional name override for the zip file

#### `entry_point` (optional)
Entry point for executable zip files (equivalent to `-m` / `--main` in zipapp-style CLI).

```jsonc
{
  "entry_point": "my_package.__main__:main"
}
```

Format: `module.path:function_name` or `module.path` (for `__main__.py`)

When specified, zipbundler will generate code to call this function when the zip is executed. This is compatible with Python's `zipapp` module entry point format.

#### `options` (optional)
Various bundling options.

```jsonc
{
  "options": {
    "shebang": "/usr/bin/env python3",  // Shebang line (default: "/usr/bin/env python3", set to false to disable)
    "main_guard": true,                  // Insert if __name__ == "__main__" guard (default: true)
    "compression": "deflate",            // Compression method: "deflate", "stored", "bzip2", "lzma" (default: "deflate")
    "compression_level": 6               // Compression level 0-9 (default: 6, only for deflate)
  }
}
```

- `shebang`: Shebang line string (e.g., `"/usr/bin/env python3"`) or `false` to disable. Equivalent to `-p` / `--python` in zipapp-style CLI.
- `main_guard`: If `true`, wraps entry point in `if __name__ == "__main__":` guard
- `compression`: Zip compression method (see Python's `zipfile` module). Use `"stored"` for no compression (equivalent to `--no-compress` in zipapp-style CLI).
- `compression_level`: Compression level for deflate method (0-9, higher = more compression)

#### `metadata` (optional)
Metadata included in the zip file.

```jsonc
{
  "metadata": {
    "display_name": "My Package",
    "description": "A great Python package",
    "version": "1.0.0",
    "author": "Your Name",
    "license": "MIT"
  }
}
```

This metadata is stored in the zip but doesn't affect functionality.

## pyproject.toml Integration

You can also configure zipbundler in `pyproject.toml`:

```toml
[tool.zipbundler]
packages = ["src/my_package/**/*.py"]
exclude = ["**/__pycache__/**", "**/tests/**"]

[tool.zipbundler.output]
path = "dist/my_package.zip"

[tool.zipbundler.options]
shebang = true
main_guard = true
compression = "deflate"

[tool.zipbundler.metadata]
display_name = "My Package"
version = "1.0.0"
```

## Example Configurations

### Minimal Configuration

```jsonc
{
  "packages": ["src/my_package"]
}
```

### Full Configuration

```jsonc
{
  "packages": [
    "src/my_package/**/*.py",
    "src/utils/**/*.py"
  ],
  "exclude": [
    "**/__pycache__/**",
    "**/*.pyc",
    "**/tests/**",
    "**/docs/**"
  ],
  "output": {
    "path": "dist/my_package.zip",
    "name": "my_package"
  },
  "entry_point": "my_package.__main__:main",
  "options": {
    "shebang": true,
    "main_guard": true,
    "compression": "deflate",
    "compression_level": 9
  },
  "metadata": {
    "display_name": "My Package",
    "description": "A bundled Python package",
    "version": "1.0.0"
  }
}
```

## Validation

Validate your configuration file:

```bash
zipbundler validate
```

This checks for:
- Required fields
- Valid glob patterns
- Valid entry point format
- Output path accessibility

