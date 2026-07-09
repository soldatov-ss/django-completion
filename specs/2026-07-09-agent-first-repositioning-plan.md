# Agent-First Repositioning Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reposition README, PyPI metadata, and docs index to lead with the coding-agent use case, keeping tab completion as the strong second feature (dual-headline, per `specs/2026-07-09-agent-first-repositioning-design.md`).

**Architecture:** Prose-only diff across four files (`README.md`, `pyproject.toml`, `docs/index.md` + `zensical.toml`, `CHANGELOG/0.3.0.md`). No code changes. Content moves and grows; nothing is deleted.

**Tech Stack:** Markdown, TOML, zensical (mkdocs-like) docs build.

## Global Constraints

- Branch: `feature/0.3.0-agent-context`. The working tree already holds unrelated staged-for-0.3.0 changes — `git add` only the files each task names, never `git add -A`.
- Measured numbers (already taken on `tests/testproject`, 2026-07-09, macOS): 32 commands; `help` + 32 × `--help` = 33 Django boots ≈ 3.9 s; `autocomplete context` = 0.16 s (one boot); reading `.django-completion-cache.json` = 0.12 ms. Copy below uses rounded forms (~4 s, ~0.2 s, under a millisecond) — do not re-measure or invent different numbers.
- Verification commands: `uv run --group docs zensical build --clean` for the docs site; `uv run --python=3.13 pytest .` must stay at 188 passed (sanity that no code was touched).
- Copy rule: the phrase "Tab completion" keeps a capital T mid-sentence only where existing files already do that (README currently mixes; follow each file's local style).

---

### Task 1: README.md — dual-headline intro, agent section promoted and expanded

**Files:**
- Modify: `README.md` (lines 8–12 intro, lines 48–91 section reorder)

**Interfaces:**
- Consumes: nothing.
- Produces: README section names `## For AI agents` and `## Tab completion` (Task 4's changelog bullet references this restructuring; no other task links to README anchors — verified via grep, only self-references exist).

- [ ] **Step 1: Replace the intro (README.md lines 8–12)**

Old:

```markdown
Project-aware **tab completion** for Django's `manage.py`.

Press Tab to complete your project's own management commands and their flags — plus app labels and migration targets — in bash and zsh. On a project with dozens of custom commands, nobody remembers every name and argument signature; django-completion introspects them from your actual project.

![django-completion demo](https://raw.githubusercontent.com/soldatov-ss/django-completion/main/demo.gif)
```

New (the demo gif moves to the Tab completion section in Step 3):

```markdown
Django `manage.py` context for **coding agents** — and **tab completion** for you.

Your agent learns every management command, its flags, and all migration names from one file read (no Django boot at all) or one `autocomplete context` call — instead of running `--help` once per command, each one booting Django. The same cache gives you project-aware Tab completion in bash and zsh: your own commands, their flags, app labels, and migration targets.
```

- [ ] **Step 2: Move and expand the "For AI agents" section**

Delete the current `## For AI agents` section (currently after "What Completes", lines 78–91) and insert this expanded version directly after the `## Installation` section (after the `source ~/.zshrc    # zsh` block):

````markdown
## For AI agents

An agent working in a Django repo discovers commands by running `manage.py help`, then `<command> --help` once per command — each one importing Django and your settings — or by grepping `management/commands/`, which misses commands from third-party apps. The cache django-completion maintains already holds all of it.

```bash
python manage.py autocomplete context
```

prints a compact markdown summary — your project's own commands first with their flags and help text, migration names per local app, and a one-line list of everything else (`--json` prints the full cache):

```markdown
# manage.py — 32 commands (cache generated 2026-07-05 16:40:15 UTC)

## Project commands [local]
- import_articles — Import articles from an external feed into the blog.
    --dry-run  --limit  --since  --source

## Migrations on disk [local]
- accounts: 0001_initial, 0002_add_profile
- blog: 0001_initial, 0002_add_slug, 0003_add_published_at

## Built-in and third-party commands
check, dumpdata, makemigrations, migrate, runserver, shell, test, …
```

Measured on this repo's minimal test project (32 commands): the `--help` sweep is 33 Django boots (~4 s), `autocomplete context` is one boot (~0.2 s), and reading `.django-completion-cache.json` directly takes under a millisecond — and the file read still works when settings are broken or dependencies are missing. On a real project where each boot takes seconds, the sweep costs minutes.

Add this to your project's `AGENTS.md` or `CLAUDE.md`:

```markdown
## Django management commands
This project maintains `.django-completion-cache.json` (django-completion).
Read it — or run `python manage.py autocomplete context` — instead of running
`manage.py help` or grepping management/commands/. It lists every command,
its flags with descriptions, and all migration names, and refreshes
automatically after each manage.py run.
```

See [For AI agents](https://soldatov-ss.github.io/django-completion/agents/) for the output format, the cache schema, and its stability policy.
````

- [ ] **Step 3: Rename "What Completes" to "Tab completion" and re-anchor the human pitch**

Replace the current section header and add the displaced intro copy plus the demo gif at the top of it. Old:

```markdown
## What Completes

The completion cache is built from your project at runtime, so it covers your custom management commands the same way it covers Django's built-ins:
```

New:

```markdown
## Tab completion

Press Tab to complete your project's own management commands and their flags — plus app labels and migration targets — in bash and zsh. On a project with dozens of custom commands, nobody remembers every name and argument signature; django-completion introspects them from your actual project.

![django-completion demo](https://raw.githubusercontent.com/soldatov-ss/django-completion/main/demo.gif)

The completion cache is built from your project at runtime, so it covers your custom management commands the same way it covers Django's built-ins:
```

The rest of the section (invocation styles, completion depth list, built-in comparison paragraph) stays verbatim. Final section order must be: intro → Installation → For AI agents → Tab completion → Commands → Compatibility → Safety and Privacy → Limitations → Roadmap → Documentation → Development.

- [ ] **Step 4: Verify structure**

Run: `grep -n "^## " README.md`
Expected order: `Installation`, `For AI agents`, `Tab completion`, `Commands`, `Compatibility`, `Safety and Privacy`, `Limitations`, `Roadmap`, `Documentation`, `Development` — and `grep -c "demo.gif" README.md` prints `1`.

- [ ] **Step 5: Commit**

```bash
git add README.md
git commit -m "docs: README leads with the agent use case (dual-headline)"
```

---

### Task 2: pyproject.toml — PyPI description and keywords

**Files:**
- Modify: `pyproject.toml:8` (description), `pyproject.toml:39-42` (keywords)

**Interfaces:**
- Consumes: nothing. Produces: nothing other tasks use.

- [ ] **Step 1: Replace the description**

Old:

```toml
description = "Tab completion for Django's manage.py — commands, app labels, options, and migration targets in bash and zsh"
```

New:

```toml
description = "Django manage.py context for coding agents + project-aware tab completion — commands, flags, app labels, and migration targets from one cache"
```

- [ ] **Step 2: Extend keywords**

Old:

```toml
keywords = [
    "django", "manage.py", "tab-completion", "autocomplete", "completion",
    "bash", "zsh", "bash-completion", "zsh-completion", "shell", "cli",
    "developer-tools", "productivity", "migration",
]
```

New:

```toml
keywords = [
    "django", "manage.py", "tab-completion", "autocomplete", "completion",
    "bash", "zsh", "bash-completion", "zsh-completion", "shell", "cli",
    "developer-tools", "productivity", "migration",
    "ai", "agents", "coding-agents", "llm", "claude", "cursor", "copilot",
    "agents-md", "context",
]
```

- [ ] **Step 3: Verify TOML parses and package builds metadata**

Run: `uv run --python=3.13 python -c "import tomllib; d=tomllib.load(open('pyproject.toml','rb')); print(d['project']['description']); print(len(d['project']['keywords']), 'keywords')"`
Expected: the new description and `23 keywords`.

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml
git commit -m "docs: PyPI description and keywords cover the agent use case"
```

---

### Task 3: docs/index.md dual pitch + zensical.toml nav order

**Files:**
- Modify: `docs/index.md` (intro paragraph, getting-started list, new teaser section)
- Modify: `zensical.toml:7-16` (nav order)

**Interfaces:**
- Consumes: nothing. Produces: nothing other tasks use.

- [ ] **Step 1: Rewrite the docs/index.md intro paragraph**

Old (line 3):

```markdown
**django-completion** adds project-aware tab completion to Django's `manage.py`. It completes your project's own management commands and their flags — plus app labels, migration targets, and everything Django ships with — in bash and zsh, reading a local JSON cache so Tab never imports Django or touches the database.
```

New:

```markdown
**django-completion** maintains a JSON cache of your Django project's management commands, their flags, app labels, and migration names — and serves it to two consumers. Coding agents read it in one go (one file read or one `autocomplete context` call) instead of running `--help` once per command, each one booting Django. Your shell turns the same cache into project-aware tab completion for `manage.py` in bash and zsh — and Tab never imports Django or touches the database.
```

The shell example block and the "On a project with dozens of custom management commands…" paragraph below it stay verbatim.

- [ ] **Step 2: Move "For AI agents" to #2 in the getting-started list**

Old:

```markdown
1. [Installation](installation.md) — install the package and set up shell completion
2. [Usage](usage.md) — completion behavior, subcommands, and auto-refresh
3. [How it works](how_it_works.md) — cache, shell hooks, helper process, and refresh lifecycle
4. [For AI agents](agents.md) — the cache as a machine-readable project summary, `autocomplete context`, schema contract
5. [Troubleshooting](troubleshooting.md) — common problems and fixes
6. [API Reference](api.md) — supported commands, cache schema, and compatibility notes
7. [Comparison with Django's built-in completion](comparison.md) — feature-by-feature breakdown
```

New:

```markdown
1. [Installation](installation.md) — install the package and set up shell completion
2. [For AI agents](agents.md) — the cache as a machine-readable project summary, `autocomplete context`, schema contract
3. [Usage](usage.md) — completion behavior, subcommands, and auto-refresh
4. [How it works](how_it_works.md) — cache, shell hooks, helper process, and refresh lifecycle
5. [Troubleshooting](troubleshooting.md) — common problems and fixes
6. [API Reference](api.md) — supported commands, cache schema, and compatibility notes
7. [Comparison with Django's built-in completion](comparison.md) — feature-by-feature breakdown
```

- [ ] **Step 3: Add a "For AI agents" teaser section**

Insert directly after the "Getting started" list (before `## Compatibility`):

```markdown
## For AI agents

The same cache gives coding agents every command, flag, and migration name from one file read — no Django boot — or one `python manage.py autocomplete context` call for a compact markdown summary. Measured on this repo's test project: 33 Django boots (~4 s) for the `--help` sweep vs. one boot (~0.2 s) for `context` vs. under a millisecond to read the file. See [For AI agents](agents.md) for the schema contract and an `AGENTS.md`/`CLAUDE.md` snippet.
```

- [ ] **Step 4: Reorder zensical.toml nav**

Old:

```toml
nav = [
  { "Home" = "index.md" },
  { "Installation" = "installation.md" },
  { "Comparison" = "comparison.md" },
  { "Usage" = "usage.md" },
  { "How it works" = "how_it_works.md" },
  { "For AI agents" = "agents.md" },
  { "Troubleshooting" = "troubleshooting.md" },
  { "API Reference" = "api.md" },
]
```

New:

```toml
nav = [
  { "Home" = "index.md" },
  { "Installation" = "installation.md" },
  { "For AI agents" = "agents.md" },
  { "Comparison" = "comparison.md" },
  { "Usage" = "usage.md" },
  { "How it works" = "how_it_works.md" },
  { "Troubleshooting" = "troubleshooting.md" },
  { "API Reference" = "api.md" },
]
```

- [ ] **Step 5: Verify docs build**

Run: `uv run --group docs zensical build --clean`
Expected: build succeeds with no warnings (strict mode fails on warnings).

- [ ] **Step 6: Commit**

```bash
git add docs/index.md zensical.toml
git commit -m "docs: index and nav lead with the agent use case"
```

---

### Task 4: CHANGELOG bullet + final sweep

**Files:**
- Modify: `CHANGELOG/0.3.0.md` (Changed section)

**Interfaces:**
- Consumes: the restructuring done in Tasks 1–3. Produces: nothing.

- [ ] **Step 1: Add the Changed bullet**

In `CHANGELOG/0.3.0.md`, under `## Changed`, after the fish-shell line, add:

```markdown
- README, PyPI metadata, and docs repositioned to lead with the coding-agent use case; tab completion stays as the second headline feature.
```

- [ ] **Step 2: Final verification sweep**

Run: `uv run --group docs zensical build --clean && uv run --python=3.13 pytest .`
Expected: docs build clean; `188 passed` (prose-only change — any test delta means a file outside scope was touched).

- [ ] **Step 3: Commit**

```bash
git add CHANGELOG/0.3.0.md
git commit -m "docs: changelog notes the agent-first repositioning"
```
