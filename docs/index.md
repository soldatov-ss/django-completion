# django-completion

**django-completion** adds project-aware tab completion to Django's `manage.py`. It completes command names, app labels, option flags, and migration targets in bash and zsh — reading a local JSON cache so Tab never imports Django or touches the database.

```bash
$ python manage.py migrate <TAB>
accounts  billing  blog

$ python manage.py migrate accounts <TAB>
0001_initial  0002_add_profile  zero

$ python manage.py runserver --<TAB>
--addrport  --ipv6  --noreload  --nothreading
```

## Getting started

1. [Installation](installation.md) — install the package and set up shell completion
2. [Usage](usage.md) — completion behavior, subcommands, and auto-refresh
3. [How it works](how_it_works.md) — cache, shell hooks, helper process, and refresh lifecycle
4. [Troubleshooting](troubleshooting.md) — common problems and fixes
5. [API Reference](api.md) — supported commands, cache schema, and compatibility notes
6. [Comparison with Django's built-in completion](comparison.md) — feature-by-feature breakdown

## Compatibility

| Area | Supported |
|---|---|
| Python | 3.10+ |
| Django | 4.2+ |
| Shells | bash, zsh |
| OS | Linux and macOS expected |
| Windows | not officially supported; WSL with bash/zsh may work |
| Invocations | `manage.py`, `python manage.py`, `python3 manage.py`, `python ./manage.py`, `uv run python manage.py` |
| Completion depth | commands, app labels, options, migrate app labels, migration names |

## How it works

django-completion writes a JSON cache (`.django-completion-cache.json`) to your project root when you run `autocomplete install`, then refreshes it in a background thread after each `manage.py` command. When you press Tab, a shell script reads that file — no Python import, no Django startup, no database query. The cache holds management command names, app labels with their pip-or-local origin, option flags per command, and migration file names discovered on disk. Completion stays current without making Tab slow.

## Why not Django's built-in?

Django ships a bash script that completes command names and option flags. It works without any extra package but reads argparse metadata at completion time and has no knowledge of your project's runtime state — so `python manage.py migrate <TAB>` shows nothing, and `python manage.py migrate accounts <TAB>` shows nothing. django-completion fills that gap.

See [Comparison with Django's built-in completion](comparison.md) for the full feature breakdown.

## Why it exists

Django can suggest close command names after an error. django-completion prevents many of those errors by completing project-specific commands, app labels, options, and migration targets before you press Enter.

---
*By [Soldatov Serhii](https://github.com/soldatov-ss) · Last updated: May 2026*
