# django-completion

**django-completion** maintains a JSON cache of your Django project's management commands, their flags, app labels, and migration names — and serves it to two consumers. Coding agents read it in one go (one file read or one `autocomplete context` call) instead of running `--help` once per command, each one booting Django. Your shell turns the same cache into project-aware tab completion for `manage.py` in bash and zsh — and Tab never imports Django or touches the database.

```bash
$ python manage.py imp<TAB>
import_articles

$ python manage.py import_articles --<TAB>
--dry-run  --limit  --since  --source

$ python manage.py migrate accounts <TAB>
0001_initial  0002_add_profile  zero
```

On a project with dozens of custom management commands, nobody remembers every name and argument signature. The completion cache is built from your project at runtime, so custom commands complete the same way Django's built-ins do — names, flags, and help descriptions included.

> **Note:** this is the pip-installable, project-aware tool. The `django-completion` Homebrew formula is an unrelated static bash completion script.

## Getting started

1. [Installation](installation.md) — install the package and set up shell completion
2. [For AI agents](agents.md) — the cache as a machine-readable project summary, `autocomplete context`, schema contract
3. [Usage](usage.md) — completion behavior, subcommands, and auto-refresh
4. [How it works](how_it_works.md) — cache, shell hooks, helper process, and refresh lifecycle
5. [Troubleshooting](troubleshooting.md) — common problems and fixes
6. [API Reference](api.md) — supported commands, cache schema, and compatibility notes
7. [Comparison with Django's built-in completion](comparison.md) — feature-by-feature breakdown

## For AI agents

The same cache gives coding agents every command, flag, and migration name from one file read — no Django boot — or one `python manage.py autocomplete context` call for a compact markdown summary. Measured on this repo's test project: 33 Django boots (~4 s) for the `--help` sweep vs. one boot (~0.2 s) for `context` vs. under a millisecond to read the file. See [For AI agents](agents.md) for the schema contract and an `AGENTS.md`/`CLAUDE.md` snippet.

## Compatibility

| Area | Supported |
|---|---|
| Python | 3.10+ |
| Django | 4.2+ |
| Shells | bash, zsh |
| OS | Linux and macOS expected |
| Windows | not officially supported; WSL with bash/zsh may work |
| Invocations | `manage.py`, `python manage.py`, `python3 manage.py`, `python ./manage.py`, `uv run python manage.py` |
| Completion depth | commands (including custom), option flags, app labels, migrate app labels, migration names |

## How it works

django-completion writes a JSON cache (`.django-completion-cache.json`) to your project root when you run `autocomplete install`, then refreshes it in a background thread after each `manage.py` command. When you press Tab, a shell script reads that file — no Python import, no Django startup, no database query. The cache holds management command names (including your project's custom commands), app labels with their pip-or-local origin, option flags per command introspected from each command's argparse parser, and migration file names discovered on disk. Completion stays current without making Tab slow.

## Why not Django's built-in?

Django ships a bash script that completes command names and option flags. It works without any extra package but reads argparse metadata at completion time and has no knowledge of your project's runtime state — so `python manage.py migrate <TAB>` shows nothing, and `python manage.py migrate accounts <TAB>` shows nothing. django-completion fills that gap.

See [Comparison with Django's built-in completion](comparison.md) for the full feature breakdown.

## Why it exists

Django can suggest close command names after an error. django-completion prevents many of those errors by completing project-specific commands, app labels, options, and migration targets before you press Enter.

---
*By [Soldatov Serhii](https://github.com/soldatov-ss) · Last updated: July 2026*
