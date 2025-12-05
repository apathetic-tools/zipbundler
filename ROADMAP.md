<!-- Roadmap.md -->
# 🧭 Roadmap

**Important Clarification**: Zipbundler provides Bundle your packages into a runnable, importable zip

## Key Points

Some of these we just want to consider, and may not want to implement.

## 🎯 Core Features

## 🧰 CLI Commands

### CLI Arguments (Defined but Not Yet Implemented)

The following CLI arguments are defined in `cli.py` but not yet used in command handlers:

#### Build Flags
- **`--add-include`** / `add_include`: Additional include paths (relative to cwd). Format: path or path:dest. Extends config includes.
- **`--add-exclude`** / `add_exclude`: Additional exclude patterns (relative to cwd). Extends config excludes.
- **`--input`** / `--in` / `input`: Override the name of the input file or directory. Start from an existing build (usually optional).

#### Build Options
- **`--gitignore`** / `--no-gitignore`** / `respect_gitignore`: Respect .gitignore when selecting files (default: True). Currently defined but not passed to build functions.
- **`--disable-build-timestamp`** / `disable_build_timestamp`: Disable build timestamps for deterministic builds (uses placeholder). Currently defined but not used.
- **`--no-main`**: Disable main insertion. Currently defined but not fully implemented - command handlers check `if args.entry_point:` but don't handle `entry_point=False` case.
- **`--no-compress`**: Do not compress the zip file (overrides config). ✅ Implemented (handles `compress=False`).

#### Universal Flags
- **`--compat`** / `--compatability`** / `compat`: Compatibility mode with stdlib zipapp behaviour. Currently defined but not implemented.

#### Terminal Flags
- **`--color`** / `--no-color`** / `use_color`: Force-enable or disable ANSI color output (overrides auto-detect). Currently defined but not used.

### CLI Commands (Other)
- audit for missing CLI arguments
- watch argument as float

## ⚙️ Configuration Features


## 🧪 Testing

## 🧑‍💻 Development

### Constants (Defined but Not Yet Implemented)

The following constants are defined in `constants.py` but not yet used in the codebase. They represent future features:

- **DEFAULT_COMMENTS_MODE**: Strip comments from files before bundling (default: "keep")
- **DEFAULT_DOCSTRING_MODE**: Strip docstrings from files before bundling (default: "keep")
- **DEFAULT_SOURCE_BASES**: Directories to search for packages (default: ["src", "lib", "packages"])
- **DEFAULT_MAIN_MODE**: Generate the `__main__` block (default: "auto")
- **DEFAULT_MAIN_NAME**: Name to use for main function (default: None, auto-detect)
- **DEFAULT_DISABLE_BUILD_TIMESTAMP**: Disable build timestamps for deterministic builds (default: False)
- **BUILD_TIMESTAMP_PLACEHOLDER**: Placeholder string for build timestamps (default: "<build-timestamp>")
- **DEFAULT_LICENSE_FALLBACK**: Fallback license text if not derived or specified

### Constants (Currently Used)

- **DEFAULT_RESPECT_GITIGNORE**: Respect .gitignore when selecting files (default: True)
- **DEFAULT_STRICT_CONFIG**: Fail on config validation warnings (default: True)
- **DEFAULT_OUT_DIR**: Default output directory (default: "dist")
- **DEFAULT_DRY_RUN**: Simulate build actions without copying/deleting files (default: False)
- **DEFAULT_USE_PYPROJECT_METADATA**: Pull metadata from pyproject.toml (default: True)
- **DEFAULT_WATCH_INTERVAL**: Default watch interval in seconds (default: 1.0)
- **DEFAULT_LOG_LEVEL**: Default log verbosity level (default: "info")

## 🔌 API Implementation


## 📚 Documentation

## 🚀 Deployment

## 💡 Future Ideas

- **Multi-format Support**: Support other archive formats
- **Plugin System**: Extensible architecture for custom handlers

## 🔧 Development Infrastructure


> See [REJECTED.md](REJECTED.md) for experiments and ideas that were explored but intentionally not pursued.

---

> ✨ *AI was used to help draft language, formatting, and code — plus we just love em dashes.*

<p align="center">
  <sub>😐 <a href="https://apathetic-tools.github.io/">Apathetic Tools</a> © <a href="./LICENSE">MIT-a-NOAI</a></sub>
</p>
