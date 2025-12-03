# {{project_title}} 🧭 


[![CI]({{project_repo}}/actions/workflows/ci.yml/badge.svg?branch=main)]({{project_repo}}/actions/workflows/ci.yml)
[![License: MIT-aNOAI](https://img.shields.io/badge/License-MIT--aNOAI-blueviolet.svg)](LICENSE)
[![Discord](https://img.shields.io/badge/Discord-%235865F2.svg?logo=discord&logoColor=white)](https://discord.gg/PW6GahZ7)

**{{project_description}}**  
*Because tasks shouldn't get lost in translation.*

📘 **[Roadmap](./ROADMAP.md)** · 📝 **[Release Notes]({{project_repo}}/releases)**

> [!NOTE]
> Heads up: the AI cooked dinner. It's edible, but watch your step. Detailed bug reports welcome.

## 🚀 Quick Start

{{project_title}} provides preset rules, workflows, and commands for AI-powered IDE integrations like Cursor, Claude Desktop, and similar tools. These presets can be selectively enabled, similar to how you configure linter rules.

### Installation

```bash
# Using poetry
poetry add {{project_name}}

# Using pip
pip install {{project_name}}
```

### Basic Usage

```bash
# Enable specific presets (coming soon)
{{project_script_name}} enable --rules code-quality --workflows testing

# List available presets
{{project_script_name}} list

# Apply presets to your project
{{project_script_name}} sync
```

---

## 🎯 What is {{project_title}}?

{{project_title}} offers a curated collection of AI guidance presets that you can selectively enable:

- **Preset Rules**: Pre-configured prompt rules that get added to each AI interaction
  - Code quality standards
  - Testing best practices
  - Documentation guidelines
  - Security considerations

- **Preset Workflows**: Common workflows you can point an AI assistant to
  - Setting up new features
  - Refactoring patterns
  - Debugging strategies
  - Code review checklists

- **Preset Commands**: Ready-to-use commands for common development tasks
  - Generate test files
  - Create documentation
  - Run code quality checks
  - Format and lint code

All of these leverage functionality that already exists in your IDE — {{project_title}} just provides a well-organized, selective set of presets you can opt into, similar to how ruff lets you choose which linting rules to enable.

## ✨ Features

- 🎯 **Selective presets** — Choose only the rules, workflows, and commands you need
- 🔌 **IDE integration** — Works with Cursor, Claude Desktop, and similar tools
- 📦 **Zero dependencies** — Lightweight and focused
- 🧩 **Modular** — Enable or disable presets independently
- 🔧 **Configurable** — Customize presets to match your project's needs

---

## ⚖️ License

- [MIT-aNOAI License](LICENSE)

You're free to use, copy, and modify the script under the standard MIT terms.  
The additional rider simply requests that this project not be used to train or fine-tune AI/ML systems until the author deems fair compensation frameworks exist.  
Normal use, packaging, and redistribution for human developers are unaffected.

## 🪶 Summary

**Use it. Hack it. Ship it.**  
It's MIT-licensed, minimal, and meant to stay out of your way — just with one polite request: don't feed it to the AIs (yet).

---

> ✨ *AI was used to help draft language, formatting, and code — plus we just love em dashes.*

<p align="center">
  <sub>😐 <a href="https://{{project_org}}.github.io/">{{project_author}}</a> © <a href="./LICENSE">MIT-aNOAI</a></sub>
</p>
