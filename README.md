# Zipbundler 🗜️

[![CI](https://github.com/apathetic-tools/zipbundler/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/apathetic-tools/zipbundler/actions/workflows/ci.yml)
[![License: MIT-a-NOAI](https://img.shields.io/badge/License-MIT--a-NOAI-blueviolet.svg)](LICENSE)
[![Discord](https://img.shields.io/badge/Discord-%235865F2.svg?logo=discord&logoColor=white)](https://discord.gg/PW6GahZ7)

**Bundle your packages into a runnable, importable zip.**  
*Because installation is optional.*

📘 **[Roadmap](./ROADMAP.md)** · 📝 **[Release Notes](https://github.com/apathetic-tools/zipbundler/releases)**

> [!NOTE]
> Heads up: the AI cooked dinner. It's edible, but watch your step. Detailed bug reports welcome.

## 🚀 Quick Start

Zipbundler bundles your Python packages into runnable, importable zip files. Perfect for distributing single-file applications or creating portable package archives.

### Installation

```bash
# Using poetry
poetry add zipbundler

# Using pip
pip install zipbundler
```

### Basic Usage

```bash
# zipapp-style CLI (100% compatible with python -m zipapp)
zipbundler src/myapp -o app.pyz -p "/usr/bin/env python3" -m "myapp:main"

# With compression
zipbundler src/myapp -o app.pyz -m "myapp:main" -c

# Display info from existing archive
zipbundler app.pyz --info

# Or use configuration file
zipbundler init
zipbundler build

# Watch for changes and rebuild automatically
zipbundler watch
```

### Configuration

Create a `.zipbundler.jsonc` file in your project root:

```jsonc
{
  "packages": ["src/my_package/**/*.py"],
  "exclude": ["**/__pycache__/**", "**/tests/**"],
  "output": {
    "path": "dist/my_package.zip"
  },
  "entry_point": "my_package.__main__:main",
  "options": {
    "shebang": true,
    "main_guard": true
  }
}
```

---

## 🎯 What is Zipbundler?

Zipbundler creates **zipapp-compatible** `.pyz` files that are both **runnable** (executable) and **importable** (usable as a package). Unlike tools like [shiv](https://github.com/linkedin/shiv) or [pex](https://github.com/pantsbuild/pex), zipbundler produces standard zipapp files that work with Python's built-in `zipimport` module.

**Key Features:**
- ✅ **zipapp Compatible** — Produces standard `.pyz` files compatible with Python's `zipapp` module
- ✅ **Importable** — Files can be imported directly using `zipimport` or `importlib`
- ✅ **Flat Structure** — Preserves original package structure without path transformations
- ✅ **Standard Format** — Works with `python -m zipapp` and all zipapp-compatible tools

**Comparison with Other Tools:**

| Feature | zipbundler | [shiv](https://github.com/linkedin/shiv) | [pex](https://github.com/pantsbuild/pex) |
|---------|------------|------------------------------------------|------------------------------------------|
| zipapp compatible | ✅ Yes | ❌ No | ❌ No |
| Importable | ✅ Yes | ❌ No | ❌ No |
| Flat structure | ✅ Yes | ⚠️ Transforms paths | ⚠️ Transforms paths |
| Dependency resolution | ⚠️ Manual | ✅ Automatic | ✅ Automatic |
| Virtualenv support | ❌ No | ✅ Yes | ✅ Yes |

*Note: shiv and pex excel at dependency management and virtualenv creation, but produce non-standard zip files that aren't importable or zipapp-compatible.*

### Use Cases

- **CLI Tools**: Bundle command-line applications into single executable `.pyz` files
- **Importable Packages**: Create packages that can be imported without installation
- **Standard zipapp Format**: Generate files compatible with Python's standard library
- **Quick Deployment**: Ship code without installation steps or path transformations

## ✨ Features

- 📦 **zipapp Compatible** — Produces standard `.pyz` files compatible with Python's `zipapp` module
- 🔄 **Importable** — Files can be imported using `zipimport` or `importlib`
- 📁 **Flat Structure** — Preserves original package paths without transformations
- 🎯 **zipapp-style CLI** — Compatible with `python -m zipapp` command-line interface
- 🚫 **Exclude Patterns** — Fine-grained control over what gets included
- 🎬 **Entry Points** — Support for executable zip files with entry points
- ⚙️ **Code Generation** — Optional shebang and main guard insertion
- 🔍 **Watch Mode** — Automatically rebuild on file changes
- 📝 **Dry Run** — Preview what would be bundled without creating files

---

## ⚖️ License

- [MIT-a-NOAI License](LICENSE)

You're free to use, copy, and modify the script under the standard MIT terms.  
The additional rider simply requests that this project not be used to train or fine-tune AI/ML systems until the author deems fair compensation frameworks exist.  
Normal use, packaging, and redistribution for human developers are unaffected.

## 🪶 Summary

**Use it. Hack it. Ship it.**  
It's MIT-licensed, minimal, and meant to stay out of your way — just with one polite request: don't feed it to the AIs (yet).

---

> ✨ *AI was used to help draft language, formatting, and code — plus we just love em dashes.*

<p align="center">
  <sub>😐 <a href="https://apathetic-tools.github.io/">Apathetic Tools</a> © <a href="./LICENSE">MIT-a-NOAI</a></sub>
</p>
