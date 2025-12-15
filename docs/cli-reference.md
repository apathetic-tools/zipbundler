---
layout: default
title: CLI Reference
---

# CLI Reference

Complete reference for all zipbundler command-line options.

## zipapp-Compatible Interface

Zipbundler supports a `python -m zipapp` compatible command-line interface that matches the standard library's zipapp module exactly:

```bash
zipbundler SOURCE [OPTIONS]
```

**Positional Arguments:**
- `SOURCE`: Source directory (or existing `.pyz` archive for `--info`)

**Options:**
- `-o, --output OUTPUT`: Output `.pyz` file path (required if SOURCE is an archive)
- `-p, --python PYTHON`: Python interpreter path for shebang line (default: no shebang)
- `-m, --main MAIN`: Main entry point as `module:function` or `module` (default: use existing `__main__.py`)
- `-c, --compress`: Compress files with deflate method (default: uncompressed)
- `--info`: Display the interpreter from an existing archive

**Examples:**
```bash
# Basic usage (no shebang, uses __main__.py if present)
zipbundler src/myapp -o app.pyz

# With shebang and entry point
zipbundler src/myapp -o app.pyz -p "/usr/bin/env python3" -m "myapp:main"

# With compression (shorthand)
zipbundler src/myapp -o app.pyz -m "myapp:main" -c

# With compression (long form)
zipbundler src/myapp -o app.pyz -m "myapp:main" --compress

# Display info from existing archive
zipbundler app.pyz --info

# Modify existing archive (requires -o)
zipbundler app.pyz -o app_new.pyz -p "/usr/bin/env python3"
```

**Compatibility Notes:**
- ✅ **100% zipapp compatible** — Matches `python -m zipapp` interface exactly
- ✅ **API compatible** — Python API matches `zipapp.create_archive()` and `zipapp.get_interpreter()`
- ✅ **Importable** — Files can be imported via `zipimport` or `importlib`
- ✅ **Flat structure** — Preserves original package paths without transformations
- ✅ **Archive reading** — Supports reading and modifying existing `.pyz` files

## Commands

### `zipbundler build`

Build a zip file from the current directory or configuration file.

```bash
zipbundler build [OPTIONS]
```

**Options:**
- `-c, --config PATH`: Path to configuration file (default: `.zipbundler.jsonc`)
- `-i, --include PATHS`: Override include paths from config. Format: `path` or `path:dest`
- `--add-include PATHS`: Additional include paths to append to config includes (CLI only). Format: `path` or `path:dest`
- `-e, --exclude PATTERNS`: Override exclude patterns from config
- `--add-exclude PATTERNS`: Additional exclude patterns to append to config excludes (CLI only)
- `-o, --output PATH`: Override output path from config
- `-m, --main ENTRY_POINT`: Override entry point from config
- `-p, --shebang PYTHON`: Override shebang from config
- `--no-shebang`: Disable shebang insertion
- `--gitignore`: Respect `.gitignore` patterns when selecting files (default)
- `--no-gitignore`: Ignore `.gitignore` and include all files
- `-c, --compress`: Compress files with deflate method
- `--no-compress`: Disable compression
- `--compression-level LEVEL`: Compression level 0-9 (only with --compress)
- `--no-main-guard`: Disable main guard insertion
- `--disable-build-timestamp`: Disable build timestamps for deterministic builds
  (uses placeholder in PKG-INFO metadata)
- `--dry-run`: Preview what would be bundled without creating zip
- `-f, --force`: Force rebuild even if up-to-date
- `--strict`: Fail on configuration warnings
- `-v, --verbose`: Increase verbosity
- `-q, --quiet`: Reduce output

**Include Path Format:**
- `path`: Include directory/file, destination derived from source structure
- `path:dest`: Include directory/file at custom destination in zip

Destinations in the zip are relative paths. For example:
- `config.json:etc/config.json` → file at root of zip: `etc/config.json`
- `README.md:docs/README.md` → file at root of zip: `docs/README.md`
- `src/lib` → includes all files from `src/lib` directory

**Examples:**
```bash
# Build using default config
zipbundler build

# Build with custom config
zipbundler build --config custom.jsonc

# Append additional directories to config packages
zipbundler build --add-include extra/lib

# Append multiple items with custom destinations
zipbundler build \
  --add-include config.json:etc/config.json \
  --add-include README.md:docs/README.md

# Override includes (replace config)
zipbundler build --include "src/pkg1/**/*.py" "src/pkg2/**/*.py"

# Preview without building
zipbundler build --dry-run

# Build with compression
zipbundler build --compress --compression-level 9

# Force rebuild
zipbundler build --force

# Ignore .gitignore patterns (include all files)
zipbundler build --no-gitignore

# Respect .gitignore (default behavior)
zipbundler build --gitignore
```

### `zipbundler init`

Create a default configuration file.

```bash
zipbundler init [OPTIONS]
```

**Options:**
- `-f, --force`: Overwrite existing config file
- `-o, --output PATH`: Output file path (default: `.zipbundler.jsonc`)

**Examples:**
```bash
# Create default config
zipbundler init

# Create with custom name
zipbundler init --output my-config.jsonc

# Overwrite existing
zipbundler init --force
```

### `zipbundler list`

List packages and files that would be included in the bundle.

```bash
zipbundler list [OPTIONS]
```

**Options:**
- `-c, --config PATH`: Path to configuration file
- `--tree`: Show as directory tree
- `--count`: Show file count only

**Examples:**
```bash
# List all files
zipbundler list

# Show as tree
zipbundler list --tree

# Just count
zipbundler list --count
```

### `zipbundler validate`

Validate a configuration file.

```bash
zipbundler validate [OPTIONS]
```

**Options:**
- `-c, --config PATH`: Path to configuration file (default: `.zipbundler.jsonc`)
- `--strict`: Fail on warnings

**Examples:**
```bash
# Validate default config
zipbundler validate

# Validate custom config
zipbundler validate --config custom.jsonc

# Strict validation
zipbundler validate --strict
```

### `zipbundler watch`

Watch for file changes and rebuild automatically.

```bash
zipbundler watch [OPTIONS]
```

**Options:**
- `-c, --config PATH`: Path to configuration file
- `--interval SECONDS`: Watch interval in seconds (default: 1.0)
- `--debounce SECONDS`: Debounce time before rebuild (default: 0.5)

**Examples:**
```bash
# Watch with default settings
zipbundler watch

# Watch with custom interval
zipbundler watch --interval 2.0
```

## Global Options

These options apply to all commands:

- `-h, --help`: Show help message
- `--version`: Show version information
- `--log-level LEVEL`: Set log level (DEBUG, INFO, WARNING, ERROR)

## Exit Codes

- `0`: Success
- `1`: General error
- `2`: Configuration error
- `3`: Build error

## Examples

### Basic Workflow

```bash
# Initialize config
zipbundler init

# Validate config
zipbundler validate

# Preview what will be bundled
zipbundler list

# Build the zip
zipbundler build

# Watch for changes
zipbundler watch
```

### Advanced Usage

```bash
# Build with multiple package sources
zipbundler build \
  --packages "src/pkg1,src/pkg2,installed_pkg" \
  --exclude "**/tests/**,**/docs/**" \
  --output dist/combined.zip

# Build executable zip
zipbundler build \
  --entry-point "myapp.__main__:main" \
  --output dist/myapp.zip

# Dry run to check configuration
zipbundler build --dry-run --verbose

# Build with deterministic timestamps for reproducible builds
zipbundler build --disable-build-timestamp

# Build with deterministic timestamps via environment variable
DISABLE_BUILD_TIMESTAMP=true zipbundler build
```

