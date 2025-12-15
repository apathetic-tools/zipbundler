<!-- Roadmap.md -->
# 🧭 Roadmap

**Important Clarification**: Zipbundler provides Bundle your packages into a runnable, importable zip

## 🎯 Core Features
- None at this time.

## 🧰 CLI Commands

### CLI Arguments (Implemented)

#### Universal Flags
- **`--compat`** / `--compatability`** / `compat`: Compatibility mode with stdlib zipapp behaviour. Currently defined but not implemented.

## ⚙️ Configuration Features
- None at this time.

## 🧪 Testing
- None at this time.

## 🧑‍💻 Development

### Constants (Defined but Not Yet Implemented)

The following constants are defined in `constants.py` but not yet used in the codebase. They represent future features:

- **DEFAULT_COMMENTS_MODE**: Strip comments from files before bundling (default: "keep")
- **DEFAULT_DOCSTRING_MODE**: Strip docstrings from files before bundling (default: "keep")
- **DEFAULT_SOURCE_BASES**: Directories to search for packages (default: ["src", "lib", "packages"])
- **DEFAULT_MAIN_MODE**: Generate the `__main__` block (default: "auto")
- **DEFAULT_MAIN_NAME**: Name to use for main function (default: None, auto-detect)
- **DEFAULT_LICENSE_FALLBACK**: Fallback license text if not derived or specified

### Constants (Currently Used)

- **DEFAULT_RESPECT_GITIGNORE**: Respect .gitignore when selecting files (default: True)
- **DEFAULT_STRICT_CONFIG**: Fail on config validation warnings (default: True)
- **DEFAULT_OUT_DIR**: Default output directory (default: "dist")
- **DEFAULT_DRY_RUN**: Simulate build actions without copying/deleting files (default: False)
- **DEFAULT_USE_PYPROJECT_METADATA**: Pull metadata from pyproject.toml (default: True)
- **DEFAULT_WATCH_INTERVAL**: Default watch interval in seconds (default: 1.0)
- **DEFAULT_LOG_LEVEL**: Default log verbosity level (default: "info")
- **DEFAULT_DISABLE_BUILD_TIMESTAMP**: Disable build timestamps for deterministic builds (default: False). ✅ Implemented with `--disable-build-timestamp` CLI flag and `DISABLE_BUILD_TIMESTAMP` environment variable
- **BUILD_TIMESTAMP_PLACEHOLDER**: Placeholder string for build timestamps (default: "<build-timestamp>"). Used for deterministic builds

## 🔌 API Implementation
- None at this time.

## 📚 Documentation
- None at this time.

## 🚀 Deployment
- None at this time.

## 💡 Future Ideas

- **Multi-format Support**: Support other archive formats
- **Plugin System**: Extensible architecture for custom handlers

## 🔧 Development Infrastructure
- None at this time.

> See [REJECTED.md](REJECTED.md) for experiments and ideas that were explored but intentionally not pursued.

---

> ✨ *AI was used to help draft language, formatting, and code — plus we just love em dashes.*

<p align="center">
  <sub>😐 <a href="https://apathetic-tools.github.io/">Apathetic Tools</a> © <a href="./LICENSE">MIT-a-NOAI</a></sub>
</p>
